"""SSH command runner for the cloud-VM compute provider.

The cloud-VM provider deliberately avoids cloud SDKs: it talks to remote
machines with the system ``ssh`` client in ``BatchMode`` (never prompts),
optionally reusing a ControlMaster socket so a burst of Docker commands
opens a single TCP connection.  Everything goes through :class:`SSHRunner`
so tests can inject a fake ``subprocess`` runner and so the security
posture (host-key verification, key path, timeouts) lives in one place.

Security defaults come from :mod:`config`:

* host-key verification is **on** (``StrictHostKeyChecking=yes`` and
  ``UserKnownHostsFile=<known_hosts>``) unless an operator explicitly
  disables it for throwaway lab hosts;
* ``BatchMode=yes`` and ``IdentitiesOnly=yes`` prevent interactive auth
  and stray agent keys;
* every invocation has a connect timeout and an overall command timeout.

Failures are mapped onto the provider error taxonomy in
``compute.base``: :class:`SSHAuthError` -> ``ProviderAuthError``,
:class:`SSHHostKeyError` -> ``ProviderPermissionError`` (the host is not
trusted), and transient connection failures are retried with exponential
backoff before surfacing as ``ProviderUnavailableError``.
"""

import logging
import shlex
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

logger = logging.getLogger(__name__)


class SSHError(Exception):
    """Base class for SSH runner failures."""


class SSHConnectionError(SSHError):
    """The remote host could not be reached (transient, retryable)."""


class SSHAuthError(SSHError):
    """Authentication was rejected (bad key/user)."""


class SSHHostKeyError(SSHError):
    """Host key is missing (strict mode) or has changed."""


class SSHCommandError(SSHError):
    """The remote command ran but exited non-zero."""

    def __init__(self, returncode: int, stderr: str, stdout: str = ""):
        super().__init__(f"remote command failed ({returncode}): {stderr.strip()}")
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout


# stderr fragments that indicate a retryable transport failure.
_TRANSIENT_MARKERS = (
    "connection refused",
    "connection timed out",
    "connection closed",
    "operation timed out",
    "no route to host",
    "network is unreachable",
    "connection reset",
    "broken pipe",
    "kex_exchange_identification",
    "port 22: connection",
    "temporary failure in name resolution",
    "could not resolve hostname",
    "banner exchange",
    "connection aborted",
)
_AUTH_MARKERS = (
    "permission denied",
    "authentication failed",
    "too many authentication failures",
    "no supported authentication methods",
)
_HOST_KEY_MARKERS = (
    "host key verification failed",
    "remote host identification has changed",
    "no ed25519 host key is known",
    "no rsa host key is known",
    "no ecdsa host key is known",
    "no matching host key",
    "offending key",
)


