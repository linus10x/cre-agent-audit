"""README version-badge consistency test.

Catches the version-marker drift class the existing staleness test misses.

The README carries a shields.io release-tag badge of the form
``release-vX.Y.Z-blue`` and an optional in-flight badge of the form
``in--flight-X.Y.Z.devN-orange``. The in-repo SoT for the version is
``cre_agent_audit.__version__`` and ``pyproject.toml`` ``version =``.
Drift between these surfaces is the class of bug that put the README
out of sync with the published wheel in v0.2.1 (the wheel self-identified
as ``0.2.1.dev2`` because the version marker bump landed after the tag).

Rules enforced:
- README shows at least one release badge of the form ``release-vX.Y.Z``
- The release-badge version is a valid semver-shaped string
- ``__init__.__version__`` and ``pyproject.toml`` ``version`` agree
- If an in-flight badge is present, its version is >= the release-badge
  version and matches the in-repo version marker
"""

from __future__ import annotations

import pathlib
import re

import pytest

import cre_agent_audit

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Shields.io URL-encoded version pattern in README:
#   ![v0.2.1](https://img.shields.io/badge/release-v0.2.1-blue)
# We extract the X.Y.Z from "release-vX.Y.Z" (with shields.io escaping)
_RELEASE_BADGE_RE = re.compile(
    r"shields\.io/badge/release-v(\d+\.\d+\.\d+)-",
)

# In-flight badge:
#   ![v0.2.2.dev0 in flight](https://img.shields.io/badge/in--flight-v0.2.2.dev0-orange)
# Note shields.io escapes a literal '-' as '--' in the badge text path.
_INFLIGHT_BADGE_RE = re.compile(
    r"shields\.io/badge/in--flight-v?(\d+\.\d+\.\d+\.dev\d+)-",
)


def _read_readme() -> str:
    assert README.is_file(), f"README missing at {README}"
    return README.read_text(encoding="utf-8")


def _read_pyproject_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    assert m, "Could not find version = '...' in pyproject.toml"
    return m.group(1)


def _semver_tuple(s: str) -> tuple[int, int, int]:
    parts = s.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def test_readme_carries_a_release_badge() -> None:
    text = _read_readme()
    matches = _RELEASE_BADGE_RE.findall(text)
    assert matches, "README must carry at least one shields.io release-vX.Y.Z badge"


def test_release_badge_version_is_semver() -> None:
    text = _read_readme()
    matches = _RELEASE_BADGE_RE.findall(text)
    for v in matches:
        parts = v.split(".")
        assert len(parts) == 3, f"release badge version {v!r} is not X.Y.Z"
        for p in parts:
            assert p.isdigit(), f"release badge version part {p!r} is not numeric"


def test_init_version_matches_pyproject_version() -> None:
    init_v = cre_agent_audit.__version__
    pyproject_v = _read_pyproject_version()
    assert init_v == pyproject_v, (
        f"cre_agent_audit.__version__ {init_v!r} != pyproject.toml version {pyproject_v!r}"
    )


def test_inflight_badge_matches_init_version_when_present() -> None:
    """If the README has an in-flight badge, it must match ``__version__``.

    The in-flight badge is optional; not every release cycle uses one.
    But when it IS present, drift between it and ``__version__`` is
    the same class of bug the staleness test catches for other claims.
    """
    text = _read_readme()
    matches = _INFLIGHT_BADGE_RE.findall(text)
    if not matches:
        pytest.skip("No in-flight badge in README")
    init_v = cre_agent_audit.__version__
    for badge_v in matches:
        assert badge_v == init_v, (
            f"in-flight badge {badge_v!r} != cre_agent_audit.__version__ {init_v!r}"
        )


def test_inflight_version_dominates_release_version_when_present() -> None:
    """In-flight badge version should be >= release badge version.

    The in-flight marker signals "next pre-release in flight." If it's
    older than the released version, that's a drift signal.
    """
    text = _read_readme()
    release_matches = _RELEASE_BADGE_RE.findall(text)
    inflight_matches = _INFLIGHT_BADGE_RE.findall(text)
    if not release_matches or not inflight_matches:
        pytest.skip("Need both release and in-flight badges to compare")

    for release_v in release_matches:
        for inflight_v in inflight_matches:
            # Strip the .devN suffix for the semver comparison
            inflight_semver = inflight_v.split(".dev", 1)[0]
            assert _semver_tuple(inflight_semver) >= _semver_tuple(release_v), (
                f"in-flight {inflight_v!r} (semver part "
                f"{inflight_semver!r}) is older than release {release_v!r}"
            )
