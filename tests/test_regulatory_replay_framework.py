"""Conformance tests for the regulatory_replay framework.

Tests the Protocol surface, dataclass shape, and zip-bundle assembly.
Per-matter behavior is in test_regulatory_incident_matters.py.
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path

import pytest

from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger
from cre_agent_audit.regulatory_replay import (
    ADRRef,
    Citation,
    Evidence,
    EvidenceBundle,
    Finding,
    IncidentReplay,
    IncidentReplayBase,
    ReplayResult,
    Severity,
    pattern_coverage_score,
)


def test_severity_is_enum_with_four_levels() -> None:
    assert {s.value for s in Severity} == {"Critical", "High", "Medium", "Low"}


def test_citation_requires_case_name_court_date() -> None:
    cit = Citation(
        case_name="Louis v. SafeRent Solutions, LLC",
        court="D. Mass.",
        docket="No. 1:22-cv-10800",
        date_iso="2024-11-20",
        url="https://example.test/saferent",
    )
    assert cit.case_name == "Louis v. SafeRent Solutions, LLC"
    assert cit.date_iso == "2024-11-20"


def test_adrref_normalizes_number_to_int() -> None:
    ref = ADRRef(number=8, title="Fair-Housing Pre-Flight Gate")
    assert ref.number == 8
    assert str(ref) == "ADR-0008"


def test_finding_carries_pattern_severity_evidence_anchor() -> None:
    cit = Citation(
        case_name="In re TransUnion Rental Screening Solutions",
        court="FTC + CFPB",
        docket="C-4810 + 2023-CFPB-0008",
        date_iso="2023-10-12",
        url=None,
    )
    f = Finding(
        pattern=ADRRef(number=3, title="Audit Ledger"),
        severity=Severity.HIGH,
        evidence=Evidence(
            chain_sequence_range=(0, 12),
            verdict="chain-of-custody break on 12 entries lacking source-document hash",
        ),
        regulatory_anchor=cit,
        remediation="Require source-document hash field on every entry",
    )
    assert f.pattern.number == 3
    assert f.severity == Severity.HIGH


# --------------------------------------------------------------------------- #
# Stub replay for harness tests                                                #
# --------------------------------------------------------------------------- #


_STUB_CIT = Citation(
    case_name="Stub v. Test",
    court="N.D. Cal.",
    docket="No. stub-001",
    date_iso="2026-01-01",
    url=None,
)


class _StubReplay(IncidentReplayBase):
    matter_id = "00_stub"
    matter_title = "Stub matter for harness conformance"
    primary_sources: tuple[Citation, ...] = (_STUB_CIT,)
    failure_shape = "Stub failure for harness testing"
    patterns_engaged: tuple[ADRRef, ...] = (ADRRef(number=3, title="Audit Ledger"),)

    def synthetic_dataset(self) -> Iterable[dict[str, object]]:
        return [{"applicant_id": "A-001"}]

    def run_replay(
        self,
        *,
        ledger: AuditLedger,
        gates: Mapping[str, object],
    ) -> ReplayResult:
        ledger.append(
            actor_kind=ActorKind.SYSTEM,
            actor_id="stub_replay",
            decision_type="stub_decision",
            action_payload=b"stub",
            gate_verdicts={},
        )
        return ReplayResult(
            matter_id=self.matter_id,
            findings_produced=self.expected_findings(),
            chain_entries_written=len(ledger.entries),
        )

    def expected_findings(self) -> tuple[Finding, ...]:
        return (
            Finding(
                pattern=ADRRef(number=3, title="Audit Ledger"),
                severity=Severity.LOW,
                evidence=Evidence(
                    chain_sequence_range=(0, 0),
                    verdict="stub finding",
                ),
                regulatory_anchor=_STUB_CIT,
                remediation="Stub remediation",
            ),
        )


def test_incident_replay_protocol_conformance() -> None:
    replay: IncidentReplay = _StubReplay()
    assert replay.matter_id == "00_stub"
    assert callable(replay.synthetic_dataset)
    assert callable(replay.run_replay)
    assert callable(replay.expected_findings)


def test_stub_replay_writes_to_ledger() -> None:
    ledger = AuditLedger()
    result = _StubReplay().run_replay(ledger=ledger, gates={})
    assert result.matter_id == "00_stub"
    assert result.chain_entries_written == 1
    assert len(result.findings_produced) == 1


def test_replay_result_round_trip_through_json() -> None:
    ledger = AuditLedger()
    result = _StubReplay().run_replay(ledger=ledger, gates={})
    as_json = result.to_dict()
    assert as_json["matter_id"] == "00_stub"
    assert as_json["chain_entries_written"] == 1
    assert isinstance(as_json["findings_produced"], list)


def test_evidence_bundle_assembles_six_artifacts() -> None:
    ledger = AuditLedger()
    result = _StubReplay().run_replay(ledger=ledger, gates={})
    bundle = EvidenceBundle.assemble(matter=_StubReplay(), ledger=ledger, result=result)
    assert set(bundle.artifacts.keys()) == {
        "audit_chain.jsonl",
        "verify_chain_report.json",
        "mi_proxy_attestation.json",
        "findings.json",
        "controls_description_table.md",
        "narrative.md",
    }


def test_evidence_bundle_writes_valid_zip(tmp_path: Path) -> None:
    ledger = AuditLedger()
    result = _StubReplay().run_replay(ledger=ledger, gates={})
    bundle = EvidenceBundle.assemble(matter=_StubReplay(), ledger=ledger, result=result)
    zip_path = tmp_path / "stub.zip"
    bundle.write_zip(zip_path)
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())
        assert "audit_chain.jsonl" in names
        assert "findings.json" in names
        with z.open("findings.json") as f:
            data = json.load(f)
            assert data["matter_id"] == "00_stub"


def test_evidence_bundle_findings_json_matches_result() -> None:
    ledger = AuditLedger()
    result = _StubReplay().run_replay(ledger=ledger, gates={})
    bundle = EvidenceBundle.assemble(matter=_StubReplay(), ledger=ledger, result=result)
    parsed = json.loads(bundle.artifacts["findings.json"])
    assert parsed == result.to_dict()


def test_pattern_coverage_score_full_coverage() -> None:
    matter = _StubReplay()
    result = ReplayResult(
        matter_id="00_stub",
        findings_produced=(
            Finding(
                pattern=ADRRef(number=3, title="Audit Ledger"),
                severity=Severity.LOW,
                evidence=Evidence(chain_sequence_range=(0, 0), verdict="x"),
                regulatory_anchor=_STUB_CIT,
                remediation="x",
            ),
        ),
        chain_entries_written=1,
    )
    assert pattern_coverage_score(matter, result) == 1.0


def test_pattern_coverage_score_no_coverage() -> None:
    matter = _StubReplay()
    result = ReplayResult(
        matter_id="00_stub",
        findings_produced=(),
        chain_entries_written=0,
    )
    assert pattern_coverage_score(matter, result) == 0.0


def test_cli_list_runs(capsys: pytest.CaptureFixture[str]) -> None:
    from cre_agent_audit.regulatory_replay.cli import main

    exit_code = main(["list"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "matter_id" in out.lower()
