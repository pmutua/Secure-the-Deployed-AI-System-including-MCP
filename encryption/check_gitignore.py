"""Deliverable 1: prove .env was never tracked.

Two independent checks, run from the repository root:

1. `git check-ignore -v .env` must match a rule -- exit code is the
   signal, not the text on stdout, because a command can succeed and
   still print nothing useful.
2. Every Compose file in the repo must not inline a long quoted value
   that looks like a secret. A line is treated as *injected* (safe) if
   it uses `${...}` substitution or a `secrets.` reference; anything
   else that pairs a key name with a long quoted literal is flagged.

Both checks report which one failed and what to do about it, because two
independent failures deserve two independent messages.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

# A quoted value at least this long is treated as "looks like a secret"
# rather than an ordinary short config string (a port number, a flag).
MIN_SECRET_LEN = 32

# Lines carrying either marker are being *injected* at runtime, not
# stored in the file, so they are the pattern we want to pass.
INJECTED_MARKERS = ("${", "secrets.")

# A whole-line "KEY: "long value"" (mapping form) or "- KEY=long value"
# (list form) -- the shape an inlined secret actually takes in a Compose
# `environment:` block. Anchored to the full line rather than searched
# anywhere in it: a healthcheck `test: ["CMD", "python", "-c", "import
# ..."]` array also contains a 32+ character quoted string, and is not a
# secret.
INLINE_SECRET_RE = re.compile(
    rf'^\s*(?:-\s*)?[A-Za-z_][A-Za-z0-9_]*\s*[:=]\s*["\']([^"\']{{{MIN_SECRET_LEN},}})["\']\s*$'
)

COMPOSE_GLOBS = (
    "**/docker-compose*.yml",
    "**/docker-compose*.yaml",
    "**/compose*.yaml",
    "**/compose*.yml",
)

SKIP_DIR_PARTS = {".venv", "venv", "__pycache__", ".git", "node_modules"}


def env_is_gitignored(cwd: Path) -> bool:
    """True only when git actually matches .env against an ignore rule.

    subprocess.run's returncode is the contract git documents for this
    command: 0 means a rule matched, 1 means it did not.
    """
    result = subprocess.run(
        ["git", "check-ignore", "-q", ".env"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _strip_comments(line: str) -> str:
    return line.split("#", 1)[0]


def find_compose_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for pattern in COMPOSE_GLOBS:
        for path in root.glob(pattern):
            if any(part in SKIP_DIR_PARTS for part in path.parts):
                continue
            found.append(path)
    return sorted(set(found))


def scan_compose_file(path: Path) -> list[str]:
    """Return one message per suspicious line, empty when the file is clean."""
    problems = []
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = _strip_comments(raw_line)
        if any(marker in line for marker in INJECTED_MARKERS):
            continue  # value is substituted at runtime, not stored here
        match = INLINE_SECRET_RE.search(line)
        if match:
            problems.append(f"{path}:{lineno}: inlined value looks like a secret")
    return problems


def main(cwd: Path | None = None) -> int:
    cwd = cwd or Path.cwd()

    if not env_is_gitignored(cwd):
        print("FAIL: .env is not gitignored. Add it, then re-run.")
        return 1

    all_problems: list[str] = []
    for compose_file in find_compose_files(cwd):
        all_problems.extend(scan_compose_file(compose_file))

    if all_problems:
        print("FAIL: possible inlined secret(s) in Compose file(s):")
        for problem in all_problems:
            print(" -", problem)
        return 1

    print("OK: .env ignored and Compose looks clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
