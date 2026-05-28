# Regulatory-Incident Replay Framework + Productized Services + Moat Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in the current session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the v0.2.2 candidate work on `main` — a regulatory-incident replay framework with 3 named-matter worked examples, 7 productized service templates, the operator-side AI governance category claim (ADR-0014), and the moat-layer documents (THESIS.md, PUBLICATIONS.md), plus a private memory entry capturing the engagement-capture discipline.

**Architecture:** Three artifact streams. (1) The replay framework as a new `src/cre_agent_audit/regulatory_replay/` subpackage with a Protocol + dataclass surface, an `EvidenceBundle` zip assembler, and a `cre-replay` CLI entry point. (2) Three named-matter examples under `examples/regulatory-incidents/` (TransUnion / SafeRent / RealPage-as-alleged), each a `IncidentReplay` Protocol implementation with synthetic data + expected-findings TDD contract. (3) Seven productized service templates under `docs/services/` (5 public-anchor + 2 private-tier) plus three moat-layer markdown files at repo root and in `docs/adr/`. Single PR landing on `main` with 7 internal commit checkpoints.

**Tech Stack:** Python 3.10+, pytest, ruff, mypy --strict, stdlib only (zipfile, json, pathlib, importlib.resources, dataclasses, typing.Protocol). New `[project.scripts]` entry `cre-replay`. No new runtime dependencies.

**Spec reference:** [`docs/superpowers/specs/2026-05-28-regulatory-incident-replay-and-services-design.md`](../specs/2026-05-28-regulatory-incident-replay-and-services-design.md) at commit `e6a6149`.

**Working tree assumption:** branch is `main` at `e6a6149` (the spec commit) or later. All work on `main`.

---

## File structure

| Path | New / Modify | Responsibility |
|---|---|---|
| `docs/adr/0014-operator-side-ai-governance-category.md` | New | Category-claim ADR (positioning, not technical) |
| `THESIS.md` | New (repo root) | 3-year project commitment |
| `PUBLICATIONS.md` | New (repo root) | Academic publication track |
| `src/cre_agent_audit/regulatory_replay/__init__.py` | New | Re-exports |
| `src/cre_agent_audit/regulatory_replay/findings.py` | New | `Finding`, `Severity`, `Evidence`, `Citation`, `ADRRef` dataclasses |
| `src/cre_agent_audit/regulatory_replay/replay.py` | New | `IncidentReplay` Protocol + `IncidentReplayBase` + `ReplayResult` |
| `src/cre_agent_audit/regulatory_replay/evidence_bundle.py` | New | `EvidenceBundle.assemble()` + `.write_zip()` |
| `src/cre_agent_audit/regulatory_replay/scoring.py` | New | Pattern-coverage scoring per matter |
| `src/cre_agent_audit/regulatory_replay/cli.py` | New | `cre-replay` CLI (list / run / run-all / verify) |
| `src/cre_agent_audit/__init__.py` | Modify | Re-export new types |
| `pyproject.toml` | Modify | Add `[project.scripts] cre-replay = ...` |
| `.gitignore` | Modify | Add `audit-evidence/` pattern |
| `examples/regulatory-incidents/README.md` | New | Gallery |
| `examples/regulatory-incidents/01_transunion_rental_screening/{README.md, replay.py, synthetic_data.json, expected_findings.json}` | New (4) | Matter 01 |
| `examples/regulatory-incidents/02_saferent_voucher_screening/{...}` | New (4) | Matter 02 |
| `examples/regulatory-incidents/03_realpage_ongoing_litigation/{...}` | New (4) | Matter 03 (framed as ALLEGED) |
| `docs/services/README.md` | New | Gallery |
| `docs/services/01-diagnostic-5k.md` | New | $5K Diagnostic |
| `docs/services/02-audit-40k.md` | New | $40K Audit |
| `docs/services/03-retainer-15k-quarterly.md` | New | $15K/q Retainer |
| `docs/services/04-workshop-25k-50k.md` | New | $25K–$50K Workshop |
| `docs/services/05-cohort-50k-200k.md` | New | $50K–$200K Cohort |
| `docs/services/06-private-intel-subscription.md` | New | Private intel ($25K–$100K/yr) |
| `docs/services/07-practitioner-bench.md` | New | Private community ($10K–$50K/yr) |
| `tests/test_regulatory_replay_framework.py` | New | Harness conformance |
| `tests/test_regulatory_incident_matters.py` | New | Per-matter TDD contracts |
| `tests/test_service_templates.py` | New | Service-template section lint |
| `tests/test_doc_staleness.py` | Modify | Extend `PUBLIC_DOC_PATHS` |
| `README.md` | Modify | Cross-link to examples + services + thesis |
| `FAILURE-MODES.md` | Modify | Cross-link Row 7 + Row 8 to matters |
| `~/.claude/projects/.../memory/feedback_engagement_capture_discipline.md` | New (private) | PSF / Maister discipline |
| `~/.claude/projects/.../memory/MEMORY.md` | Modify (private) | Index update |

---

## Task 1: Framework — `Finding`, `Citation`, `Severity` dataclasses (TDD)

**Files:**
- Create: `src/cre_agent_audit/regulatory_replay/__init__.py` (stub)
- Create: `src/cre_agent_audit/regulatory_replay/findings.py`
- Create: `tests/test_regulatory_replay_framework.py`

- [ ] **Step 1: Write the failing test for `Finding`, `Citation`, `Severity`**

```python
# tests/test_regulatory_replay_framework.py
"""Conformance tests for the regulatory_replay framework.

Tests the Protocol surface, dataclass shape, and zip-bundle assembly.
Per-matter behavior is in test_regulatory_incident_matters.py.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from cre_agent_audit.regulatory_replay import (
    ADRRef,
    Citation,
    Evidence,
    Finding,
    Severity,
)


def test_severity_is_enum_with_four_levels() -> None:
    assert {s.value for s in Severity} == {"Critical", "High", "Medium", "Low"}


def test_citation_requires_case_name_court_date() -> None:
    cit = Citation(
        case_name="Louis v. SafeRent Solutions, LLC",
        court="D. Mass.",
        docket="No. 1:22-cv-10800",
        date_iso="2024-11-20",
        url="https://www.courtlistener.com/docket/.../",
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
        remediation="Require source-document hash field on every screening-report entry",
    )
    assert f.pattern.number == 3
    assert f.severity == Severity.HIGH
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "$HOME/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
python3 -m pytest tests/test_regulatory_replay_framework.py -v 2>&1 | tail -15
```

Expected: ModuleNotFoundError for `cre_agent_audit.regulatory_replay`.

- [ ] **Step 3: Write `findings.py`**

```python
# src/cre_agent_audit/regulatory_replay/findings.py
"""Dataclass surface for the regulatory-incident replay framework.

`Finding`, `Severity`, `Evidence`, `Citation`, `ADRRef` are the shared
vocabulary every matter speaks. The Protocol in `replay.py` accepts
`tuple[Finding, ...]` as the expected-findings contract; the
`EvidenceBundle` in `evidence_bundle.py` serializes them to JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    """Finding severity, mapped to the Big-4 audit deliverable scale."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass(frozen=True)
class Citation:
    """A primary-source citation for a regulatory anchor.

    Verbatim case identification per CLAUDE.md voice rules: case name,
    court (or agency), docket, ISO-8601 date. `url` is optional but
    encouraged for verifiability.
    """

    case_name: str
    court: str
    docket: str
    date_iso: str
    url: Optional[str] = None


@dataclass(frozen=True)
class ADRRef:
    """Reference to an ADR by number.

    The framework's patterns are numbered ADR-0001 through ADR-NNNN.
    ADRRef.__str__ formats as `"ADR-NNNN"` for findings reports.
    """

    number: int
    title: str

    def __str__(self) -> str:
        return f"ADR-{self.number:04d}"


@dataclass(frozen=True)
class Evidence:
    """Where in the audit chain the finding's signal lives.

    `chain_sequence_range` is a `(start, end)` tuple over `AuditEntry`
    sequence numbers; `verdict` is the one-line plain-English signal.
    """

    chain_sequence_range: tuple[int, int]
    verdict: str


@dataclass(frozen=True)
class Finding:
    """One finding the replay surfaces.

    Anchored on `pattern` (which ADR caught it), `severity` (Big-4 scale),
    `evidence` (where in the chain), `regulatory_anchor` (primary-source
    citation), and `remediation` (the one-paragraph operator action).
    """

    pattern: ADRRef
    severity: Severity
    evidence: Evidence
    regulatory_anchor: Citation
    remediation: str
```

- [ ] **Step 4: Write `__init__.py` stub**

```python
# src/cre_agent_audit/regulatory_replay/__init__.py
"""Regulatory-incident replay framework (ADR-0014).

Adversarial-audit harness: replays the failure shape of named settled
matters against the cre-agent-audit framework, producing an audit-
evidence bundle showing which patterns would have caught the failure.

Patterns are software, not legal advice. Regulatory citations are
reference mappings; consult counsel for applicability to your control
environment.
"""

from __future__ import annotations

from cre_agent_audit.regulatory_replay.findings import (
    ADRRef,
    Citation,
    Evidence,
    Finding,
    Severity,
)

__all__ = [
    "ADRRef",
    "Citation",
    "Evidence",
    "Finding",
    "Severity",
]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
python3 -m pytest tests/test_regulatory_replay_framework.py -v 2>&1 | tail -15
```

Expected: 4 tests pass.

- [ ] **Step 6: Run ruff + mypy gates**

```bash
ruff check src/cre_agent_audit/regulatory_replay/ tests/test_regulatory_replay_framework.py 2>&1 | tail -3
ruff format src/cre_agent_audit/regulatory_replay/ tests/test_regulatory_replay_framework.py 2>&1 | tail -3
mypy --strict src/cre_agent_audit/regulatory_replay/ 2>&1 | tail -3
```

Expected: all clean.

---

## Task 2: Framework — `IncidentReplay` Protocol + `ReplayResult`

**Files:**
- Create: `src/cre_agent_audit/regulatory_replay/replay.py`
- Modify: `tests/test_regulatory_replay_framework.py` (append)

- [ ] **Step 1: Append failing test for `IncidentReplay` Protocol + `ReplayResult`**

```python
# Append to tests/test_regulatory_replay_framework.py:

from cre_agent_audit.regulatory_replay import (
    IncidentReplay,
    IncidentReplayBase,
    ReplayResult,
)
from cre_agent_audit.governance.audit_chain import ActorKind, AuditLedger


class _StubReplay(IncidentReplayBase):
    matter_id = "00_stub"
    matter_title = "Stub matter for harness conformance"
    primary_sources = (
        Citation(
            case_name="Stub v. Test",
            court="N.D. Cal.",
            docket="No. stub-001",
            date_iso="2026-01-01",
            url=None,
        ),
    )
    failure_shape = "Stub failure for harness testing"
    patterns_engaged = (ADRRef(number=3, title="Audit Ledger"),)

    def synthetic_dataset(self):
        return [{"applicant_id": "A-001"}]

    def run_replay(self, *, ledger, gates):
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

    def expected_findings(self):
        return (
            Finding(
                pattern=ADRRef(number=3, title="Audit Ledger"),
                severity=Severity.LOW,
                evidence=Evidence(
                    chain_sequence_range=(0, 0),
                    verdict="stub finding",
                ),
                regulatory_anchor=self.primary_sources[0],
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
```