@dataclass
class SSHResult:
    """Outcome of a remote command."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


_Transport = Callable[[Sequence[str], float], subprocess.CompletedProcess]


def _default_transport(command: Sequence[str], timeout: float):
    return subprocess.run(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
        text=True,
    )


def classify_failure(returncode: int, stderr: str) -> SSHError:
    """Map an ssh exit status/stderr to the precise error type."""
    text = (stderr or "").lower()
    if any(marker in text for marker in _HOST_KEY_MARKERS):
        return SSHHostKeyError(stderr.strip() or "host key verification failed")
    if any(marker in text for marker in _AUTH_MARKERS):
        return SSHAuthError(stderr.strip() or "authentication failed")
    if returncode == 255 or any(marker in text for marker in _TRANSIENT_MARKERS):
        return SSHConnectionError(stderr.strip() or f"ssh exited {returncode}")
    return SSHCommandError(returncode, stderr)


class SSHRunner:
    """Run commands on remote hosts over the system ``ssh`` client."""

    def __init__(
        self,
        key_path: str = "",
        known_hosts: str = "",
        strict_host_key: bool = True,
        user: str = "root",
        port: int = 22,
        connect_timeout: int = 15,
        command_timeout: int = 120,
        retries: int = 3,
        backoff: float = 0.5,
        controlmaster: bool = True,
        control_path: str = "/tmp/infra-pilot-ssh-%r@%h:%p",
        control_persist: str = "60s",
        ssh_binary: str = "ssh",
        transport: Optional[_Transport] = None,
        sleep: Callable[[float], None] = time.sleep,
        extra_options: Optional[List[str]] = None,
    ):
        self.key_path = key_path
        self.known_hosts = known_hosts
        self.strict_host_key = strict_host_key
        self.user = user
        self.port = port
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        self.retries = max(1, retries)
        self.backoff = backoff
        self.controlmaster = controlmaster
        self.control_path = control_path
        self.control_persist = control_persist
        self.ssh_binary = ssh_binary
        self._transport: _Transport = transport or _default_transport
        self._sleep = sleep
        self.extra_options = list(extra_options or [])

    # ------------------------------------------------------------------
    # Command construction
    # ------------------------------------------------------------------
    def build_command(self, host: str, remote_command: str) -> List[str]:
        """Build the full ``ssh`` argv for ``remote_command`` on ``host``."""
        command = [
            self.ssh_binary,
            "-o",
            "BatchMode=yes",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            f"ConnectTimeout={self.connect_timeout}",
            "-o",
            "ServerAliveInterval=15",
            "-o",
            "ServerAliveCountMax=3",
        ]
        if self.strict_host_key:
            command += ["-o", "StrictHostKeyChecking=yes"]
            if self.known_hosts:
                command += ["-o", f"UserKnownHostsFile={self.known_hosts}"]
        else:
            command += [
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
            ]
        if self.key_path:
            command += ["-i", self.key_path]
        if self.controlmaster:
            command += [
                "-o",
                "ControlMaster=auto",
                "-o",
                f"ControlPath={self.control_path}",
                "-o",
                f"ControlPersist={self.control_persist}",
            ]
        command += self.extra_options
        command += ["-p", str(self.port), f"{self.user}@{host}", "--", remote_command]
        return command

    @staticmethod
    def quote_args(args: Sequence[str]) -> str:
        return " ".join(shlex.quote(str(a)) for a in args)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def run(
        self,
        host: str,
        command: str,
        timeout: Optional[int] = None,
        check: bool = False,
    ) -> SSHResult:
        """Run ``command`` on ``host``, retrying transient failures.

        When ``check`` is true a non-zero exit raises
        :class:`SSHCommandError` (a provider-level failure); otherwise the
        result is returned so callers can branch on ``returncode``.
        """
        argv = self.build_command(host, command)
        effective_timeout = timeout or self.command_timeout
        last_error: Optional[SSHError] = None
        attempts = self.retries
        for attempt in range(1, attempts + 1):
            try:
                completed = self._transport(argv, effective_timeout)
            except subprocess.TimeoutExpired as exc:
                last_error = SSHConnectionError(
                    f"ssh to {host} timed out after {effective_timeout}s"
                )
                logger.warning(
                    "ssh timeout to %s (attempt %d/%d)", host, attempt, attempts
                )
                if attempt < attempts:
                    self._sleep(self.backoff * (2 ** (attempt - 1)))
                    continue
                raise last_error from exc
            except OSError as exc:
                last_error = SSHConnectionError(f"could not execute ssh: {exc}")
                if attempt < attempts:
                    self._sleep(self.backoff * (2 ** (attempt - 1)))
                    continue
                raise last_error from exc

            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            result = SSHResult(completed.returncode, stdout, stderr)
            if result.returncode == 0:
                return result

            error = classify_failure(result.returncode, stderr)
            if isinstance(error, SSHConnectionError) and attempt < attempts:
                logger.warning(
                    "transient ssh failure to %s (attempt %d/%d): %s",
                    host,
                    attempt,
                    attempts,
                    stderr.strip(),
                )
                self._sleep(self.backoff * (2 ** (attempt - 1)))
                continue
            if check and not isinstance(error, SSHConnectionError):
                raise SSHCommandError(result.returncode, stderr, stdout)
            if check:
                raise error
            return result

        # Unreachable, but keep mypy/readers happy.
        raise last_error or SSHConnectionError(f"ssh to {host} failed")

    def check(self, host: str, command: str, timeout: Optional[int] = None) -> str:
        """Run ``command`` and return stdout, raising on any failure."""
        result = self.run(host, command, timeout=timeout)
        if not result.ok:
            error = classify_failure(result.returncode, result.stderr)
            raise error
        return result.stdout

    def ping(self, host: str, timeout: Optional[int] = None) -> bool:
        """Return True when the host accepts an SSH command."""
        try:
            result = self.run(host, "true", timeout=timeout or self.connect_timeout)
        except SSHError:
            return False
        return result.ok

    def wait_for_host(
        self,
        host: str,
        timeout: float = 60.0,
        interval: float = 2.0,
    ) -> bool:
        """Poll ``host`` until SSH answers or ``timeout`` elapses.

        Used after ``enable_vm``/migrations where an SSH daemon may still
        be restarting; returns False on deadline instead of raising.
        """
        deadline = time.monotonic() + timeout
        while True:
            if self.ping(host, timeout=min(self.connect_timeout, max(1, int(timeout)))):
                return True
            if time.monotonic() >= deadline:
                return False
            self._sleep(interval)

    def run_batch(
        self,
        host: str,
        commands: Sequence[str],
        timeout: Optional[int] = None,
        separator: str = " && ",
        check: bool = True,
    ) -> SSHResult:
        """Run several remote commands over one SSH connection.

        Commands are joined with ``separator`` (default ``&&`` so the batch
        stops at the first failure) and executed as a single remote shell
        string, which avoids re-authenticating per command.  An empty
        batch short-circuits to success.
        """
        usable = [c for c in commands if c and c.strip()]
        if not usable:
            return SSHResult(0, "", "")
        return self.run(host, separator.join(usable), timeout=timeout, check=check)

    def stream_pipe(
        self,
        producer: Sequence[str],
        consumer: Sequence[str],
        timeout: Optional[int] = None,
        context: str = "stream",
    ) -> SSHResult:
        """Pipe stdout of local argv ``producer`` into stdin of ``consumer``.

        Both sides are full local argv lists (normally two ``build_command``
        results), which lets the provider stream an image between two remote
        hosts — ``ssh src docker save | ssh dst docker load`` — without
        buffering the payload on this machine.

        The producer's stderr goes to a temp file rather than a pipe so a
        chatty producer cannot deadlock against an unread pipe; the
        consumer's streams are drained by ``communicate``.  Either side
        failing raises the classified SSH error (exit 255 maps to
        :class:`SSHConnectionError`, a host-key or auth failure maps to the
        precise type).
        """
        effective_timeout = timeout or self.command_timeout * 4
        producer_proc: Optional[subprocess.Popen] = None
        consumer_proc: Optional[subprocess.Popen] = None
        with tempfile.TemporaryFile() as producer_err:
            try:
                producer_proc = subprocess.Popen(
                    list(producer),
                    stdout=subprocess.PIPE,
                    stderr=producer_err,
                )
                consumer_proc = subprocess.Popen(
                    list(consumer),
                    stdin=producer_proc.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                # The consumer owns the write end now; our copy must close
                # or it never sees EOF.
                producer_proc.stdout.close()
                consumer_out, consumer_err = consumer_proc.communicate(
                    timeout=effective_timeout
                )
                producer_rc = producer_proc.wait(timeout=self.connect_timeout)
            except subprocess.TimeoutExpired as exc:
                self._kill_process(producer_proc)
                self._kill_process(consumer_proc)
                raise SSHConnectionError(
                    f"{context} timed out after {effective_timeout}s"
                ) from exc
            except OSError as exc:
                self._kill_process(producer_proc)
                self._kill_process(consumer_proc)
                raise SSHConnectionError(f"could not execute {context}: {exc}") from exc

            producer_err.seek(0)
            producer_stderr = producer_err.read().decode("utf-8", "replace")
            consumer_stderr = (consumer_err or b"").decode("utf-8", "replace")
            consumer_stdout = (consumer_out or b"").decode("utf-8", "replace")
            stderr = (producer_stderr + "\n" + consumer_stderr).strip()
            returncode = consumer_proc.returncode or 0
            if producer_rc != 0:
                returncode = producer_rc
            if returncode != 0:
                raise classify_failure(returncode, stderr)
            return SSHResult(returncode, consumer_stdout, stderr)

    @staticmethod
    def _kill_process(proc: Optional[subprocess.Popen]) -> None:
        if proc is None:
            return
        try:
            proc.kill()
        except OSError:  # pragma: no cover - best effort
            pass
        try:
            proc.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):  # pragma: no cover
            pass

    def close_control_master(self, host: str, timeout: Optional[int] = None) -> bool:
        """Ask the ControlMaster socket for ``host`` to close.

        Returns True when the socket was closed (or none existed with an
        error we can ignore).  Called when a VM is disabled or drained so a
        stale multiplexed connection cannot keep a half-migrated VM alive.
        """
        if not self.controlmaster:
            return False
        command = [
            self.ssh_binary,
            "-o",
            "BatchMode=yes",
            "-o",
            f"ControlPath={self.control_path}",
            "-O",
            "exit",
            "-p",
            str(self.port),
            f"{self.user}@{host}",
        ]
        try:
            completed = self._transport(command, timeout or self.connect_timeout)
        except (OSError, subprocess.TimeoutExpired):
            return False
        if completed.returncode != 0:
            logger.debug(
                "ControlMaster close for %s: %s",
                host,
                (completed.stderr or "").strip(),
            )
            return False
        return True
