"""Blame-aware GitOps: attribute YAML resources to their git authors.

Maps each ``- name:`` entry under ``spec.servers`` to the git blame of its
YAML lines, so reviewers see who last touched a resource, when, and whether
the change looks risky (uncommitted, stale, or touched by many hands).
"""

import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

ZERO_COMMIT = "0" * 40


class BlameError(Exception):
    """Raised when git blame cannot run for a file."""


@dataclass
class BlameLine:
    commit: str
    author: str
    author_time: int


@dataclass
class ResourceBlame:
    name: str
    last_author: str
    last_commit: str
    last_changed: str
    authors: List[str] = field(default_factory=list)
    risk: List[str] = field(default_factory=list)


def run_git_blame(path: str) -> str:
    """Run ``git blame --line-porcelain`` for a file in its own directory."""
    directory = os.path.dirname(os.path.abspath(path))
    try:
        proc = subprocess.run(
            ["git", "blame", "--line-porcelain", "--", os.path.basename(path)],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BlameError(f"git not available: {exc}") from exc
    if proc.returncode != 0:
        detail = proc.stderr.strip() or f"git blame failed for {path}"
        raise BlameError(detail)
    return proc.stdout


def _is_hex(value: str) -> bool:
    return len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def parse_blame_porcelain(output: str) -> Dict[int, BlameLine]:
    """Parse ``git blame --line-porcelain`` into 1-based line attributions."""
    blame: Dict[int, BlameLine] = {}
    commit = ""
    author = ""
    author_time = 0
    lineno = 0
    for raw in output.splitlines():
        if raw.startswith("\t"):
            lineno += 1
            blame[lineno] = BlameLine(
                commit=commit,
                author=author or "unknown",
                author_time=author_time,
            )
        elif raw.startswith("author "):
            author = raw[len("author "):]
        elif raw.startswith("author-time "):
            try:
                author_time = int(raw[len("author-time "):])
            except ValueError:
                author_time = 0
        else:
            parts = raw.split()
            if parts and _is_hex(parts[0]):
                commit, author, author_time = parts[0], "", 0
    return blame


def resource_spans(text: str) -> List[Tuple[str, int, int]]:
    """Find ``- name:`` items under ``servers:`` as (name, start, end) lines.

    Line numbers are 1-based and inclusive. Only the first ``servers:`` block
    is tracked; leaving its indent level closes the block.
    """
    lines = text.splitlines()
    servers_indent: Optional[int] = None
    spans: List[Tuple[str, int, int]] = []
    pending_name = ""
    pending_start = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if servers_indent is None:
            if re.match(r"servers\s*:", stripped):
                servers_indent = indent
            continue
        if indent <= servers_indent:
            if pending_name:
                spans.append((pending_name, pending_start, idx - 1))
                pending_name = ""
            servers_indent = None
            continue
        match = re.match(r"-\s*name\s*:\s*(.+)", stripped)
        if match:
            if pending_name:
                spans.append((pending_name, pending_start, idx - 1))
            pending_name = match.group(1).strip().strip("'\"")
            pending_start = idx
    if pending_name:
        spans.append((pending_name, pending_start, len(lines)))
    return spans


def annotate(
    spans: List[Tuple[str, int, int]],
    blame: Dict[int, BlameLine],
    stale_days: int = 180,
    now: Optional[datetime] = None,
) -> List[ResourceBlame]:
    """Attribute each resource span to authors and flag risky ownership."""
    current = int((now or datetime.now(timezone.utc)).timestamp())
    stale_after = stale_days * 86400
    result: List[ResourceBlame] = []
    for name, start, end in spans:
        entries = [(num, blame[num]) for num in range(start, end + 1) if num in blame]
        if not entries:
            result.append(
                ResourceBlame(
                    name=name,
                    last_author="unknown",
                    last_commit="-",
                    last_changed="-",
                    risk=["unknown"],
                )
            )
            continue
        authors = sorted({entry.author for _, entry in entries})
        uncommitted_lines = [num for num, entry in entries if entry.commit == ZERO_COMMIT]
        recency = {
            num: current if entry.commit == ZERO_COMMIT else entry.author_time
            for num, entry in entries
        }
        newest_num = max(recency, key=lambda num: recency[num])
        newest = blame[newest_num]
        risk: List[str] = []
        if uncommitted_lines:
            risk.append("uncommitted")
        elif recency[newest_num] < current - stale_after:
            risk.append("stale")
        if len(authors) > 3:
            risk.append("many-hands")
        if newest.commit == ZERO_COMMIT:
            last_changed = "uncommitted"
        else:
            last_changed = datetime.fromtimestamp(
                newest.author_time, tz=timezone.utc
            ).date().isoformat()
        result.append(
            ResourceBlame(
                name=name,
                last_author=newest.author,
                last_commit=newest.commit[:7],
                last_changed=last_changed,
                authors=authors,
                risk=risk,
            )
        )
    return result


def blame_file(path: str, stale_days: int = 180) -> List[ResourceBlame]:
    """Blame every server resource declared in a YAML config file."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    spans = resource_spans(text)
    if not spans:
        return []
    return annotate(spans, parse_blame_porcelain(run_git_blame(path)), stale_days)