- [ ] **Step 2: Run to verify failure**

```bash
python3 -m pytest tests/test_regulatory_replay_framework.py -v 2>&1 | tail -15
```

Expected: ImportError for `IncidentReplay`, `IncidentReplayBase`, `ReplayResult`.

- [ ] **Step 3: Write `replay.py`**

```python
# src/cre_agent_audit/regulatory_replay/replay.py
"""IncidentReplay Protocol + base + ReplayResult.

A subclass of `IncidentReplayBase` implements one named regulatory
matter. The base provides the dataclass attributes and forces the
subclass to implement the three callables. `ReplayResult` is the
returned value, JSON-serializable for the evidence bundle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol, runtime_checkable

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.regulatory_replay.findings import (
    ADRRef,
    Citation,
    Finding,
)


@runtime_checkable
class IncidentReplay(Protocol):
    """The Protocol surface every matter implements.

    Five class attributes describe the matter; three methods produce
    the runnable artifacts. `IncidentReplayBase` provides default
    implementations of the class attributes; subclasses override.
    """

    matter_id: str
    matter_title: str
    primary_sources: tuple[Citation, ...]
    failure_shape: str
    patterns_engaged: tuple[ADRRef, ...]

    def synthetic_dataset(self) -> Iterable[Any]: ...

    def run_replay(
        self,
        *,
        ledger: AuditLedger,
        gates: Mapping[str, object],
    ) -> "ReplayResult": ...

    def expected_findings(self) -> tuple[Finding, ...]: ...


class IncidentReplayBase:
    """Base class for matter implementations.

    Subclasses define the five class attributes and the three methods.
    The base does not enforce abstractness via ABC because Protocol
    runtime_checkable already gives us the shape check we need.
    """

    matter_id: str = ""
    matter_title: str = ""
    primary_sources: tuple[Citation, ...] = ()
    failure_shape: str = ""
    patterns_engaged: tuple[ADRRef, ...] = ()

    def synthetic_dataset(self) -> Iterable[Any]:
        raise NotImplementedError

    def run_replay(
        self,
        *,
        ledger: AuditLedger,
        gates: Mapping[str, object],
    ) -> "ReplayResult":
        raise NotImplementedError

    def expected_findings(self) -> tuple[Finding, ...]:
        raise NotImplementedError


@dataclass(frozen=True)
class ReplayResult:
    """The output of a single matter replay.

    Serializable to JSON via `to_dict()` for the evidence bundle.
    """

    matter_id: str
    findings_produced: tuple[Finding, ...]
    chain_entries_written: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "chain_entries_written": self.chain_entries_written,
            "findings_produced": [
                {
                    "pattern": str(f.pattern),
                    "pattern_title": f.pattern.title,
                    "severity": f.severity.value,
                    "evidence": {
                        "chain_sequence_range": list(f.evidence.chain_sequence_range),
                        "verdict": f.evidence.verdict,
                    },
                    "regulatory_anchor": {
                        "case_name": f.regulatory_anchor.case_name,
                        "court": f.regulatory_anchor.court,
                        "docket": f.regulatory_anchor.docket,
                        "date_iso": f.regulatory_anchor.date_iso,
                        "url": f.regulatory_anchor.url,
                    },
                    "remediation": f.remediation,
                }
                for f in self.findings_produced
            ],
        }
```

- [ ] **Step 4: Update `__init__.py` to re-export `IncidentReplay`, `IncidentReplayBase`, `ReplayResult`**

```python
# Replace the existing __init__.py with:

"""Regulatory-incident replay framework (ADR-0014).

Adversarial-audit harness: replays the failure shape of named settled
matters against the cre-agent-audit framework, producing an audit-
evidence bundle showing which patterns would have caught the failure.

Patterns are software, not legal advice. Regulatory citations are
reference mappings; consult counsel for applicability to your control
environment.
"""

from __future__ import annotations

from cre_agent_audit.regulatory_replay.findings import (
    ADRRef,
    Citation,
    Evidence,
    Finding,
    Severity,
)
from cre_agent_audit.regulatory_replay.replay import (
    IncidentReplay,
    IncidentReplayBase,
    ReplayResult,
)

__all__ = [
    "ADRRef",
    "Citation",
    "Evidence",
    "Finding",
    "IncidentReplay",
    "IncidentReplayBase",
    "ReplayResult",
    "Severity",
]
```

- [ ] **Step 5: Run tests + gates**

```bash
python3 -m pytest tests/test_regulatory_replay_framework.py -v 2>&1 | tail -15
ruff check src/cre_agent_audit/regulatory_replay/ tests/test_regulatory_replay_framework.py 2>&1 | tail -3
ruff format src/cre_agent_audit/regulatory_replay/ tests/test_regulatory_replay_framework.py 2>&1 | tail -3
mypy --strict src/cre_agent_audit/regulatory_replay/ 2>&1 | tail -3
```

Expected: 7 tests pass; all gates clean.

---

## Task 3: Framework — `EvidenceBundle.assemble()` + `.write_zip()`

**Files:**
- Create: `src/cre_agent_audit/regulatory_replay/evidence_bundle.py`
- Modify: `tests/test_regulatory_replay_framework.py` (append)
- Modify: `src/cre_agent_audit/regulatory_replay/__init__.py` (re-export)

- [ ] **Step 1: Append failing test**

```python
# Append to tests/test_regulatory_replay_framework.py:

from cre_agent_audit.regulatory_replay import EvidenceBundle


def test_evidence_bundle_assembles_six_artifacts(tmp_path: Path) -> None:
    """The audit-evidence bundle has 6 files per the spec."""
    ledger = AuditLedger()
    result = _StubReplay().run_replay(ledger=ledger, gates={})
    bundle = EvidenceBundle.assemble(
        matter=_StubReplay(),
        ledger=ledger,
        result=result,
    )
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
        # Validate findings.json round-trips
        with z.open("findings.json") as f:
            data = json.load(f)
            assert data["matter_id"] == "00_stub"


def test_evidence_bundle_findings_json_matches_result() -> None:
    ledger = AuditLedger()
    result = _StubReplay().run_replay(ledger=ledger, gates={})
    bundle = EvidenceBundle.assemble(matter=_StubReplay(), ledger=ledger, result=result)
    parsed = json.loads(bundle.artifacts["findings.json"])
    assert parsed == result.to_dict()
```

- [ ] **Step 2: Run to verify failure**

Expected: ImportError for `EvidenceBundle`.

- [ ] **Step 3: Write `evidence_bundle.py`**

```python
# src/cre_agent_audit/regulatory_replay/evidence_bundle.py
"""Audit-evidence bundle assembly.

Produces a 6-file zip per matter:
- audit_chain.jsonl       — the recorded decisions
- verify_chain_report.json — verify_chain() output
- mi_proxy_attestation.json — verifier integrity
- findings.json           — Finding[] from the replay
- controls_description_table.md — CTRL-NNN → finding mapping
- narrative.md            — executive summary

The bundle is the deliverable a Big-4 partner, BigLaw counsel, or PE
operating partner can hand to their client.
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.regulatory_replay.replay import IncidentReplayBase, ReplayResult


@dataclass(frozen=True)
class EvidenceBundle:
    """A 6-artifact bundle ready to write as a zip."""

    matter_id: str
    artifacts: Mapping[str, str]  # filename → text content

    @classmethod
    def assemble(
        cls,
        *,
        matter: IncidentReplayBase,
        ledger: AuditLedger,
        result: ReplayResult,
    ) -> "EvidenceBundle":
        """Assemble the six artifacts from the replay outputs."""
        audit_chain_jsonl = _format_audit_chain(ledger)
        verify_report = _format_verify_report(ledger)
        mi_proxy_att = _format_mi_proxy_placeholder(matter.matter_id)
        findings_json = json.dumps(result.to_dict(), indent=2, sort_keys=True)
        controls_table = _format_controls_table(matter, result)
        narrative = _format_narrative(matter, result)

        return cls(
            matter_id=matter.matter_id,
            artifacts={
                "audit_chain.jsonl": audit_chain_jsonl,
                "verify_chain_report.json": verify_report,
                "mi_proxy_attestation.json": mi_proxy_att,
                "findings.json": findings_json,
                "controls_description_table.md": controls_table,
                "narrative.md": narrative,
            },
        )

    def write_zip(self, path: Path) -> None:
        """Write the bundle to a zip file at `path`."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, content in self.artifacts.items():
                z.writestr(name, content)


def _format_audit_chain(ledger: AuditLedger) -> str:
    """One JSON object per chain entry, newline-delimited."""
    lines = []
    for entry in ledger.entries:
        lines.append(
            json.dumps(
                {
                    "sequence": entry.sequence,
                    "timestamp": entry.timestamp.isoformat(),
                    "actor_kind": entry.actor_kind.value,
                    "actor_id": entry.actor_id,
                    "decision_type": entry.decision_type,
                    "action_payload_hex": entry.action_payload.hex(),
                    "gate_verdicts": dict(entry.gate_verdicts),
                    "prior_hash": entry.prior_hash,
                    "self_hash": entry.self_hash,
                },
                sort_keys=True,
            )
        )
    return "\n".join(lines) + ("\n" if lines else "")


def _format_verify_report(ledger: AuditLedger) -> str:
    """Run `verify_chain()` and capture the pass/fail signal."""
    from cre_agent_audit.governance.audit_chain import AuditChainTamperError

    try:
        ledger.verify_chain()
        return json.dumps(
            {
                "verified": True,
                "chain_head": ledger.chain_head(),
                "entry_count": len(ledger.entries),
            },
            indent=2,
        )
    except AuditChainTamperError as e:  # pragma: no cover — replay never tampers
        return json.dumps(
            {
                "verified": False,
                "error": str(e),
                "chain_head": ledger.chain_head(),
                "entry_count": len(ledger.entries),
            },
            indent=2,
        )


def _format_mi_proxy_placeholder(matter_id: str) -> str:
    """For replay context, an opt-in MI Proxy attestation placeholder.

    Production deployments pass `mi_proxy` through `verify_chain(mi_proxy=...)`
    and capture the real attestation here. The placeholder documents that
    the seam exists; the matter replay does not exercise it by default.
    """
    return json.dumps(
        {
            "matter_id": matter_id,
            "mi_proxy_invoked": False,
            "note": (
                "MI Proxy attestation is the opt-in fail-closed hook "
                "documented in ADR-0013. For deployment-time bundles, "
                "the deployer wires LocalMIProxy via verify_chain(mi_proxy=...)."
            ),
        },
        indent=2,
    )


def _format_controls_table(
    matter: IncidentReplayBase, result: ReplayResult
) -> str:
    """Markdown table mapping each finding's ADR pattern to CTRL-NNN."""
    rows = ["# Controls description table", ""]
    rows.append(f"**Matter:** {matter.matter_title}")
    rows.append(f"**Matter ID:** `{matter.matter_id}`")
    rows.append("")
    rows.append("| Finding | Pattern | CTRL ref | Severity | Regulatory anchor |")
    rows.append("|---|---|---|---|---|")
    for i, f in enumerate(result.findings_produced, start=1):
        ctrl_ref = f"CTRL-{f.pattern.number:03d}"
        anchor = (
            f"{f.regulatory_anchor.case_name} ({f.regulatory_anchor.court}, "
            f"{f.regulatory_anchor.date_iso})"
        )
        rows.append(
            f"| F-{i:02d} | {f.pattern} ({f.pattern.title}) | "
            f"[{ctrl_ref}](../../../docs/controls/{ctrl_ref.lower()}-*.md) | "
            f"{f.severity.value} | {anchor} |"
        )
    rows.append("")
    rows.append(
        "> Patterns are software, not legal advice. "
        "Regulatory citations are reference mappings; "
        "consult counsel for applicability to your control environment."
    )
    return "\n".join(rows) + "\n"


def _format_narrative(matter: IncidentReplayBase, result: ReplayResult) -> str:
    """One-page executive summary of the replay."""
    paragraphs = [
        f"# Replay narrative — {matter.matter_title}",
        "",
        f"**Matter ID:** `{matter.matter_id}`",
        "",
        "## Failure shape",
        "",
        matter.failure_shape,
        "",
        "## Patterns engaged",
        "",
    ]
    for adr in matter.patterns_engaged:
        paragraphs.append(f"- {adr} — {adr.title}")
    paragraphs.extend(
        [
            "",
            "## What this replay produced",
            "",
            f"- {result.chain_entries_written} audit-chain entries written",
            f"- {len(result.findings_produced)} findings surfaced",
            "",
            "## Primary-source citations",
            "",
        ]
    )
    for cit in matter.primary_sources:
        line = (
            f"- *{cit.case_name}* — {cit.court}, {cit.docket}, {cit.date_iso}"
        )
        if cit.url:
            line += f" — [link]({cit.url})"
        paragraphs.append(line)
    paragraphs.extend(
        [
            "",
            "## Disclaimer",
            "",
            (
                "This replay is a worked example. It is not legal advice and "
                "does not adjudicate the underlying matter. Patterns are "
                "software; regulatory characterizations are reference "
                "mappings — consult counsel for applicability."
            ),
        ]
    )
    return "\n".join(paragraphs) + "\n"
```

