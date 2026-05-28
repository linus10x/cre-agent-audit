"""Service-template section lint.

Every `docs/services/NN-*.md` carries the canonical 10-section structure.
Drift between templates fails the build.
"""

from __future__ import annotations

import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SERVICES_DIR = REPO_ROOT / "docs" / "services"

REQUIRED_SECTIONS = [
    "## What you get",
    "## Methodology",
    "## What's NOT in the public framework",
    "## What's NOT in scope",
    "## How to engage",
    "## Pricing",
    "## Disclaimer",
]


def _service_files() -> list[pathlib.Path]:
    return sorted(p for p in SERVICES_DIR.glob("*.md") if p.name != "README.md")


def test_at_least_seven_service_files() -> None:
    files = _service_files()
    assert len(files) >= 7, f"Expected >=7 service files; found {len(files)}"


@pytest.mark.parametrize("service_file", _service_files(), ids=lambda p: p.name)
def test_service_file_has_required_sections(service_file: pathlib.Path) -> None:
    text = service_file.read_text(encoding="utf-8")
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    assert not missing, f"{service_file.name} missing sections: {missing}"


@pytest.mark.parametrize("service_file", _service_files(), ids=lambda p: p.name)
def test_service_file_names_a_price_in_h1(service_file: pathlib.Path) -> None:
    text = service_file.read_text(encoding="utf-8")
    h1 = text.split("\n", 1)[0]
    assert h1.startswith("# "), f"{service_file.name}: expected H1 header"
    assert "$" in h1, f"{service_file.name}: H1 should name a price (e.g. '— $5K')"


@pytest.mark.parametrize("service_file", _service_files(), ids=lambda p: p.name)
def test_service_file_carries_disclaimer(service_file: pathlib.Path) -> None:
    text = service_file.read_text(encoding="utf-8")
    assert "Patterns are software, not legal advice" in text, (
        f"{service_file.name}: disclaimer line required"
    )
