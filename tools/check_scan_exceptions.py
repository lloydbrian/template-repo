"""Fail if a vulnerability exception file holds an undocumented or expired entry.

Used for `.trivyignore` (image scan) and `.pip-audit-ignore` (dependency audit). Every entry reads:
    CVE-2026-12345  # reason: <why not exploitable>; owner: <name>; expires: YYYY-MM-DD
A new entry may say `expires: on-bootstrap`; `mise run bootstrap` replaces it with today + MAX_DAYS
(`--stamp`), and until then the check fails. `--pip-audit-args` prints the ignore flags for
pip-audit, so only documented, unexpired advisories are ever ignored.
Exceptions are time-boxed (at most MAX_DAYS ahead) so accepted risk is re-reviewed instead of
silently living forever. A trivy config or VEX file next to .trivyignore is refused: trivy reads
`trivy.yaml` from the working directory automatically, and it could skip paths or suppress findings
without any of the checks above. TRIVY_* variables in .mise.toml are refused for the same reason.
"""

from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path

ENTRY = re.compile(
    r"^(?P<id>(CVE|GHSA|PYSEC)-[\w-]+)\s+#\s*reason:\s*(?P<reason>[^;]+);\s*owner:\s*(?P<owner>[^;]+);"
    r"\s*expires:\s*(?P<expires>\d{4}-\d{2}-\d{2}|on-bootstrap)\s*$"
)
MAX_DAYS = 90
BYPASS_FILES = ("trivy.yaml", "trivy.yml", ".trivyignore.yaml", ".trivyignore.yml")


def check(path: Path, today: date | None = None) -> list[str]:
    """Return a list of problems; empty means every exception is valid."""
    today = today or date.today()
    problems: list[str] = []
    folder = path.parent
    for name in BYPASS_FILES:
        if (folder / name).exists():
            problems.append(
                f"{folder / name}: trivy config files are not allowed; use .trivyignore"
            )
    for vex in sorted(folder.glob("*vex*.json")):
        problems.append(f"{vex}: VEX files are not allowed; use .trivyignore entries")
    mise = folder / ".mise.toml"
    if mise.exists() and "TRIVY_" in mise.read_text(encoding="utf-8"):
        problems.append(f"{mise}: TRIVY_* settings are not allowed; they override the scan policy")
    if not path.exists():
        return problems
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = ENTRY.match(line)
        if not match:
            problems.append(f"{path}:{n}: needs '# reason: ...; owner: ...; expires: YYYY-MM-DD'")
            continue
        if match["expires"] == "on-bootstrap":
            problems.append(f"{path}:{n}: {match['id']} is not dated yet; run `mise run bootstrap`")
            continue
        expires = date.fromisoformat(match["expires"])
        if expires < today:
            problems.append(f"{path}:{n}: {match['id']} expired on {expires}; re-review or remove")
        elif expires > today + timedelta(days=MAX_DAYS):
            problems.append(
                f"{path}:{n}: {match['id']} expires more than {MAX_DAYS} days ahead; shorten it"
            )
    return problems


def stamp(path: Path, today: date | None = None) -> int:
    """Replace `expires: on-bootstrap` with today + MAX_DAYS; returns how many were dated."""
    if not path.exists():
        return 0
    expires = ((today or date.today()) + timedelta(days=MAX_DAYS)).isoformat()
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    count = 0
    for i, line in enumerate(lines):  # entry lines only: comments are left untouched
        match = ENTRY.match(line.strip())
        if match and match["expires"] == "on-bootstrap":
            lines[i] = re.sub(r"expires:\s*on-bootstrap", f"expires: {expires}", line)
            count += 1
    if count:
        path.write_text("".join(lines), encoding="utf-8")
    return count


def pip_audit_args(path: Path) -> list[str]:
    """`--ignore-vuln ID` for each well-formed entry (run `check` first to reject bad ones)."""
    if not path.exists():
        return []
    args: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = ENTRY.match(raw.strip())
        if match:
            args += ["--ignore-vuln", match["id"]]
    return args


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--stamp":
        dated = stamp(Path(argv[2]))
        if dated:
            print(
                f"{argv[2]}: dated {dated} new exception(s) to expire in {MAX_DAYS} days; commit it"
            )
        return 0
    if len(argv) == 3 and argv[1] == "--pip-audit-args":
        print(" ".join(pip_audit_args(Path(argv[2]))))
        return 0
    problems = check(Path(argv[1] if len(argv) > 1 else ".trivyignore"))
    for p in problems:
        print(p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