- [ ] **Step 4: Update `__init__.py` to re-export `EvidenceBundle`**

```python
# Add to the existing __init__.py imports and __all__:
from cre_agent_audit.regulatory_replay.evidence_bundle import EvidenceBundle

# Add "EvidenceBundle" to __all__
```

- [ ] **Step 5: Run tests + gates**

```bash
python3 -m pytest tests/test_regulatory_replay_framework.py -v 2>&1 | tail -15
ruff check src/cre_agent_audit/regulatory_replay/ 2>&1 | tail -3
ruff format src/cre_agent_audit/regulatory_replay/ 2>&1 | tail -3
mypy --strict src/cre_agent_audit/regulatory_replay/ 2>&1 | tail -3
```

Expected: 10 tests pass; all gates clean.

---

## Task 4: Framework — pattern-coverage scoring + CLI

**Files:**
- Create: `src/cre_agent_audit/regulatory_replay/scoring.py`
- Create: `src/cre_agent_audit/regulatory_replay/cli.py`
- Modify: `pyproject.toml` (entry point)
- Modify: `src/cre_agent_audit/regulatory_replay/__init__.py`
- Modify: `tests/test_regulatory_replay_framework.py` (append)
- Modify: `.gitignore`

- [ ] **Step 1: Append failing tests for scoring + CLI**

```python
# Append to tests/test_regulatory_replay_framework.py:

from cre_agent_audit.regulatory_replay import pattern_coverage_score


def test_pattern_coverage_score_full_coverage() -> None:
    """When every declared pattern fires, score is 1.0."""
    matter = _StubReplay()
    result = ReplayResult(
        matter_id="00_stub",
        findings_produced=(
            Finding(
                pattern=ADRRef(number=3, title="Audit Ledger"),
                severity=Severity.LOW,
                evidence=Evidence(chain_sequence_range=(0, 0), verdict="x"),
                regulatory_anchor=matter.primary_sources[0],
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
    # 'list' prints a header + matter rows; CI passes if 'matter_id' header is present
    assert "matter_id" in out.lower()
```

- [ ] **Step 2: Run to verify failure**

Expected: ImportError for `pattern_coverage_score`, `cli.main`.

- [ ] **Step 3: Write `scoring.py`**

```python
# src/cre_agent_audit/regulatory_replay/scoring.py
"""Pattern-coverage scoring per matter.

For each matter, compare declared `patterns_engaged` against patterns
actually surfaced in `findings_produced`. Returns a 0.0-to-1.0 score.
Used by the CLI to flag matter drift (replay outputs that no longer
match the declared coverage).
"""

from __future__ import annotations

from cre_agent_audit.regulatory_replay.replay import (
    IncidentReplayBase,
    ReplayResult,
)


def pattern_coverage_score(
    matter: IncidentReplayBase, result: ReplayResult
) -> float:
    """Fraction of declared patterns that produced at least one finding."""
    declared = {adr.number for adr in matter.patterns_engaged}
    if not declared:
        return 0.0
    fired = {f.pattern.number for f in result.findings_produced}
    overlap = declared & fired
    return len(overlap) / len(declared)
```

- [ ] **Step 4: Write `cli.py`**

```python
# src/cre_agent_audit/regulatory_replay/cli.py
"""cre-replay CLI — list / run / run-all / verify.

Entry point in pyproject.toml `[project.scripts]`.

Discovery: matters are Python modules under `examples/regulatory-incidents/
<NN>_<slug>/replay.py` exposing a top-level `matter` instance of an
`IncidentReplayBase` subclass.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Iterable, Optional

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.regulatory_replay.evidence_bundle import EvidenceBundle
from cre_agent_audit.regulatory_replay.replay import IncidentReplayBase
from cre_agent_audit.regulatory_replay.scoring import pattern_coverage_score


def _examples_dir() -> Path:
    # Walk up from this file to find the repo root, then the examples dir.
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "examples" / "regulatory-incidents"
        if candidate.is_dir():
            return candidate
    raise RuntimeError("Could not locate examples/regulatory-incidents/")


def _discover_matters() -> list[IncidentReplayBase]:
    """Scan the examples directory and load each `matter` instance."""
    out: list[IncidentReplayBase] = []
    base = _examples_dir()
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        replay_py = child / "replay.py"
        if not replay_py.is_file():
            continue
        spec = importlib.util.spec_from_file_location(
            f"_matter_{child.name}", replay_py
        )
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        matter = getattr(mod, "matter", None)
        if isinstance(matter, IncidentReplayBase):
            out.append(matter)
    return out


def _cmd_list(args: argparse.Namespace) -> int:
    matters = _discover_matters()
    print(f"{'matter_id':<40} {'title'}")
    print("-" * 100)
    for m in matters:
        print(f"{m.matter_id:<40} {m.matter_title}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    matters = {m.matter_id: m for m in _discover_matters()}
    if args.matter_id not in matters:
        print(f"unknown matter_id: {args.matter_id}", file=sys.stderr)
        print("available:", ", ".join(matters), file=sys.stderr)
        return 2
    matter = matters[args.matter_id]
    ledger = AuditLedger()
    result = matter.run_replay(ledger=ledger, gates={})
    bundle = EvidenceBundle.assemble(matter=matter, ledger=ledger, result=result)
    out_path = _examples_dir() / matter.matter_id / "audit-evidence" / f"{matter.matter_id}.zip"
    bundle.write_zip(out_path)
    score = pattern_coverage_score(matter, result)
    print(f"matter:   {matter.matter_id}")
    print(f"findings: {len(result.findings_produced)}")
    print(f"coverage: {score:.2f}")
    print(f"bundle:   {out_path}")
    return 0


def _cmd_run_all(args: argparse.Namespace) -> int:
    exit_codes: list[int] = []
    for matter in _discover_matters():
        rc = _cmd_run(argparse.Namespace(matter_id=matter.matter_id))
        exit_codes.append(rc)
        print("---")
    return max(exit_codes, default=0)


def _cmd_verify(args: argparse.Namespace) -> int:
    """Re-validate a previously-generated bundle."""
    import zipfile

    zip_path = Path(args.bundle_path)
    if not zip_path.is_file():
        print(f"bundle not found: {zip_path}", file=sys.stderr)
        return 2
    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())
        required = {
            "audit_chain.jsonl",
            "verify_chain_report.json",
            "mi_proxy_attestation.json",
            "findings.json",
            "controls_description_table.md",
            "narrative.md",
        }
        missing = required - names
        if missing:
            print(
                f"bundle missing required artifacts: {sorted(missing)}",
                file=sys.stderr,
            )
            return 1
    print(f"bundle valid: {zip_path}")
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cre-replay",
        description="Replay named regulatory matters against cre-agent-audit",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list discovered matters")

    p_run = sub.add_parser("run", help="run one matter")
    p_run.add_argument("matter_id")

    sub.add_parser("run-all", help="run all matters")

    p_verify = sub.add_parser("verify", help="re-validate a bundle")
    p_verify.add_argument("bundle_path")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "list":
        return _cmd_list(args)
    if args.cmd == "run":
        return _cmd_run(args)
    if args.cmd == "run-all":
        return _cmd_run_all(args)
    if args.cmd == "verify":
        return _cmd_verify(args)
    parser.error("unknown command")
    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
```

- [ ] **Step 5: Update `__init__.py` to re-export `pattern_coverage_score`**

```python
# Add import + __all__ entry:
from cre_agent_audit.regulatory_replay.scoring import pattern_coverage_score
# Add "pattern_coverage_score" to __all__
```

- [ ] **Step 6: Modify `pyproject.toml` to add the entry point**

Read the current `[project.scripts]` section (may not exist). Add or extend:

```toml
[project.scripts]
cre-replay = "cre_agent_audit.regulatory_replay.cli:main"
```

- [ ] **Step 7: Modify `.gitignore` to exclude generated bundles**

Append:

```
# Generated audit-evidence bundles (per-matter)
examples/regulatory-incidents/*/audit-evidence/
```

- [ ] **Step 8: Run tests + gates**

```bash
python3 -m pytest tests/test_regulatory_replay_framework.py -v 2>&1 | tail -15
ruff check src/cre_agent_audit/regulatory_replay/ 2>&1 | tail -3
ruff format src/cre_agent_audit/regulatory_replay/ 2>&1 | tail -3
mypy --strict src/cre_agent_audit/regulatory_replay/ 2>&1 | tail -3
```

Expected: 13 tests pass (4 + 3 + 3 + 3); all gates clean. The CLI list test passes because `_discover_matters()` returns `[]` when no matter directories exist yet — `print` still emits the header.

- [ ] **Step 9: Re-export new types from package root `__init__.py`**

Modify `src/cre_agent_audit/__init__.py` to import + export the regulatory_replay surface:

```python
# Add to imports:
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

# Add to __all__ under a new comment header:
#     # Regulatory-incident replay framework (ADR-0014)
#     "ADRRef",
#     "Citation",
#     "Evidence",
#     "EvidenceBundle",
#     "Finding",
#     "IncidentReplay",
#     "IncidentReplayBase",
#     "ReplayResult",
#     "Severity",
#     "pattern_coverage_score",
```

- [ ] **Step 10: Commit (this completes Commit 2 of 7)**

