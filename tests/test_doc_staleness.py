"""Automated drift detection for doc claims about shipped features.

For every name exported from the package (`cre_agent_audit.__all__`), this
test scans the public-facing doc surfaces and fails the build if a
known-deferred marker appears in close proximity to that exported name.

The motivating failure mode (observed 2026-05-28 post-PR-#31 merge):
multiple downstream docs (`docs/LIMITATIONS.md`, `docs/SHIP-RECEIPT.md`,
`ROADMAP.md`, `ARCHITECTURE.md`) still said "v0.3 candidate" for
`VendorScoreGate`, RFC 3161 timestamps, and the witness anchor — features
that had just shipped in `0.2.1.dev2`. The Majors-chamber transparency
hit was real: anyone reading the LinkedIn-post-linked GitHub repo first
encountered the README's accurate state, then drifted-into-stale claims
in the secondary docs.

This test runs in CI. A failure means a recent change to either the
package exports or a doc surface drifted a claim. The fix is the SoT-
propagation discipline (see `feedback_sot_propagation_discipline.md` in
the user's memory): identify the SoT for the claim, edit it first, then
propagate to every downstream doc in the same commit.
"""

from __future__ import annotations

import pathlib
import re

import pytest

import cre_agent_audit

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Public-facing doc surfaces. Internal session artifacts (handoffs, specs,
# plans) are intentionally excluded — they record historical state and
# their claims about "what shipped" are correctly snapshots, not contracts.
PUBLIC_DOC_PATHS = [
    "README.md",
    "ARCHITECTURE.md",
    "ROADMAP.md",
    "FAILURE-MODES.md",
    "THESIS.md",
    "PUBLICATIONS.md",
    "docs/LIMITATIONS.md",
    "docs/SHIP-RECEIPT.md",
    "docs/PRIOR-ART.md",
    "docs/MAPPING-MATRICES.md",
    "docs/services/README.md",
    "docs/services/01-diagnostic-5k.md",
    "docs/services/02-audit-40k.md",
    "docs/services/03-retainer-15k-quarterly.md",
    "docs/services/04-workshop-25k-50k.md",
    "docs/services/05-cohort-50k-200k.md",
    "docs/services/06-private-intel-subscription.md",
    "docs/services/07-practitioner-bench.md",
    "examples/regulatory-incidents/README.md",
]

# ADR files are included with a more permissive rule (they may legitimately
# reference deferred work as forward-looking pointers to OTHER ADRs).
ADR_DIR = REPO_ROOT / "docs" / "adr"

# Markers that signal "this thing is deferred / not yet shipped." If any
# of these appear within `_PROXIMITY_CHARS` of an exported name in the
# `PUBLIC_DOC_PATHS` files, the test fails.
DEFERRED_MARKERS = [
    "v0.3 candidate",
    "v0.3 follow-up",
    "v0.3 candidates",
    "reference implementation in v0.3",
    "implementation in v0.3",
    "ships in v0.3",
    "forthcoming",
    "not yet shipped",
    "design only for v0.2.0",
    "design-only for v0.2.0",
]

# Proximity window in characters. Two-paragraph radius — large enough to
# catch "VendorScoreGate ... reference implementation in v0.3" even with
# a sentence between, small enough to avoid false positives across an
# entire doc.
_PROXIMITY_CHARS = 400

# Exported names that are intentionally exempt because they semantically
# refer to a still-deferred concept. None today; this is the registry for
# future allow-listing if a Protocol gets exported before its concrete
# default backend ships.
EXEMPT_EXPORTS: set[str] = set()

# Specific (file, marker_excerpt) pairs that are intentionally preserved
# meta-prose explaining historical state or supersession. The test allows
# these explicit pairs and fails on any other co-occurrence.
ALLOWED_HISTORICAL_CONTEXTS: list[tuple[str, str]] = [
    # CHANGELOG: explains why "ADR-0013 forthcoming" was superseded by MI Proxy.
    (
        "CHANGELOG.md",
        "agent topology pruning previously referenced as",
    ),
    # ADR-0012: explains the same supersession in the implementation notes.
    (
        "docs/adr/0012-persistence-witness-timestamp-pattern.md",
        'The placeholder "(ADR-0013, forthcoming)" that this section previously carried was superseded',
    ),
]


def _exported_feature_names() -> list[str]:
    """Return the names that are first-party exports of the package.

    Filters out generic names (`__version__`) and names that are too
    short to grep usefully (would create false positives like 'a' inside
    arbitrary words).
    """
    raw = list(cre_agent_audit.__all__)
    return sorted(
        name
        for name in raw
        if not name.startswith("__") and len(name) >= 4 and name not in EXEMPT_EXPORTS
    )


def _load_public_doc_text() -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in PUBLIC_DOC_PATHS:
        p = REPO_ROOT / rel
        if p.is_file():
            out[rel] = p.read_text(encoding="utf-8")
    return out


def _proximity_violations(text: str, exported_name: str, marker: str) -> list[tuple[int, str]]:
    """Find every co-occurrence of ``exported_name`` and ``marker`` within
    ``_PROXIMITY_CHARS`` characters. Returns a list of (line_no, excerpt).
    """
    out: list[tuple[int, str]] = []
    # Word-boundary match on exported_name to avoid partial matches inside
    # other identifiers (e.g., `MIProxy` matching inside `MIProxyKey...`).
    name_re = re.compile(rf"\b{re.escape(exported_name)}\b")
    for name_match in name_re.finditer(text):
        start = max(0, name_match.start() - _PROXIMITY_CHARS)
        end = min(len(text), name_match.end() + _PROXIMITY_CHARS)
        window = text[start:end]
        if marker.lower() not in window.lower():
            continue
        # Compute line number of the name match.
        line_no = text.count("\n", 0, name_match.start()) + 1
        out.append((line_no, window.strip().replace("\n", " ")[:200]))
    return out


def _is_allowed_historical(file_rel: str, window: str) -> bool:
    """Return True if the (file, window) matches a registered historical pair."""
    for allowed_file, allowed_excerpt in ALLOWED_HISTORICAL_CONTEXTS:
        if file_rel == allowed_file and allowed_excerpt.lower() in window.lower():
            return True
    return False


def test_package_has_public_exports() -> None:
    """Sanity: __all__ has at least one usable export name."""
    names = _exported_feature_names()
    assert names, "Expected at least one exported feature name"


def test_public_doc_paths_exist() -> None:
    """Sanity: at least the README and CHANGELOG-adjacent docs are present."""
    docs = _load_public_doc_text()
    assert "README.md" in docs
    assert "docs/LIMITATIONS.md" in docs


def test_no_deferred_marker_near_exported_feature() -> None:
    """No exported feature name should appear within 400 chars of a deferred
    marker in any public doc. Co-occurrence means a downstream doc still
    describes a shipped feature as not-yet-shipped.

    Failure remediation: apply the SoT-propagation discipline. Identify
    which ADR / module is the SoT for the claim, edit it first, then
    propagate to the downstream doc in the same commit.
    """
    names = _exported_feature_names()
    docs = _load_public_doc_text()

    failures: list[str] = []
    for file_rel, text in docs.items():
        for name in names:
            for marker in DEFERRED_MARKERS:
                hits = _proximity_violations(text, name, marker)
                for line_no, window in hits:
                    if _is_allowed_historical(file_rel, window):
                        continue
                    failures.append(
                        f"  {file_rel}:{line_no} — exported name "
                        f"{name!r} within {_PROXIMITY_CHARS} chars of "
                        f"marker {marker!r}\n"
                        f"    excerpt: ...{window}..."
                    )

    if failures:
        msg = (
            "Doc-staleness drift detected — downstream docs describe "
            "shipped features as deferred:\n\n"
            + "\n\n".join(failures)
            + "\n\nApply the SoT-propagation discipline: edit the ADR/module first, "
            "then propagate to the downstream doc in the same commit."
        )
        pytest.fail(msg)


def test_deferred_markers_appear_somewhere() -> None:
    """Sanity for the test itself: the marker list must be findable somewhere
    in the repo's docs (otherwise the test passes vacuously and we wouldn't
    notice if all the regex patterns silently broke).

    Note: the markers we expect to find are in genuinely-deferred contexts
    (ADR-0010 retention sketches; ARCHITECTURE.md ISO/COSO mapping). These
    are NOT failures — they're the test's evidence that the proximity logic
    is real.
    """
    text = "\n".join(
        (REPO_ROOT / "docs" / "adr" / "0010-audit-chain-retention-privilege-discovery.md")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert any(marker.lower() in text.lower() for marker in DEFERRED_MARKERS), (
        "ADR-0010 (retention) is expected to contain at least one deferred "
        "marker for genuinely-v0.3-candidate retention sketches. If this test "
        "fails, the marker list may have drifted out of sync with real usage."
    )
