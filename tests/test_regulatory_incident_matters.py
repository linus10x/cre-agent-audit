"""Per-matter TDD contracts for the three named matters in PR 1.

Each matter declares ``expected_findings()`` and an ``expected_findings.json``
file. The replay must produce findings matching the declared contract.
Drift between the matter file and the contract fails the build.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.regulatory_replay import (
    IncidentReplayBase,
    pattern_coverage_score,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
INCIDENTS_DIR = REPO_ROOT / "examples" / "regulatory-incidents"

MATTERS = [
    "01_transunion_rental_screening",
    "02_saferent_voucher_screening",
    "03_realpage_ongoing_litigation",
]


def _load_matter(matter_dir_name: str) -> IncidentReplayBase:
    replay_py = INCIDENTS_DIR / matter_dir_name / "replay.py"
    spec = importlib.util.spec_from_file_location(f"_matter_{matter_dir_name}", replay_py)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    matter = mod.matter
    assert isinstance(matter, IncidentReplayBase)
    return matter


@pytest.mark.parametrize("matter_dir_name", MATTERS)
def test_matter_loads(matter_dir_name: str) -> None:
    matter = _load_matter(matter_dir_name)
    assert matter.matter_id == matter_dir_name
    assert matter.matter_title
    assert matter.primary_sources
    assert matter.failure_shape
    assert matter.patterns_engaged


@pytest.mark.parametrize("matter_dir_name", MATTERS)
def test_matter_synthetic_dataset_is_non_empty(matter_dir_name: str) -> None:
    matter = _load_matter(matter_dir_name)
    rows = list(matter.synthetic_dataset())
    assert rows, f"{matter_dir_name}: synthetic_dataset() returned empty"


@pytest.mark.parametrize("matter_dir_name", MATTERS)
def test_matter_replay_produces_expected_findings(matter_dir_name: str) -> None:
    matter = _load_matter(matter_dir_name)
    ledger = AuditLedger()
    result = matter.run_replay(ledger=ledger, gates={})
    expected = matter.expected_findings()
    assert len(result.findings_produced) == len(expected), (
        f"{matter_dir_name}: replay produced "
        f"{len(result.findings_produced)} findings; expected {len(expected)}"
    )
    expected_keys = sorted((str(f.pattern), f.severity.value, f.evidence.verdict) for f in expected)
    actual_keys = sorted(
        (str(f.pattern), f.severity.value, f.evidence.verdict) for f in result.findings_produced
    )
    assert actual_keys == expected_keys, (
        f"{matter_dir_name}: finding (pattern,severity,verdict) tuples diverge from expected"
    )


@pytest.mark.parametrize("matter_dir_name", MATTERS)
def test_matter_pattern_coverage_is_full(matter_dir_name: str) -> None:
    matter = _load_matter(matter_dir_name)
    ledger = AuditLedger()
    result = matter.run_replay(ledger=ledger, gates={})
    assert pattern_coverage_score(matter, result) == 1.0


@pytest.mark.parametrize("matter_dir_name", MATTERS)
def test_matter_expected_findings_json_matches_replay(matter_dir_name: str) -> None:
    """expected_findings.json matches what the matter declares in code."""
    matter = _load_matter(matter_dir_name)
    json_path = INCIDENTS_DIR / matter_dir_name / "expected_findings.json"
    declared = json.loads(json_path.read_text(encoding="utf-8"))
    declared_keys = sorted(
        (e["pattern"], e["severity"], e["evidence"]["verdict"]) for e in declared["findings"]
    )
    method_keys = sorted(
        (str(f.pattern), f.severity.value, f.evidence.verdict) for f in matter.expected_findings()
    )
    assert declared_keys == method_keys, (
        f"{matter_dir_name}: expected_findings.json diverges from expected_findings() method"
    )


@pytest.mark.parametrize("matter_dir_name", MATTERS)
def test_matter_evidence_bundle_assembles(matter_dir_name: str) -> None:
    """End-to-end: matter replay → EvidenceBundle assembles."""
    from cre_agent_audit.regulatory_replay import EvidenceBundle

    matter = _load_matter(matter_dir_name)
    ledger = AuditLedger()
    result = matter.run_replay(ledger=ledger, gates={})
    bundle = EvidenceBundle.assemble(matter=matter, ledger=ledger, result=result)
    assert bundle.matter_id == matter.matter_id
    assert len(bundle.artifacts) == 6
