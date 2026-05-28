"""TransUnion Rental Screening Solutions consent orders — replay.

Primary sources:
- In re Trans Union Rental Screening Solutions
- FTC + CFPB joint consent orders, October 2023
- $15M civil money penalty
- Failure shape: systemic accuracy failures in rental-screening reports
  under FCRA § 607(b)

This worked example is not legal advice and does not adjudicate the
underlying matter. Patterns are software; regulatory characterizations
are reference mappings; consult counsel for applicability to your
control environment.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping

from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditLedger,
)
from cre_agent_audit.governance.vendor_score_gate import (
    InMemoryVendorScoreGate,
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

_CIT = Citation(
    case_name="In re Trans Union Rental Screening Solutions",
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
        "addresses, mismatched criminal records, duplicate identities. "
        "The operator could not produce a chain-of-custody for the "
        "screening-report data feeding their tenancy decision, and the "
        "vendor's scoring model produced divergent scores on identical "
        "inputs without operator-visible signal."
    )
    patterns_engaged = (
        ADRRef(number=3, title="Audit Ledger"),
        ADRRef(number=11, title="Vendor-Output Adapter"),
    )

    # Engineering constants matching expected_findings.json
    _TOTAL_RECORDS = 500
    _CHAIN_OF_CUSTODY_BREAK_COUNT = 12
    _SCORE_DRIFT_PAIR_COUNT = 47

    def synthetic_dataset(self) -> Iterable[dict[str, object]]:
        """Deterministically synthesize the 500-record dataset.

        Records 0..11 (12 total) lack source_document_hash → chain-of-custody breaks.
        Records 12..58 (47 total) are paired with records that share their
        input_hash but produce a divergent vendor score under the same
        model_version → 47 drift signals.
        """
        records: list[dict[str, object]] = []

        # First 12: missing source_document_hash
        for i in range(self._CHAIN_OF_CUSTODY_BREAK_COUNT):
            records.append(
                {
                    "applicant_id": f"A-{i:04d}",
                    "input_hash": f"hash-base-{i:04d}",
                    "vendor_score": 0.50 + (i * 0.01),
                    "model_version": "v3.1.0",
                    "source_document_hash": None,
                }
            )

        # Next 47 pairs: same input_hash + same model_version + divergent score
        for i in range(self._SCORE_DRIFT_PAIR_COUNT):
            shared_hash = f"shared-hash-{i:04d}"
            base_idx = self._CHAIN_OF_CUSTODY_BREAK_COUNT + (i * 2)
            records.append(
                {
                    "applicant_id": f"A-{base_idx:04d}",
                    "input_hash": shared_hash,
                    "vendor_score": 0.50,
                    "model_version": "v3.1.0",
                    "source_document_hash": f"sha256:doc-{base_idx:04d}",
                }
            )
            records.append(
                {
                    "applicant_id": f"A-{base_idx + 1:04d}",
                    "input_hash": shared_hash,
                    "vendor_score": 0.65,  # divergent under same model_version
                    "model_version": "v3.1.0",
                    "source_document_hash": f"sha256:doc-{base_idx + 1:04d}",
                }
            )

        # Fill the remainder with clean records
        next_idx = len(records)
        while len(records) < self._TOTAL_RECORDS:
            records.append(
                {
                    "applicant_id": f"A-{next_idx:04d}",
                    "input_hash": f"clean-hash-{next_idx:04d}",
                    "vendor_score": 0.70,
                    "model_version": "v3.1.0",
                    "source_document_hash": f"sha256:doc-{next_idx:04d}",
                }
            )
            next_idx += 1

        return records

    def run_replay(
        self,
        *,
        ledger: AuditLedger,
        gates: Mapping[str, object],
    ) -> ReplayResult:
        vendor_gate = InMemoryVendorScoreGate(ledger=ledger, raise_on_drift=False)
        chain_of_custody_break_indices: list[int] = []
        drift_count = 0

        for record in self.synthetic_dataset():
            applicant_id = str(record["applicant_id"])
            source_hash = record.get("source_document_hash")

            entry = ledger.append(
                actor_kind=ActorKind.SYSTEM,
                actor_id="transunion_replay",
                decision_type="screening_decision",
                action_payload=json.dumps({"applicant_id": applicant_id}, sort_keys=True).encode(
                    "utf-8"
                ),
                gate_verdicts={
                    "audit_ledger": "recorded",
                    "source_hash_present": "yes" if source_hash else "no",
                },
            )
            if not source_hash:
                chain_of_custody_break_indices.append(entry.sequence)

            score_raw = record["vendor_score"]
            assert isinstance(score_raw, (int, float))
            vendor_entry = vendor_gate.emit(
                vendor_id="transunion-rental",
                input_hash=str(record["input_hash"]),
                score=float(score_raw),
                model_version=str(record["model_version"]),
            )
            if vendor_entry.drift_detected:
                drift_count += 1

        first_break = chain_of_custody_break_indices[0] if chain_of_custody_break_indices else 0
        last_break = chain_of_custody_break_indices[-1] if chain_of_custody_break_indices else 0

        findings = (
            Finding(
                pattern=ADRRef(number=3, title="Audit Ledger"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(first_break, last_break),
                    verdict=(
                        f"chain-of-custody break on "
                        f"{len(chain_of_custody_break_indices)} entries "
                        "lacking source-document hash"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=("Require source-document hash field on every screening-report ingest"),
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
                    "Quarantine the vendor's signal until the score-"
                    "divergence root cause is identified"
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
                    chain_sequence_range=(0, 22),
                    verdict=("chain-of-custody break on 12 entries lacking source-document hash"),
                ),
                regulatory_anchor=_CIT,
                remediation=("Require source-document hash field on every screening-report ingest"),
            ),
            Finding(
                pattern=ADRRef(number=11, title="Vendor-Output Adapter"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(0, 999),
                    verdict=(
                        "VendorScoreGate flagged 47 entries where same "
                        "input_hash + same model_version produced divergent "
                        "scores"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Quarantine the vendor's signal until the score-"
                    "divergence root cause is identified"
                ),
            ),
        )


matter = TransUnionRentalScreeningReplay()
