"""Doc/code parity test for FAILURE-MODES.md.

Every detection mechanism named in the matrix as `(F) module.path.callable`
must resolve to a real callable in this codebase. Every `NOT YET IMPLEMENTED`
row must carry a tracking marker. The build fails on either kind of drift —
the matrix is the contract, the test enforces it.
"""

from __future__ import annotations

import importlib
import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FAILURE_MODES = REPO_ROOT / "FAILURE-MODES.md"

# (F) module.path.callable — qualified Python ref the matrix points at.
# Greedy match on the path stops at backtick to avoid eating prose around it.
_CALLABLE_REF_RE = re.compile(r"\(F\)\s+`?([a-zA-Z_][\w.]*)`?")
_DEFERRED_RE = re.compile(r"NOT YET IMPLEMENTED\s+·\s+tracking:\s+([A-Za-z0-9 #_().-]+)")


def _matrix_text() -> str:
    assert FAILURE_MODES.exists(), f"FAILURE-MODES.md missing at {FAILURE_MODES}"
    return FAILURE_MODES.read_text(encoding="utf-8")


def _resolve_callable(qualified_name: str) -> object:
    """Resolve `module.path.attr1.attr2` to the bound attribute."""
    parts = qualified_name.split(".")
    for split in range(len(parts) - 1, 0, -1):
        module_name = ".".join(parts[:split])
        attr_path = parts[split:]
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        obj: object = module
        for attr in attr_path:
            if not hasattr(obj, attr):
                obj = None
                break
            obj = getattr(obj, attr)
        if obj is not None:
            return obj
    raise ImportError(f"Could not resolve {qualified_name!r}")


def test_failure_modes_doc_exists() -> None:
    assert FAILURE_MODES.is_file()


def test_failure_modes_doc_carries_disclaimer() -> None:
    text = _matrix_text()
    assert "Patterns are software, not legal advice." in text


def test_every_callable_reference_resolves() -> None:
    """Every `(F) module.path.fn` in the matrix must point at a real callable.

    If a row's referenced function gets renamed, deleted, or moved without
    the matrix being updated, this test fails — and the build fails.
    """
    refs = sorted(set(_CALLABLE_REF_RE.findall(_matrix_text())))
    assert refs, "Expected at least one (F) callable reference in the matrix"

    unresolved: list[str] = []
    not_callable: list[str] = []
    for qualified in refs:
        try:
            obj = _resolve_callable(qualified)
        except ImportError:
            unresolved.append(qualified)
            continue
        if not callable(obj):
            not_callable.append(qualified)

    assert not unresolved, (
        f"FAILURE-MODES.md references functions that do not resolve: {unresolved}"
    )
    assert not not_callable, f"FAILURE-MODES.md references non-callable attributes: {not_callable}"


def test_deferred_rows_carry_tracking_markers() -> None:
    """`NOT YET IMPLEMENTED` rows must name what tracks them.

    The matrix is allowed to admit gaps, but it is not allowed to admit
    them silently. A row may say `NOT YET IMPLEMENTED · tracking: ADR-XXXX`
    or `... · tracking: (#issue)`; an unlabeled gap fails the build.
    """
    text = _matrix_text()
    if "NOT YET IMPLEMENTED" not in text:
        pytest.skip("No deferred rows in matrix")
    deferred = _DEFERRED_RE.findall(text)
    # Every `NOT YET IMPLEMENTED` substring must be followed by a tracking marker.
    occurrences = text.count("NOT YET IMPLEMENTED")
    assert len(deferred) == occurrences, (
        "Some NOT YET IMPLEMENTED rows are missing tracking markers — "
        f"found {len(deferred)} markers for {occurrences} occurrences"
    )


def test_matrix_covers_all_eight_classes() -> None:
    """Sanity check: 8 numbered rows in the matrix.

    Catches accidental row deletion or table-format corruption.
    """
    text = _matrix_text()
    matrix_section = text.split("## Matrix", 1)[1].split("## Defaults", 1)[0]
    # Count `| N |` numbered rows.
    row_numbers = re.findall(r"^\|\s*(\d+)\s*\|", matrix_section, flags=re.MULTILINE)
    assert row_numbers == [str(n) for n in range(1, 9)], f"Expected rows 1..8, got {row_numbers}"