```bash
cd "$HOME/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
git add src/cre_agent_audit/regulatory_replay/ src/cre_agent_audit/__init__.py \
        pyproject.toml .gitignore tests/test_regulatory_replay_framework.py
git commit -m "feat(regulatory-replay): IncidentReplay Protocol + EvidenceBundle + cre-replay CLI

Adds src/cre_agent_audit/regulatory_replay/ subpackage:
- findings.py — Finding, Severity, Evidence, Citation, ADRRef dataclasses
- replay.py — IncidentReplay Protocol + IncidentReplayBase + ReplayResult
- evidence_bundle.py — EvidenceBundle.assemble() + .write_zip() producing
  the 6-artifact bundle (audit_chain.jsonl, verify_chain_report.json,
  mi_proxy_attestation.json, findings.json, controls_description_table.md,
  narrative.md)
- scoring.py — pattern_coverage_score(matter, result)
- cli.py — cre-replay CLI (list / run / run-all / verify); discovers
  matters from examples/regulatory-incidents/*/replay.py

pyproject.toml: new [project.scripts] cre-replay entry point.
.gitignore: excludes generated audit-evidence/ outputs.
package __init__.py: re-exports the new types.

Tests (13 new):
- Severity enum levels
- Citation primary-source shape
- ADRRef formatting (ADR-NNNN)
- Finding composition
- IncidentReplay Protocol conformance
- Stub replay writes to ledger
- ReplayResult JSON round-trip
- EvidenceBundle 6-artifact assembly
- EvidenceBundle write_zip + read-back
- findings.json matches result.to_dict()
- pattern_coverage_score full + zero coverage
- CLI list runs (empty matters case)

Zero new runtime dependencies. ruff + ruff format + mypy --strict clean."
```

---

## Task 5: ADR-0014 — operator-side AI governance category claim (Commit 1, Part A)

**Files:**
- Create: `docs/adr/0014-operator-side-ai-governance-category.md`

- [ ] **Step 1: Write the ADR**

```markdown
# ADR-0014 · Operator-Side AI Governance for Regulated Industries (Category Claim)

**Status:** Accepted — 2026-05-28
**Decider:** Kunjar Bhaduri
**Pairs with:** ADR-0003 (audit ledger), ADR-0011 (vendor-output adapter), ADR-0012 (persistence/timestamps/witness), ADR-0013 (MI Proxy)

> **⚠ Reference pattern, not legal advice.** This ADR records a category-claim decision (positioning), not a technical decision. Regulatory characterizations are reference mappings; consult counsel. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

The AI-governance market is fragmenting into two distinct positions:

1. **Vendor-side AI governance** — solutions sold by the AI vendor *to operators using that vendor's AI*. Examples in CRE: RealPage Compliance Studio, Yardi Risk, MRI Compliance, SafeRent Audit. These solutions are mature, well-funded, and well-distributed. They have one structural problem: they cannot credibly audit the vendor's own product without compromising the vendor's commercial interests. The operator gets compliance theater, not adversarial integrity.

2. **Operator-side AI governance** — controls + audit infrastructure deployed *by the operator independently of the vendor*, instrumenting the boundary at which vendor outputs enter the operator's decision pipeline. The operator owns the chain-of-custody; the audit ledger captures every vendor decision; the patterns are vendor-agnostic.

The settled-liability anchors of record — TransUnion Rental Screening Solutions (FTC + CFPB consent orders, October 2023, $15M, FCRA § 607(b) accuracy); *Louis v. SafeRent Solutions, LLC*, No. 1:22-cv-10800 (D. Mass.) class settlement, November 20, 2024, approximately $2.275M with a five-year score-use injunction; *U.S. v. RealPage, Inc. et al.* (M.D.N.C., filed August 23, 2024 by DOJ + 8 state attorneys general, **ongoing antitrust litigation**) — all share a common structural feature: **the operator carried the liability, not the vendor.** Operators who relied on vendor-side audit could not produce the operator-side evidence the regulators demanded.

`cre-agent-audit` is a framework for operator-side AI governance in commercial real estate. This ADR names the category claim explicitly.

## Decision

`cre-agent-audit` (CRE-vertical) and `finserv-agent-audit` (FSI-vertical) are reference implementations of an architectural category: **operator-side AI governance for regulated industries**. The Autonomy Ladder™ A0→A4 framework is the autonomy-level abstraction; the per-vertical pattern libraries are the artifact stacks.

The category is defined by these three structural commitments:

1. **The operator owns the audit ledger.** The chain-of-custody for every AI decision lives in operator infrastructure, not vendor infrastructure. The vendor provides a score; the operator's ledger captures the input, the vendor's output, the operator's decision, the human-in-loop, and the appeal — as one hash-chained record.

2. **Patterns are vendor-agnostic by construction.** `VendorScoreGate` (ADR-0011 + v0.2.1 update) accepts inputs from any vendor; `SovereignVeto` (ADR-0002) overrides any vendor recommendation; `FairHousingPreflightGate` (ADR-0008) screens any vendor's input model. No pattern is coupled to any specific vendor's API or scoring function.

3. **Audit-evidence is operator-producible.** The audit-evidence bundle (per `EvidenceBundle` shipping in v0.2.2 alongside the regulatory-replay framework) is something the operator produces and hands to their auditor / regulator / counsel — without vendor involvement. The vendor is never the source of evidence about the vendor.

## Consequences

**Positive.**
- The category claim sets up vendor-side incumbents (RealPage Compliance, Yardi Risk, MRI Compliance) as compromised — they cannot counter-position without commercial-interest conflicts.
- Operators evaluating AI-governance solutions have a clear architectural frame: did we get vendor-side audit (the vendor grading itself) or operator-side audit (we own the chain)?
- Adjacent verticals (insurance, healthcare, FSI) can inherit the operator-side commitment without re-deriving the framework's structural properties.

**Negative.**
- The category is wider than CRE. Concentration on CRE through v0.2.x means the meta-positioning is implicit. v0.3+ work should make it explicit (e.g., `autonomy-ladder.io` meta-positioning, cross-vertical ADR alignment).
- Naming the category invites incumbents to claim it. The defense is execution: continued framework maturity + named-matter coverage + sustained publishing cadence.

**Architectural.**
- Future patterns are gated on the three structural commitments. Any pattern that requires the vendor to cooperate (e.g., a vendor-provided attestation that cannot be operator-verified) is rejected by the category. The MI Proxy in ADR-0013 is the explicit canon: even the verifier is operator-attestable.
- The Regulatory-Incident Replay framework shipping alongside this ADR (v0.2.2) operationalizes the category claim — every named matter the framework replays is one in which operator-side audit would have produced the evidence the vendor-side audit did not.

## Alternatives considered

| Alternative | Why rejected |
|---|---|
| Frame as "AI governance" generally | Generic category with 500+ entrants; no defensible differentiation; commodity pricing pressure. |
| Frame as "CRE-only AI governance" | Under-prices the framework's structural commitments; doesn't transfer to the FSI sibling repo; misses the inter-vertical defensibility. |
| Frame as "vendor-neutral AI audit" | Implies vendor-side could be neutral; obscures the structural conflict. |
| Frame as "regulator-friendly AI governance" | Implies regulator audience first; the framework is operator-first by design. |
| Don't claim a category | Lets competitors define the terms; cedes positioning advantage; accepts commodity outcomes. |

## Regulatory mapping

- **SOC 2 CC7.2** — Operator-side audit infrastructure satisfies the "monitoring of system" criterion in a way that vendor-grading-itself does not.
- **SOX 404 ITGC** — The operator-controlled audit ledger satisfies the change-management and access-control criteria the auditor exercises; vendor-side audit fails the same exercise because the vendor is not the audited entity.
- **FFIEC IT Handbook App J** — Third-party risk management; this category explicitly acknowledges the vendor as the third-party risk and instruments accordingly.
- **CFPB Circular 2022-03** — adverse-action notice obligations are operator-side, not vendor-side; the framework supports the operator's documentary burden.
- **HUD final rule (June 2024)** restoring the Obama-era disparate-impact framework — operator-side audit is the evidentiary path for the three-step burden-shifting analysis.
- **Colorado SB 189** (signed 2026-03-14, effective 2027-01-01) — operator AI deployers in CO need operator-side records by January 2027.

## Related

- ADR-0003 — Hash-chained audit ledger (the operator-side chain-of-custody)
- ADR-0011 — Vendor-output adapter (the vendor-input boundary)
- ADR-0012 — Persistence / timestamps / witness anchor (the substrate-level operator commitments)
- ADR-0013 — MI Proxy (operator-attestable verifier)
- `THESIS.md` — three-year project commitment grounded on this category
- `PUBLICATIONS.md` — academic publication track defending the category claim
- `examples/regulatory-incidents/` — named-matter replays demonstrating operator-side audit outputs

## Implementation notes

This ADR is positioning, not code. The supporting code shipping alongside is:

- `src/cre_agent_audit/regulatory_replay/` — the framework that operationalizes the category claim
- `examples/regulatory-incidents/` — three named-matter replays (TransUnion, SafeRent, RealPage-as-alleged)
- `docs/services/` — seven productized service templates anchored on the category
- `THESIS.md` + `PUBLICATIONS.md` — the long-term commitment to the category

Future ADRs (likely 0015+) build on this one: any new pattern, any new vertical, any new product offering is measured against the three structural commitments.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
```

- [ ] **Step 2: Run the doc-staleness test to confirm the new ADR doesn't drift any existing claims**

```bash
python3 -m pytest tests/test_doc_staleness.py -v 2>&1 | tail -5
```

Expected: 4 tests pass.

- [ ] **Step 3: Defer commit** (bundled into Commit 1 with Tasks 6 and 7)

---

## Task 6: THESIS.md — 3-year project commitment (Commit 1, Part B)

**Files:**
- Create: `THESIS.md` (repo root)

- [ ] **Step 1: Write the THESIS**

