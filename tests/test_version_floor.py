"""
Guard against an aiohttp lower-bound that the CI matrix cannot exercise.

This package is a multi-version compatibility shim: at import time it branches
on the installed aiohttp version (``< 3.11`` / ``3.11`` / ``>= 3.12``) and the
CI matrix deliberately tests the lowest supported releases (``3.10.11`` and
``3.11.18``).

The declared lower bound (``aiohttp = ">=X"`` in ``pyproject.toml``) must never
rise above the lowest version CI actually tests, otherwise the project claims to
support versions it forbids at install time.

The regular test matrix *cannot* catch this regression: each matrix leg runs
``poetry add aiohttp==<version>``, which rewrites the constraint in the
ephemeral checkout before the suite runs. A floor that is too high therefore
stays green on every leg that pins a version. Only a static check that reads the
committed ``pyproject.toml`` directly — as this test does — surfaces the bug, and
it fires on the un-pinned ``latest`` legs where the constraint is left intact.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


def _parse_version(text: str) -> tuple[int, int, int]:
    """Return (major, minor, patch) for the first version token in ``text``."""
    match = _VERSION_RE.search(text)
    assert match is not None, f"no version found in {text!r}"
    major, minor, patch = match.groups()
    return (int(major), int(minor), int(patch or 0))


def _declared_aiohttp_floor() -> tuple[int, int, int]:
    """Lower bound of the aiohttp constraint declared in pyproject.toml."""
    for line in _PYPROJECT.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if re.match(r"^aiohttp\s*=", stripped):
            return _parse_version(stripped)
    raise AssertionError("no aiohttp dependency line found in pyproject.toml")


def _ci_aiohttp_versions() -> list[tuple[int, int, int]]:
    """Pinned aiohttp versions in the CI matrix (the ``latest`` entry skipped)."""
    versions: list[tuple[int, int, int]] = []
    in_block = False
    for line in _CI_WORKFLOW.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\s*aiohttp_version\s*:", line):
            in_block = True
            continue
        if not in_block:
            continue
        item = re.match(r'^\s*-\s*"([^"]+)"', line)
        if item:
            value = item.group(1)
            if _VERSION_RE.fullmatch(value):  # skip non-pinned entries like "latest"
                versions.append(_parse_version(value))
            continue
        # A non-list, non-blank, non-comment line ends the YAML block.
        if line.strip() and not line.lstrip().startswith("#"):
            break
    return versions


def test_pyproject_aiohttp_floor_is_installable() -> None:
    """Declared aiohttp floor must not exceed the lowest version CI tests."""
    floor = _declared_aiohttp_floor()
    ci_versions = _ci_aiohttp_versions()

    assert ci_versions, "could not parse any pinned aiohttp version from ci.yml"

    lowest_tested = min(ci_versions)
    assert floor <= lowest_tested, (
        f"pyproject declares aiohttp floor {floor}, but the CI matrix tests "
        f"{lowest_tested} — the project would refuse to install on a version it "
        f"claims to support. Lower the floor in pyproject.toml (and re-run "
        f"`poetry lock`) or raise the CI matrix's lowest aiohttp leg."
    )
