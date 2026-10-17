"""Advisory file locking and atomic JSON persistence helpers.

The cloud-VM inventory and the manifest provider store are read and written
by several async request handlers and, in production, by more than one
orchestrator replica behind a shared volume.  Concurrent
read-modify-write cycles must not truncate each other, so both stores use
this module for:

* an exclusive lock around the whole read-modify-write cycle, and
* an atomic replace (write to a temp file in the same directory, fsync,
  then ``os.replace``) so a crash never leaves a half-written file.

POSIX uses ``fcntl.flock``; Windows uses ``msvcrt.locking``.  On platforms
without either, locking degrades to a no-op plus the atomic replace, which
still prevents torn writes (just not lost updates).
"""

import errno
import json
import logging
import os
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)

#: Suffix of the last-known-good copy written next to a JSON store.
BACKUP_SUFFIX = ".bak"

#: How many quarantined corrupt files to keep per store path.
QUARANTINE_KEEP = 3

try:  # pragma: no cover - platform dependent
    import fcntl

    _HAVE_FCNTL = True
except ImportError:  # pragma: no cover - Windows
    fcntl = None
    _HAVE_FCNTL = False

try:  # pragma: no cover - platform dependent
    import msvcrt

    _HAVE_MSVCRT = True
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None
    _HAVE_MSVCRT = False


# Process-local locks keyed by absolute lock-file path.  flock is per open
# file description, so two threads in the same process that open the lock
# file separately would both hold the lock; the mutex serializes them.
_LOCAL_LOCKS: Dict[str, threading.Lock] = {}
_LOCAL_LOCKS_GUARD = threading.Lock()


def _local_lock(lock_path: str) -> threading.Lock:
    with _LOCAL_LOCKS_GUARD:
        lock = _LOCAL_LOCKS.get(lock_path)
        if lock is None:
            lock = threading.Lock()
            _LOCAL_LOCKS[lock_path] = lock
        return lock


def lock_path_for(target: str) -> str:
    """Return the lock-file path used to guard ``target``."""
    return f"{target}.lock"


@contextmanager
def file_lock(
    target: str,
    timeout: float = 10.0,
    poll_interval: float = 0.05,
) -> Iterator[None]:
    """Acquire an exclusive advisory lock associated with ``target``.

    Creates ``<target>.lock`` if needed.  Raises ``TimeoutError`` when the
    lock cannot be acquired within ``timeout`` seconds, which surfaces a
    stuck peer instead of hanging a request forever.
    """
    lock_path = lock_path_for(target)
    Path(lock_path).parent.mkdir(parents=True, exist_ok=True)
    local = _local_lock(os.path.abspath(lock_path))
    acquired_local = local.acquire(timeout=timeout)
    if not acquired_local:
        raise TimeoutError(f"timed out waiting for in-process lock {lock_path}")

    handle = None
    try:
        handle = open(lock_path, "a+")
        _acquire_os_lock(handle, lock_path, timeout, poll_interval)
        yield
    finally:
        if handle is not None:
            try:
                _release_os_lock(handle)
            finally:
                handle.close()
        local.release()


def _acquire_os_lock(handle, lock_path: str, timeout: float, poll: float) -> None:
    if _HAVE_FCNTL:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except OSError as exc:
                if exc.errno not in (errno.EAGAIN, errno.EACCES):
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"timed out waiting for file lock {lock_path}"
                    ) from exc
                time.sleep(poll)
    elif _HAVE_MSVCRT:  # pragma: no cover - Windows
        deadline = time.monotonic() + timeout
        while True:
            try:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"timed out waiting for file lock {lock_path}"
                    ) from exc
                time.sleep(poll)


def _release_os_lock(handle) -> None:
    if _HAVE_FCNTL:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:  # pragma: no cover - best effort
            pass
    elif _HAVE_MSVCRT:  # pragma: no cover - Windows
        try:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass


def read_json(path: str, default: Any = None) -> Any:
    """Read JSON from ``path``; return ``default`` when absent or corrupt."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read JSON %s: %s", path, exc)
        return default


def backup_path_for(path: str) -> str:
    """Return the backup-file path paired with ``path``."""
    return f"{path}{BACKUP_SUFFIX}"


def quarantine_path_for(path: str) -> str:
    """Return a fresh quarantine path for the corrupt file ``path``."""
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
    return f"{path}.corrupt-{stamp}"


def _prune_quarantine(path: str) -> None:
    """Keep only the newest ``QUARANTINE_KEEP`` quarantines of ``path``."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    prefix = os.path.basename(path) + ".corrupt-"
    try:
        entries = [
            name
            for name in os.listdir(directory)
            if name.startswith(prefix) and name not in ("", BACKUP_SUFFIX)
        ]
    except OSError:  # pragma: no cover - best effort
        return
    for name in sorted(entries)[: max(len(entries) - QUARANTINE_KEEP, 0)]:
        try:
            os.unlink(os.path.join(directory, name))
        except OSError:  # pragma: no cover - best effort
            pass