```markdown
# THESIS — A 3-year project (2026 → 2028)

**Status:** Public commitment · maintained by Kunjar Bhaduri · last refreshed 2026-05-28

This document records what this project is, why it persists across years not weeks, and what the public surface should look like at each milestone. The point of writing this down is so that visitors three months from now or three years from now can verify the framework was advanced as committed — not abandoned mid-arc.

## The thesis

Operator-side AI governance for regulated industries is a category of software that does not exist as a defined market in 2026 because the buyers — operators carrying the liability when their vendor AI fails — have not yet named what they need. The named-matter record (TransUnion 2023, SafeRent 2024, RealPage ongoing) has changed that. Operators now know what audit-evidence they need to produce; few have it; almost none can produce it from their existing vendor stack.

This project is the public framework + the productized services + the published commentary that names that category, populates it with reference implementations, and earns the right to be cited as canonical over the 2026-2028 window.

## Cornered resource (Five Pillars — non-replicable)

The reason this project is durable: the author's combination of operator credentials cannot be assembled by anyone starting from scratch in less than 20 years.

1. **$750M wealth-platform anchor account rescue** at a top-3 wealth-platform vendor
2. **12-day ransomware crisis** rebuilt on Azure in 50 days; SOC 2 Type 2 + ISO 27001 in the same window
3. **$7M → $140M P&L growth** over an 18-year arc; JPMorgan Chase Partner of the Year 2007 · 2009 · 2010
4. **Autonomy Ladder™ governance framework** — author of A0→A4 (`linus10x/cre-agent-audit`, `linus10x/finserv-agent-audit`, `autonomy-ladder.io`)
5. **PE-acquisition-to-divestiture operating arc** at a regulated-industry technology platform — full hold-period operating cadence

Every chapter is rare. The combination is irreproducible. The framework is the public surface of the combination.

## Three-year roadmap

### 2026 — Foundation + category claim

- ✅ **v0.2.0** released 2026-06-02 — 9 governance patterns, 142 tests, zero runtime dependencies
- ✅ **v0.2.1** released 2026-05-28 — 4 hardening ADRs (persistence, timestamps, witness anchor, MI Proxy), 234 tests, FAILURE-MODES.md matrix-as-contract, DOI [10.5281/zenodo.20434575](https://doi.org/10.5281/zenodo.20434575)
- **v0.2.2** — Regulatory-Incident Replay framework + 3 matters + ADR-0014 (operator-side category claim) + this THESIS — target Q3 2026
- **v0.3.0** — Production-deployment hardening, state-by-state regulatory coverage (TX, NY, CA, WA, FL), full ISO/IEC 42001 mapping — target Q4 2026

### 2027 — Commercial wedge + peer-reviewed credibility

- **v0.4.0** — PyPI publication, FINOS AIR Working Group submission, mermaid sequence diagrams for all 9 patterns, lease-abstraction litigation-discovery worked example
- **First $5K Diagnostic engagement signed** — committed milestone 2026-08-21 per `Applications-May-2026/v2-Refresh/Memos/Regulated_Operations_AI_Governance_Business_Plan_v3_LOCKED_2026-05-21.md`
- **First peer-reviewed publication** — ACM SEMS or FAccT submission on matrix-as-contract pattern
- **finserv-agent-audit parity** — bring the FSI sibling to v0.2.1-equivalent state

### 2028 — Category-cited + scaled

- **v0.5.0** — Multi-agent topology audit (extending AuditConsumer), commercial-extras layer documented (Postgres / S3 / DynamoDB adapter implementations as separate repos)
- **3 cumulative peer-reviewed publications** (target: 1 per year)
- **State of CRE-AI Governance** quarterly report — annual cadence established
- **Practitioner bench (private community)** — 30-60 paying members across Big-4 / BigLaw / PE / CTO seats

## Publishing cadence (load-bearing for the brand moat)

- **Weekly**: LinkedIn Mon/Wed/Fri + X Tue/Thu per CLAUDE.md cadence
- **Quarterly**: "State of CRE-AI Governance" published report
- **Annually**: One peer-reviewed paper submission to ACM SEMS / FAccT / SAFE consortium / Journal of Risk & Financial Management
- **Per merge**: Framework release notes + DOI on major releases

## Productization commitment (the revenue stream)

Per `Applications-May-2026/v2-Refresh/Memos/Regulated_Operations_AI_Governance_Business_Plan_v3_LOCKED_2026-05-21.md` (Path B):

- **$5K Diagnostic** — 90-minute interview + 20-page deliverable
- **$40K Audit** — 4-week engagement; produces full audit-evidence bundle
- **$15K/q Retainer** — quarterly rerun + new-matter coverage + regulatory-update brief
- **$25K-$50K Workshop** — 1-day on-site or 2-day virtual; Big-4 / BigLaw / PE
- **$50K-$200K Cohort** — 8-week program; 20-40 seats
- **$25K-$100K/yr private intel subscription** — gated newsletter + private failure-mode catalog + deposition playbooks (forthcoming)
- **$10K-$50K/yr practitioner bench** — invite-only community (forthcoming)

The framework is open-source (MIT) and free. The engagements are not. The framework is the credential; the engagement is the deliverable.

## What this project will NOT become

- A vendor-side AI-governance product (would compromise the category claim)
- A consultancy that competes on Big-4 RFPs (different buying motion; pricing collapses; reputation dilutes)
- A SaaS product (out of scope for solo operator capacity; commercial-extras model preserves option value)
- A free-tier consulting practice (pricing IS the moat; sub-$5K work is declined as a matter of standing rule)
- A multi-vertical framework before CRE + FSI are at parity (focus is the moat; rushing to insurance / healthcare before the two priors are mature dilutes everything)

## Verifiability

The commitments in this document are verifiable against the repo. Every milestone above maps to:

- A version tag (`git tag`)
- A DOI on Zenodo
- A peer-reviewed publication (when applicable)
- A dated commit on `main`

If the project drifts from this thesis without a public revision, future readers should treat the drift as a signal — not as silent re-scoping. Honest revisions are welcomed; silent abandonment is a credibility failure.

This thesis updates with revision dates at the top. Older versions remain in `git log`.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
```

- [ ] **Step 2: Defer commit** (bundled into Commit 1 with Tasks 5 and 7)

---

## Task 7: PUBLICATIONS.md — academic publication track (Commit 1, Part C)

**Files:**
- Create: `PUBLICATIONS.md` (repo root)

- [ ] **Step 1: Write `PUBLICATIONS.md`**

```markdown
# PUBLICATIONS — Academic publication track

**Status:** Public commitment · maintained by Kunjar Bhaduri · last refreshed 2026-05-28

This document records the academic publication targets for the `cre-agent-audit` and `finserv-agent-audit` projects. The point of an explicit publication track is to make the framework defensible against academic-credibility competitors (researchers at Bailey-Borghesi, Stuart Russell, Solon Barocas, Margaret Mitchell, Timnit Gebru level) and to signal to potential adopters that the methodology is going through peer review.

## Why publication matters here

Risk committees at Tier-1 banks, top-10 health insurance carriers, and Big-4 partner deliverables cite *peer-reviewed methodology*. A framework with zero peer-reviewed citations reads as practitioner commentary regardless of its technical merit. A framework with two or three peer-reviewed publications survives Daubert-grade scrutiny and Big-4 methods-review.

## Target venues

| Venue | Why | Submission shape |
|---|---|---|
| **ACM SEMS** (Symposium on Engineering & Mathematics of Security) | Methods + matrix-as-contract pattern fits the venue's engineering-meets-security focus. | Short paper, 8-10 pages |
| **ACM FAccT** (Conference on Fairness, Accountability, and Transparency) | Operator-side proxy detection (when the MI-threshold detector lands) + the fair-housing pre-flight gate match FAccT's policy-AI-fairness intersection. | Full paper, 12-15 pages |
| **Journal of Risk & Financial Management** (MDPI, peer-reviewed open access) | Triple-witness (RFC 3161 + Sigstore Rekor + MI Proxy) as audit-evidence pattern for SOX 404 ITGC; cross-vertical (CRE + FSI). | Full journal article |
| **SAFE consortium / NIST AI RMF profile submission** | CRE-vertical profile proposal — the framework as a worked example of a vertical-specific NIST AI RMF profile. | NIST community comment + workshop submission |

## Drafts in flight

### Draft 1 — `FAILURE-MODES.md` matrix-as-contract pattern (ACM SEMS target)

**Working title:** "Doc/Code Parity as a Build-Time Invariant: A Pattern for Audit-Framework Maintainability"

**Status:** Outline drafted. Pulls from the FAILURE-MODES.md matrix shipped in v0.2.1, the companion `tests/test_failure_modes_matrix.py` drift test, and the `tests/test_doc_staleness.py` pattern.

**Submission target:** Q1 2027

**Lead author:** Kunjar Bhaduri

### Draft 2 — Operator-side MI-threshold proxy detection (ACM FAccT target)

**Working title:** "Operator-Side Mutual-Information Proxy Detection for Fair-Housing AI Decision Stacks"

**Status:** Outline pending — depends on v0.2.2 deferred-item completion (the MI-threshold detector in `fair_housing_preflight.py`).

**Submission target:** Q3 2027

**Lead author:** Kunjar Bhaduri

### Draft 3 — Triple-witness pattern for audit-evidence (Journal of Risk & Financial Management target)

**Working title:** "Triple-Witness Audit-Evidence for SOX 404 ITGC: RFC 3161 + Sigstore Rekor + Module-Integrity Proxy"

**Status:** Outline drafted. Pulls from ADR-0012 (persistence/timestamps/witness) and ADR-0013 (MI Proxy) in v0.2.1.

**Submission target:** Q4 2027

**Lead author:** Kunjar Bhaduri

### Draft 4 — NIST AI RMF CRE-vertical profile (SAFE consortium / NIST community)

**Working title:** "A Commercial-Real-Estate Profile for the NIST AI RMF"

**Status:** Outline pending — depends on v0.3.0 state-by-state regulatory mappings.

**Submission target:** Q1 2028

**Lead author:** Kunjar Bhaduri

## Citation discipline

Every publication cites the framework version (with DOI) used as the methodological basis:
- `cre-agent-audit` v0.2.1: DOI [10.5281/zenodo.20434575](https://doi.org/10.5281/zenodo.20434575)
- Future releases will have their own DOIs.

Cross-references to settled matters use verbatim primary-source citations only:
- Case name, court (or agency), docket, ISO-8601 date, dollar amount where on the record
- `U.S. v. RealPage, Inc. et al.` (M.D.N.C., filed August 23, 2024) — **ongoing antitrust litigation**, never described as settled or adjudicated

## How citations help the moat

Each peer-reviewed publication produces:

1. **An academic citation surface** — every future paper citing the work compounds the framework's authority
2. **A defensibility anchor** — Big-4 methods-review and BigLaw Daubert challenges become survivable
3. **A speaking-circuit credential** — peer-reviewed work qualifies for tier-1 conference invitations
4. **An audience expansion signal** — academic readers become inbound for the productized-service portfolio

## Verifiability

When a draft ships, this document updates the status from "outline" → "submitted" → "accepted" → "published" with the venue link. Reviewers and adopters can verify the trajectory at any time.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
```

- [ ] **Step 2: Commit Commit 1 (ADR-0014 + THESIS.md + PUBLICATIONS.md)**

```bash
cd "$HOME/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
git add docs/adr/0014-operator-side-ai-governance-category.md THESIS.md PUBLICATIONS.md
git commit -m "docs(positioning): ADR-0014 operator-side AI governance category claim + THESIS + PUBLICATIONS

ADR-0014 names operator-side AI governance for regulated industries as
the architectural category cre-agent-audit and finserv-agent-audit
inhabit. Three structural commitments distinguish the category from
vendor-side incumbents (RealPage Compliance, Yardi Risk, MRI Compliance):
operator owns the audit ledger; patterns are vendor-agnostic; audit-
evidence is operator-producible.

THESIS.md records the 3-year project commitment (2026-2028) — version
roadmap, publishing cadence, productization commitment, what the
project will NOT become. Five Pillars cornered resource cited
verbatim.

PUBLICATIONS.md names the academic publication track — 4 target
venues (ACM SEMS, ACM FAccT, Journal of Risk & Financial Management,
SAFE consortium / NIST AI RMF profile), 4 draft outlines, citation
discipline.

The three documents together are the moat layer for v0.2.2 — Helmer
Counter-positioning (Power 1) + Branding (Power 5) + Cornered Resource
(Power 6) made explicit on the public surface."
```

---

## Task 8: Three matters — TransUnion, SafeRent, RealPage-as-alleged (Commit 3)

**Files:**
- Create: `examples/regulatory-incidents/README.md`
- Create: `examples/regulatory-incidents/01_transunion_rental_screening/{README.md, replay.py, synthetic_data.json, expected_findings.json}`
- Create: `examples/regulatory-incidents/02_saferent_voucher_screening/{README.md, replay.py, synthetic_data.json, expected_findings.json}`
- Create: `examples/regulatory-incidents/03_realpage_ongoing_litigation/{README.md, replay.py, synthetic_data.json, expected_findings.json}`
- Create: `tests/test_regulatory_incident_matters.py`

This task is long. Steps below cover one matter end-to-end; matters 02 and 03 repeat the same shape with their own content.

- [ ] **Step 1: Write the failing per-matter conformance test**

```python
# tests/test_regulatory_incident_matters.py
"""Per-matter TDD contracts for the three named matters in PR 1.

Each matter declares:
- patterns_engaged (which ADRs should fire)
- expected_findings (the exact Finding[] the replay should produce)

The replay must produce findings matching the declared contract.
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
    spec = importlib.util.spec_from_file_location(
        f"_matter_{matter_dir_name}", replay_py
    )
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
    # Compare by pattern + severity + verdict (loosely; replay may vary on
    # synthetic-data ordering).
    expected_keys = sorted(
        (str(f.pattern), f.severity.value, f.evidence.verdict) for f in expected
    )
    actual_keys = sorted(
        (str(f.pattern), f.severity.value, f.evidence.verdict)
        for f in result.findings_produced
    )
    assert actual_keys == expected_keys, (
        f"{matter_dir_name}: finding (pattern,severity,verdict) "
        f"tuples diverge from expected"
    )


@pytest.mark.parametrize("matter_dir_name", MATTERS)
def test_matter_pattern_coverage_is_full(matter_dir_name: str) -> None:
    matter = _load_matter(matter_dir_name)
    ledger = AuditLedger()
    result = matter.run_replay(ledger=ledger, gates={})
    assert pattern_coverage_score(matter, result) == 1.0


@pytest.mark.parametrize("matter_dir_name", MATTERS)
def test_matter_expected_findings_json_matches_replay(matter_dir_name: str) -> None:
    """The expected_findings.json file matches what the matter declares."""
    matter = _load_matter(matter_dir_name)
    json_path = INCIDENTS_DIR / matter_dir_name / "expected_findings.json"
    declared = json.loads(json_path.read_text(encoding="utf-8"))
    declared_keys = sorted(
        (e["pattern"], e["severity"], e["evidence"]["verdict"])
        for e in declared["findings"]
    )
    method_keys = sorted(
        (str(f.pattern), f.severity.value, f.evidence.verdict)
        for f in matter.expected_findings()
    )
    assert declared_keys == method_keys
```

- [ ] **Step 2: Write `examples/regulatory-incidents/README.md` (gallery)**

```markdown
# Regulatory-Incident Replays

Runnable Python replays of named settled (and one ongoing) matters in commercial real estate AI. Each replay produces an `audit-evidence/<matter>.zip` bundle showing which `cre-agent-audit` patterns would have surfaced the failure modes the public record describes.

These are not legal opinions and they do not adjudicate the underlying matters. Patterns are software; regulatory characterizations are reference mappings; consult counsel.

## Why this directory exists

The three settled-liability anchors of record in CRE-AI share one structural feature: the operator carried the liability when vendor-side audit could not produce the operator-side evidence regulators demanded. This directory replays those failure shapes against the operator-side framework.

Each replay is implemented as an `IncidentReplay` Protocol subclass (per ADR-0014 + `src/cre_agent_audit/regulatory_replay/`). The Protocol carries the matter's primary-source citations, declares which `cre-agent-audit` patterns are expected to fire, and produces a 6-artifact audit-evidence bundle.

## Run them

```bash
# After `pip install -e .` of cre-agent-audit:
cre-replay list                                    # show all matters
cre-replay run 01_transunion_rental_screening      # run one matter
cre-replay run-all                                 # run all matters
cre-replay verify <bundle.zip>                     # re-validate a bundle
```

## The three matters

| # | Matter | Primary source(s) | Patterns expected to fire |
|---|---|---|---|
| **01** | TransUnion Rental Screening Solutions — FTC + CFPB consent orders, October 2023, $15M, FCRA § 607(b) accuracy | FTC C-4810; CFPB 2023-CFPB-0008 | ADR-0003 audit ledger · ADR-0007 lease/screening provenance · ADR-0011 vendor-output adapter |
| **02** | *Louis v. SafeRent Solutions, LLC*, No. 1:22-cv-10800 (D. Mass.) — class settlement, November 20, 2024, ~$2.275M, five-year score-use injunction | D. Mass. docket | ADR-0002 sovereign veto · ADR-0003 audit ledger · ADR-0008 fair-housing pre-flight · ADR-0011 vendor-output adapter |
| **03** | *U.S. v. RealPage, Inc. et al.* (M.D.N.C., filed August 23, 2024 by DOJ + 8 state AGs) — **ongoing antitrust litigation** | M.D.N.C. docket | ADR-0001 DEFCON · ADR-0002 sovereign veto · ADR-0011 vendor-output adapter |

Matter 03 is framed throughout as **alleged conduct**. The replay surfaces coordination *signals*; it does not adjudicate Sherman § 1 exposure. See the per-matter README for the disclaimer pattern.

## Want a deeper engagement?

See [`docs/services/`](../../docs/services/) for the productized service templates ($5K Diagnostic, $40K Audit, $15K/q Retainer, $25K-$50K Workshop, $50K-$200K Cohort, plus private intel + practitioner bench).

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
```

- [ ] **Step 3: Write matter 01 — TransUnion**

Files:
- `01_transunion_rental_screening/README.md` (300-500w narrative)
- `01_transunion_rental_screening/synthetic_data.json` (500 synthetic records)
- `01_transunion_rental_screening/expected_findings.json` (TDD contract)
- `01_transunion_rental_screening/replay.py` (`IncidentReplay` implementation)

**`README.md`**: 400-word narrative covering the FTC/CFPB consent orders, the systemic accuracy failures, what the operator-side audit would have produced, and the disclaimer.

**`synthetic_data.json`**: structure
```json
{
  "matter": "01_transunion_rental_screening",
  "applications": [
    {
      "applicant_id": "A-0001",
      "credit_score": 720,
      "income_x_rent": 3.5,
      "criminal_record_match_confidence": 0.95,
      "screening_report_source_hash": "sha256:abc..."
    },
    ...500 records, ~12 missing source_hash, ~47 score-divergence pairs...
  ]
}
```

**`expected_findings.json`**: structure
```json
{
  "matter_id": "01_transunion_rental_screening",
  "findings": [
    {
      "pattern": "ADR-0003",
      "severity": "High",
      "evidence": {
        "chain_sequence_range": [0, 12],
        "verdict": "chain-of-custody break on 12 entries lacking source-document hash"
      },
      "regulatory_anchor": {
        "case_name": "In re TransUnion Rental Screening Solutions",
        "court": "FTC + CFPB",
        "docket": "C-4810 + 2023-CFPB-0008",
        "date_iso": "2023-10-12",
        "url": null
      },
      "remediation": "Require source-document hash field on every screening-report ingest"
    },
    {
      "pattern": "ADR-0011",
      "severity": "High",
      "evidence": {
        "chain_sequence_range": [13, 59],
        "verdict": "VendorScoreGate flagged 47 entries where same input_hash + same model_version produced divergent scores"
      },
      "regulatory_anchor": {
        "case_name": "In re TransUnion Rental Screening Solutions",
        "court": "FTC + CFPB",
        "docket": "C-4810 + 2023-CFPB-0008",
        "date_iso": "2023-10-12",
        "url": null
      },
      "remediation": "Quarantine the vendor's signal until the score-divergence root cause is identified"
    }
  ]
}
```

**`replay.py`**:
```python
"""TransUnion Rental Screening Solutions consent orders — replay against cre-agent-audit.

Primary sources:
- In re TransUnion Rental Screening Solutions — FTC + CFPB consent orders
- Filed October 2023; $15M civil money penalty
- Failure shape: systemic accuracy failures in rental-screening reports under FCRA § 607(b)

This worked example is not legal advice and does not adjudicate the
underlying matter. Patterns are software; regulatory characterizations
are reference mappings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditLedger,
)
from cre_agent_audit.governance.vendor_score_gate import (
    InMemoryVendorScoreGate,
    VendorScoreDriftDetected,
)
from cre_agent_audit.regulatory_replay import (
    ADRRef,
    Citation,
    Evidence,
    Finding,
    IncidentReplayBase,
    ReplayResult,
    Severity,
)

_THIS_DIR = Path(__file__).resolve().parent

_CIT = Citation(
    case_name="In re TransUnion Rental Screening Solutions",
    court="FTC + CFPB",
    docket="C-4810 + 2023-CFPB-0008",
    date_iso="2023-10-12",
    url=None,
)


class TransUnionRentalScreeningReplay(IncidentReplayBase):
    matter_id = "01_transunion_rental_screening"
    matter_title = (
        "TransUnion Rental Screening Solutions — FTC + CFPB consent orders, "
        "October 2023, $15M, FCRA § 607(b) accuracy"
    )
    primary_sources = (_CIT,)
    failure_shape = (
        "Systemic accuracy failures in rental-screening reports — wrong "
        "addresses, mismatched criminal records, duplicate identities. The "
        "operator could not produce a chain-of-custody for the screening-"
        "report data feeding their tenancy decision, and the vendor's "
        "scoring model produced divergent scores on identical inputs without "
        "operator-visible signal."
    )
    patterns_engaged = (
        ADRRef(number=3, title="Audit Ledger"),
        ADRRef(number=7, title="Lease-Abstraction Provenance"),
        ADRRef(number=11, title="Vendor-Output Adapter"),
    )

    def synthetic_dataset(self) -> Iterable[dict[str, object]]:
        path = _THIS_DIR / "synthetic_data.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data["applications"])

    def run_replay(
        self,
        *,
        ledger: AuditLedger,
        gates: Mapping[str, object],
    ) -> ReplayResult:
        vendor_gate = InMemoryVendorScoreGate(ledger=ledger, raise_on_drift=False)
        chain_of_custody_breaks: list[int] = []
        drift_count = 0

        for record in self.synthetic_dataset():
            assert isinstance(record, dict)
            applicant_id = str(record["applicant_id"])
            credit_score_raw = record["credit_score"]
            assert isinstance(credit_score_raw, (int, float))
            credit_score = float(credit_score_raw)
            source_hash = record.get("screening_report_source_hash")

            ledger.append(
                actor_kind=ActorKind.SYSTEM,
                actor_id="transunion_replay",
                decision_type="screening_decision",
                action_payload=json.dumps(
                    {"applicant_id": applicant_id}, sort_keys=True
                ).encode("utf-8"),
                gate_verdicts={
                    "audit_ledger": "recorded",
                    "source_hash_present": "yes" if source_hash else "no",
                },
            )
            if not source_hash:
                chain_of_custody_breaks.append(ledger.entries[-1].sequence)

            # Vendor scoring emit (with synthetic drift on dup-id pairs)
            entry = vendor_gate.emit(
                vendor_id="vendor-X",
                input_hash=str(record.get("input_hash", f"hash-{applicant_id}")),
                score=min(1.0, max(0.0, credit_score / 1000.0)),
                model_version="v1.0",
            )
            if entry.drift_detected:
                drift_count += 1

        findings = (
            Finding(
                pattern=ADRRef(number=3, title="Audit Ledger"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(
                        min(chain_of_custody_breaks) if chain_of_custody_breaks else 0,
                        max(chain_of_custody_breaks) if chain_of_custody_breaks else 0,
                    ),
                    verdict=(
                        f"chain-of-custody break on {len(chain_of_custody_breaks)} "
                        "entries lacking source-document hash"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Require source-document hash field on every "
                    "screening-report ingest"
                ),
            ),
            Finding(
                pattern=ADRRef(number=11, title="Vendor-Output Adapter"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(0, len(ledger.entries) - 1),
                    verdict=(
                        f"VendorScoreGate flagged {drift_count} entries where "
                        "same input_hash + same model_version produced "
                        "divergent scores"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Quarantine the vendor's signal until the score-divergence "
                    "root cause is identified"
                ),
            ),
        )

        return ReplayResult(
            matter_id=self.matter_id,
            findings_produced=findings,
            chain_entries_written=len(ledger.entries),
        )

    def expected_findings(self) -> tuple[Finding, ...]:
        return (
            Finding(
                pattern=ADRRef(number=3, title="Audit Ledger"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(0, 11),  # 12 entries → range (0, 11)
                    verdict="chain-of-custody break on 12 entries lacking source-document hash",
                ),
                regulatory_anchor=_CIT,
                remediation="Require source-document hash field on every screening-report ingest",
            ),
            Finding(
                pattern=ADRRef(number=11, title="Vendor-Output Adapter"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(0, 499),
                    verdict="VendorScoreGate flagged 47 entries where same input_hash + same model_version produced divergent scores",
                ),
                regulatory_anchor=_CIT,
                remediation="Quarantine the vendor's signal until the score-divergence root cause is identified",
            ),
        )


matter = TransUnionRentalScreeningReplay()
```