def _quarantine(path: str) -> Optional[str]:
    """Move the corrupt ``path`` aside so the next write starts clean."""
    try:
        target = quarantine_path_for(path)
        os.replace(path, target)
        _prune_quarantine(path)
        logger.warning("Quarantined corrupt JSON %s -> %s", path, target)
        return target
    except OSError as exc:
        logger.warning("Could not quarantine corrupt JSON %s: %s", path, exc)
        return None


def _try_read(candidate: str) -> tuple:
    """Return ``(ok, data)`` after one read attempt of ``candidate``."""
    try:
        with open(candidate, "r", encoding="utf-8") as fh:
            return True, json.load(fh)
    except FileNotFoundError:
        return False, None
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read JSON %s: %s", candidate, exc)
        return False, None


def read_json_recovering(path: str, default: Any = None) -> Any:
    """Read JSON from ``path`` with backup recovery.

    Recovery order:

    1. the main file, when it parses;
    2. when the main file is missing or corrupt, the paired ``.bak``
       written by :func:`write_json_atomic` with ``backup=True``;
    3. a corrupt main file is quarantined to ``<path>.corrupt-<ts>`` so a
       later write starts from a clean name;
    4. otherwise ``default``.

    Never raises for on-disk problems: a corrupt store must not take the
    orchestrator's API down, and losing a write must be visible as drift
    rather than a crash.
    """
    ok, data = _try_read(path)
    if ok:
        return data

    missing = not os.path.exists(path)
    if missing and not os.path.exists(backup_path_for(path)):
        return default

    if not missing:
        # Distinguish "absent" (handled above) from "corrupt".
        try:
            with open(path, "r", encoding="utf-8"):
                pass
        except OSError:
            logger.warning("Could not access JSON %s", path)
            return default
        _quarantine(path)

    ok, data = _try_read(backup_path_for(path))
    if ok:
        logger.warning("Recovered JSON %s from backup %s", path, backup_path_for(path))
        return data
    return default


def _write_backup(path: str, mode: Optional[int] = None) -> None:
    """Copy the current ``path`` to ``<path>.bak`` via temp + replace."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-bak-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as out:
            with open(path, "rb") as src:
                while True:
                    chunk = src.read(1 << 16)
                    if not chunk:
                        break
                    out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        if mode is not None:
            os.chmod(tmp_path, mode)
        os.replace(tmp_path, backup_path_for(path))
    except OSError as exc:
        logger.warning("Could not write backup of %s: %s", path, exc)
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def write_json_atomic(
    path: str,
    data: Any,
    mode: Optional[int] = None,
    backup: bool = False,
) -> None:
    """Atomically replace ``path`` with ``data`` serialized as JSON.

    Writes to a sibling temp file, flushes and fsyncs it, then renames over
    the target so readers never observe a partial file.  With ``backup=True``
    the previous contents are first copied to ``<path>.bak``, which
    :func:`read_json_recovering` uses to restore a store that a hardware or
    operator accident corrupts between updates.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    Path(directory).mkdir(parents=True, exist_ok=True)
    if backup and os.path.exists(path):
        _write_backup(path, mode)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.flush()
            os.fsync(fh.fileno())
        if mode is not None:
            os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def write_text_atomic(path: str, text: str, mode: Optional[int] = None) -> None:
    """Atomically replace ``path`` with ``text`` (used for quarantine-safe
    sidecar files such as rendered manifests)."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    Path(directory).mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        if mode is not None:
            os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def list_quarantined(path: str) -> List[str]:
    """Return quarantine file paths for ``path``, newest first."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    prefix = os.path.basename(path) + ".corrupt-"
    try:
        names = [n for n in os.listdir(directory) if n.startswith(prefix)]
    except OSError:  # pragma: no cover - best effort
        return []
    return [os.path.join(directory, name) for name in sorted(names, reverse=True)]


def update_json_locked(
    path: str,
    mutator: Callable[[Any], Any],
    default: Any = None,
    timeout: float = 10.0,
    backup: bool = True,
) -> Any:
    """Run ``mutator`` under the file lock and persist its return value.

    ``mutator`` receives the current (possibly default) contents and must
    return the new contents.  Returning the sentinel ``SKIP_WRITE`` keeps
    the file unchanged.  The new value is written atomically, keeping the
    previous value as ``<path>.bak`` unless ``backup=False``.
    """
    with file_lock(path, timeout=timeout):
        current = read_json(path, default if default is not None else {})
        updated = mutator(current)
        if updated is SKIP_WRITE:
            return current
        write_json_atomic(path, updated, backup=backup)
        return updated


class _SkipWrite:
    """Sentinel returned by a mutator that does not want a write."""

    __slots__ = ()


SKIP_WRITE = _SkipWrite()