Note: The matter's `synthetic_data.json` is engineered so that `chain_of_custody_breaks` count = 12 and `drift_count` = 47, matching `expected_findings()`. The generation script lives outside this plan; the JSON is hand-written for the first cut.

- [ ] **Step 4: Write matters 02 (SafeRent) and 03 (RealPage-as-alleged) following the same template**

Each matter follows the same 4-file structure (README.md, synthetic_data.json, expected_findings.json, replay.py). Patterns engaged differ per the spec § D5; the disclaimer pattern is identical; matter 03's docstrings repeat the ALLEGED framing at every API boundary.

- [ ] **Step 5: Run the per-matter test**

```bash
python3 -m pytest tests/test_regulatory_incident_matters.py -v 2>&1 | tail -25
```

Expected: 15 tests pass (5 tests × 3 matters).

- [ ] **Step 6: Run the framework + per-matter tests + full suite**

```bash
python3 -m pytest -q 2>&1 | tail -3
ruff check src/ tests/ examples/ 2>&1 | tail -3
ruff format --check src/ tests/ scripts/ 2>&1 | tail -3
mypy --strict src/cre_agent_audit/regulatory_replay/ examples/regulatory-incidents/01_transunion_rental_screening/replay.py 2>&1 | tail -5
```

Expected: 13 (framework) + 15 (matters) + 238 (existing) = 266 tests pass; gates clean.

- [ ] **Step 7: Commit Commit 3**

```bash
git add examples/regulatory-incidents/ tests/test_regulatory_incident_matters.py
git commit -m "feat(examples): three named-matter replays — TransUnion, SafeRent, RealPage (alleged)

Adds examples/regulatory-incidents/ with three IncidentReplay
implementations:

01_transunion_rental_screening — TransUnion FTC + CFPB consent orders
(October 2023, \$15M, FCRA § 607(b) accuracy). Patterns engaged:
ADR-0003 audit ledger · ADR-0007 lease/screening provenance · ADR-0011
vendor-output adapter. Replay surfaces 12 chain-of-custody breaks and
47 VendorScoreGate drift flags on a 500-record synthetic dataset.

02_saferent_voucher_screening — Louis v. SafeRent Solutions
(D. Mass., November 2024, ~\$2.275M class settlement, five-year score-
use injunction). Patterns engaged: ADR-0002 sovereign veto · ADR-0003
audit ledger · ADR-0008 fair-housing pre-flight · ADR-0011 vendor-
output adapter. Replay surfaces 89 VETO codes and 12 blanket-exclusion
blocks on a 1,000-applicant synthetic dataset.

03_realpage_ongoing_litigation — U.S. v. RealPage, Inc. et al.
(M.D.N.C., August 23, 2024, DOJ + 8 state AGs, ONGOING antitrust
litigation). Framed as ALLEGED conduct throughout — patterns surface
coordination signals, NOT proof of Sherman § 1 violation. Disclaimer
repeated at module / class / README level.

Per-matter contract: each matter declares expected_findings.json; the
replay produces findings matching the contract (15 tests across 3
matters). Pattern coverage score is 1.0 for each matter.

Gallery README at examples/regulatory-incidents/README.md.

Disclaimer applied uniformly: patterns are software, not legal advice;
regulatory citations are reference mappings; consult counsel for
applicability."
```

---

## Task 9: Seven service templates (Commit 4)

**Files:**
- Create: `docs/services/README.md`
- Create: `docs/services/01-diagnostic-5k.md` through `docs/services/07-practitioner-bench.md`

Each file follows the template from the spec § D6. The full content of each service file goes in the corresponding step below. Given length, the plan embeds the section structure + key sample paragraphs; the engineer fills the body matching the template.

- [ ] **Step 1: Write `docs/services/README.md` (gallery + how-to-engage)**

Content: introduces the productized-service portfolio anchored on the cre-agent-audit framework + Regulatory-Incident Replay. Five public-anchored services + two private-tier services. Pricing rationale: anchored on Path B per the author's business plan. How to engage: one email (`contact@autonomy-ladder.io`). Three-question intake form (firm name, role, pain point). Disclaimer.

- [ ] **Step 2: Write `01-diagnostic-5k.md`** — $5K Diagnostic, 90-min interview + 20-page deliverable, target buyer CRE Tech VP / PE deal team / Big-4 partner. Includes "What's NOT in the public framework" section naming what the engagement adds.

- [ ] **Step 3: Write `02-audit-40k.md`** — $40K Audit, 4 weeks, full audit-evidence bundle on operator's actual stack. Target: top-50 multifamily, Big-4 client engagement.

- [ ] **Step 4: Write `03-retainer-15k-quarterly.md`** — $15K/q recurring, quarterly rerun + new-matter coverage + regulatory-update brief.

- [ ] **Step 5: Write `04-workshop-25k-50k.md`** — $25K-50K Workshop, 1-day on-site or 2-day virtual.

- [ ] **Step 6: Write `05-cohort-50k-200k.md`** — $50K-200K Cohort, 8-week program for 20-40 seats.

- [ ] **Step 7: Write `06-private-intel-subscription.md`** — $25K-100K/yr private intel: gated newsletter + private failure-mode catalog + deposition-shaped playbooks + named-matter risk briefings.

- [ ] **Step 8: Write `07-practitioner-bench.md`** — $10K-50K/yr invite-only community: monthly calls with Kunjar, private Slack/Discord, peer review of new framework patterns before public, first-look at new matters.

- [ ] **Step 9: Commit Commit 4**

```bash
git add docs/services/
git commit -m "docs(services): seven productized-service templates

Seven service files under docs/services/, each following a common
template (price, duration, deliverable, target buyer, what-you-get,
methodology, what's-NOT-in-the-public-framework, what's-not-in-scope,
how-to-engage, pricing, disclaimer):

Public-anchored (5):
- 01-diagnostic-5k.md         \$5K · 90-min + 20-page
- 02-audit-40k.md             \$40K · 4 weeks · audit-evidence bundle
- 03-retainer-15k-quarterly.md \$15K/q · quarterly rerun + brief
- 04-workshop-25k-50k.md      \$25K-50K · 1-day on-site or 2-day virtual
- 05-cohort-50k-200k.md       \$50K-200K · 8-week program · 20-40 seats

Private-tier (2, the moat-strengthening layer):
- 06-private-intel-subscription.md   \$25K-100K/yr · gated content
- 07-practitioner-bench.md           \$10K-50K/yr · invite-only community

Each public-anchor service's 'What's NOT in the public framework'
section names what the paid engagement adds — making the moat visible
on the public surface. The repo becomes the artifact AND the purchase
path."
```

---

## Task 10: Cross-linkage (Commit 5)

**Files:**
- Modify: `README.md`
- Modify: `FAILURE-MODES.md`

- [ ] **Step 1: Add to `README.md` table of contents + body**

After the "Related work + intellectual lineage" line in TOC, add `- [Regulatory incidents](#regulatory-incidents)` and `- [Engage](#engage)` and `- [Thesis + publications](#thesis--publications)`.

Add three new sections to the body:

```markdown
## Regulatory incidents

Three runnable replays of named CRE-AI matters under [`examples/regulatory-incidents/`](examples/regulatory-incidents/):

- **TransUnion Rental Screening Solutions** — FTC + CFPB consent orders, October 2023, $15M, FCRA § 607(b) accuracy
- ***Louis v. SafeRent Solutions, LLC*** — D. Mass. class settlement, November 2024, ~$2.275M
- ***U.S. v. RealPage, Inc. et al.*** — M.D.N.C., DOJ + 8 state AGs, **ongoing antitrust litigation** (framed as alleged conduct)

Each replay produces an audit-evidence bundle (chain export + verify report + MI Proxy attestation + findings + controls description table + narrative). Run them: `cre-replay list`, `cre-replay run <matter_id>`, `cre-replay run-all`.

## Engage

Seven productized-service templates under [`docs/services/`](docs/services/) — five public-anchored ($5K Diagnostic, $40K Audit, $15K/q Retainer, $25K-50K Workshop, $50K-200K Cohort) and two private-tier ($25K-100K/yr private intel subscription, $10K-50K/yr practitioner bench). Each template names what the paid engagement adds beyond the public framework. Email `contact@autonomy-ladder.io`.

## Thesis + publications

- [`THESIS.md`](THESIS.md) — three-year project commitment (2026-2028)
- [`PUBLICATIONS.md`](PUBLICATIONS.md) — academic publication track (ACM SEMS, ACM FAccT, Journal of Risk & Financial Management, SAFE consortium / NIST AI RMF profile)
- [ADR-0014](docs/adr/0014-operator-side-ai-governance-category.md) — operator-side AI governance category claim
```

- [ ] **Step 2: Add cross-links to `FAILURE-MODES.md` Rows 7 and 8**

Row 7 (Verifier compromise) — append: "**Motivating example:** [`examples/regulatory-incidents/03_realpage_ongoing_litigation/`](examples/regulatory-incidents/03_realpage_ongoing_litigation/) (framed as alleged conduct)."

Row 8 (Vendor AI scoring drift) — append: "**Motivating examples:** [`examples/regulatory-incidents/01_transunion_rental_screening/`](examples/regulatory-incidents/01_transunion_rental_screening/), [`examples/regulatory-incidents/02_saferent_voucher_screening/`](examples/regulatory-incidents/02_saferent_voucher_screening/)."

- [ ] **Step 3: Run staleness test to confirm new cross-links don't drift**

```bash
python3 -m pytest tests/test_doc_staleness.py tests/test_failure_modes_matrix.py -v 2>&1 | tail -15
```

Expected: 9 tests pass.

- [ ] **Step 4: Commit Commit 5**

```bash
git add README.md FAILURE-MODES.md
git commit -m "docs(cross-link): wire regulatory-incidents + services + thesis into README + FAILURE-MODES

README.md gets three new sections:
- Regulatory incidents — links to examples/regulatory-incidents/ with the
  three named-matter cards
- Engage — links to docs/services/ with the 7 productized-service shapes
- Thesis + publications — links to THESIS.md, PUBLICATIONS.md, ADR-0014

FAILURE-MODES.md Row 7 (Verifier compromise) gets a 'Motivating example'
cross-link to examples/regulatory-incidents/03_realpage_ongoing_litigation/.

FAILURE-MODES.md Row 8 (Vendor AI scoring drift) gets 'Motivating examples'
cross-links to 01_transunion_rental_screening/ and 02_saferent_voucher_
screening/.

The loop is closed: cold visitor reads README → sees regulatory-incidents
gallery → runs one matter → sees audit-evidence bundle → reads docs/services/
01-diagnostic-5k.md → emails. Six clicks to conversion."
```

---

## Task 11: Test infrastructure — doc-staleness extension + service-template lint (Commit 6)

**Files:**
- Modify: `tests/test_doc_staleness.py`
- Create: `tests/test_service_templates.py`

- [ ] **Step 1: Extend `PUBLIC_DOC_PATHS` in `test_doc_staleness.py`**

```python
# Modify the list:
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
```

- [ ] **Step 2: Write `tests/test_service_templates.py`**

```python
"""Service-template section lint.

Every `docs/services/NN-*.md` carries the canonical 10-section structure.
Drift between templates fails the build.
"""

from __future__ import annotations

import pathlib
import re

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
```

- [ ] **Step 3: Run all tests + gates**

```bash
python3 -m pytest -q 2>&1 | tail -3
ruff check tests/ 2>&1 | tail -3
ruff format --check src/ tests/ scripts/ 2>&1 | tail -3
```

Expected: all green; new service-template tests pass (7+ files × 4 tests per file = 28+ new tests).

- [ ] **Step 4: Commit Commit 6**

```bash
git add tests/test_doc_staleness.py tests/test_service_templates.py
git commit -m "test(docs): extend doc-staleness scope + service-template section lint

tests/test_doc_staleness.py: PUBLIC_DOC_PATHS extended to include THESIS.md,
PUBLICATIONS.md, docs/services/*.md, examples/regulatory-incidents/README.md.
Drift detection now covers the new moat-layer surfaces.

tests/test_service_templates.py: regex check that every docs/services/*.md
carries the canonical 10-section structure (What you get, Methodology,
What's NOT in the public framework, What's NOT in scope, How to engage,
Pricing, Disclaimer). H1 must name a price; disclaimer line must be
present.

Both tests run in CI. New section regressions fail the build."
```

---

## Task 12: Private memory entry (Commit 7)

**Files:**
- Create: `~/.claude/projects/-Users-kunjarbhaduri-Documents-110---Kunjar-s-Resume-Repos-cre-agent-audit/memory/feedback_engagement_capture_discipline.md`
- Modify: `~/.claude/projects/-Users-kunjarbhaduri-Documents-110---Kunjar-s-Resume-Repos-cre-agent-audit/memory/MEMORY.md`

- [ ] **Step 1: Write `feedback_engagement_capture_discipline.md`**

```markdown
---
name: feedback-engagement-capture-discipline
description: For every paid engagement (Diagnostic / Audit / Retainer / Workshop / Cohort), capture confidential client memo + de-identified risk pattern + lessons-learned + referral pathway. The corpus IS the moat (Maister PSF + Helmer Process Power).
metadata:
  type: feedback
---

When Kunjar takes a paid engagement under any of the productized services (`docs/services/01..07-*.md`), apply this capture discipline at engagement close:

1. **Confidential client memo (private; never published).** Captures: client identity, scope, what was found, recommendations, residual risk, engagement-letter terms. Filed in a private location under `~/Documents/110 - Kunjar's Resume/Confidential-Engagements/<YYYY-QN>-<client-slug>/`.

2. **De-identified risk pattern (private corpus).** The pattern itself — generalized away from client identity — added to a private corpus the framework's future development consults. Format: `<RiskPattern-NNN>-<short-name>.md` with the failure shape, the patterns that fired, the patterns that would have but didn't, what was missing in the framework.

3. **Lessons learned that inform framework v.next (could-become-public).** A list of what cre-agent-audit needed to do better — new failure-modes-matrix rows, missing ADR, missing pattern. These feed the public roadmap on a delayed cadence (6-12 months).

4. **Referral pathway captured before engagement ends.** Before the final invoice clears: who in the client's network would also benefit? Permission to introduce? Warm-intro shape vs cold? Recorded in the same engagement folder.

**Why:** The private case-history library IS the moat. Maister's PSF + Helmer Power 7 (Process Power) both rest on it. After 50 engagements, "we have 47 prior matters on this exact surface" becomes the unmatchable claim — no consultant with the same framework can match it without the corpus.

**Never publish the corpus.** The framework is open; the corpus is the moat. Conflating the two destroys the moat.

**How to apply:** When Kunjar closes any paid engagement, walk through the four captures. If any is skipped — note why in the engagement folder. A skipped capture is a moat leak.

**Related:** [[feedback-sot-propagation-discipline]] for the public-surface discipline.
```

- [ ] **Step 2: Update `MEMORY.md` index**

Append:

```markdown
- [Engagement-capture discipline (4-step PSF/Maister + Helmer Power 7)](feedback_engagement_capture_discipline.md) — applied at the close of every paid engagement
```

- [ ] **Step 3: No commit needed** (memory is local, outside the repo).

---

## Task 13: Push + CI verification

- [ ] **Step 1: Final gates pass**

```bash
cd "$HOME/Documents/110 - Kunjar's Resume/Repos/cre-agent-audit"
python3 -m pytest -q 2>&1 | tail -3
ruff check src/ tests/ 2>&1 | tail -3
ruff format --check src/ tests/ scripts/ 2>&1 | tail -3
mypy --strict src/cre_agent_audit/ 2>&1 | tail -3
```

Expected: all green. Total test count ≥ 266 + service-template tests.

- [ ] **Step 2: Push**

```bash
git push origin main
```

- [ ] **Step 3: Wait for CI**

```bash
NEW_SHA=$(git rev-parse HEAD)
until gh run list --branch main --limit 1 --json status,headSha -q ".[0] | select(.headSha==\"$NEW_SHA\") | .status" 2>/dev/null | grep -q completed; do
  sleep 5
done
gh run list --branch main --limit 1 --json status,conclusion,headSha 2>&1 | head -2
```

Expected: `"conclusion":"success"`. If red, surface the failure and fix on `main`.

---

## Task 14: Per-artifact council pass (the 10/10 gate)

After the commit-and-push is green, run the council pass against each of the 7 commits' artifacts. Score against the 15-mentor slate from the spec.

- [ ] **Step 1: For each artifact, score 1-10 against each mentor's bar**

| Artifact | Helmer | Buffett | Thiel | Andreessen | Gurley | Christensen | Maister | Weiss | Naval | López | Welsh | Clark | Gil | Majors | Balfour |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ADR-0014 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| THESIS.md |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| PUBLICATIONS.md |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| regulatory_replay framework |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Matter 01 (TransUnion) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Matter 02 (SafeRent) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Matter 03 (RealPage-alleged) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Services README |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Service 01 (Diagnostic) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Service 02 (Audit) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Service 03 (Retainer) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Service 04 (Workshop) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Service 05 (Cohort) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Service 06 (Private intel) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Service 07 (Practitioner bench) |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

- [ ] **Step 2: For any cell < 10, list the gap + the specific revision**

- [ ] **Step 3: Apply revisions; re-score**

Cap: 3 revision passes per artifact. If any artifact fails to reach 10/10 after 3 passes, surface the blocker in a `docs/handoffs/2026-05-28-replay-and-services-council-residual-gaps.md` file and stop.

- [ ] **Step 4: Commit any revision passes as their own commit(s)**

Each revision commit names the artifact, the mentor's gap, and the revision applied.

- [ ] **Step 5: Push revisions; wait for CI**

---

## Task 15: Hand-off receipt

- [ ] **Step 1: Write a hand-off receipt to `docs/handoffs/2026-05-28-replay-and-services-hand-off.md`**

Names: branch, commit range, version marker (`0.2.2.dev0`), CI status, council scores per artifact, what is and isn't in scope (no tag, no publish, no DOI).

- [ ] **Step 2: Commit and push the hand-off receipt**

---

## Self-review

After writing the complete plan, checked against the spec:

**1. Spec coverage:**
- D1 (ADR-0014) → Task 5
- D2 (THESIS.md) → Task 6
- D3 (PUBLICATIONS.md) → Task 7
- D4 (regulatory_replay framework) → Tasks 1, 2, 3, 4
- D5 (three matters) → Task 8
- D6 (seven service templates) → Task 9
- D7 (tests) → Tasks 1-4 (framework tests) + Task 8 (matter tests) + Task 11 (service + staleness tests)
- D8 (cross-linkage) → Task 10
- D9 (private memory entry) → Task 12
- Plus: Task 13 (push + CI), Task 14 (council pass), Task 15 (hand-off)

Every spec deliverable mapped. No gaps.

**2. Placeholder scan:** Task 8 step 4 says "Write matters 02 and 03 following the same template" — that is acceptable per the writing-plans skill discipline only because the template is fully shown in step 3 for matter 01 (the engineer can copy + adapt). The content discipline (matter-specific narratives, patterns_engaged, expected_findings) is detailed in the spec § D5. No "TODO" or "TBD" anywhere.

**3. Type consistency:** Names match across tasks. `IncidentReplay` Protocol surface declared in Task 2 is consumed identically in Task 8. `EvidenceBundle.assemble()` signature in Task 3 is called from `cli._cmd_run` in Task 4 with the same kwargs. `Finding` / `Citation` / `ADRRef` / `Severity` / `Evidence` used consistently across the framework + matters + tests.

**4. Ambiguity check:** Matter 03's "framed as ALLEGED" requirement is restated at every API boundary (module docstring + class docstring + README + replay narrative). The disclaimer line is the same exact string repo-wide. The 7th commit (memory) is local-only and explicitly noted as not requiring a repo commit.

No issues to fix inline.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-28-regulatory-incident-replay-and-services.md`. Per the executing-plans skill already active in this session, this plan is executed inline with checkpoints at each of the 7 internal commits + the Task 14 council pass as the quality gate.

Two execution options exist per the writing-plans skill:

1. **Subagent-Driven** — Dispatch a fresh subagent per task, review between tasks. Faster wall-clock through parallelism. Risk: per-task context loss; the moat layer requires cross-task coherence (ADR-0014 voice has to match THESIS.md voice has to match service-template voice).

2. **Inline Execution** — Execute tasks in this session using executing-plans, with checkpoints at each commit + the council pass.

**Inline execution is recommended for this work** — the council-pass quality gate requires single-session voice coherence that subagent dispatch cannot guarantee.
