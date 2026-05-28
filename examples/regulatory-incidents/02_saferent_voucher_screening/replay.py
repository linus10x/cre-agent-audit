"""Louis v. SafeRent Solutions, LLC — replay.

Primary sources:
- Louis v. SafeRent Solutions, LLC, No. 1:22-cv-10800 (D. Mass.)
- Class settlement approved November 20, 2024
- Approximately $2.275M class settlement + five-year score-use injunction
  on voucher-holder applicants

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
    case_name="Louis v. SafeRent Solutions, LLC",
    court="D. Mass.",
    docket="No. 1:22-cv-10800",
    date_iso="2024-11-20",
    url=None,
)


class SafeRentVoucherScreeningReplay(IncidentReplayBase):
    matter_id = "02_saferent_voucher_screening"
    matter_title = (
        "Louis v. SafeRent Solutions, LLC — D. Mass. class settlement, "
        "November 20, 2024, ~$2.275M, five-year score-use injunction"
    )
    primary_sources = (_CIT,)
    failure_shape = (
        "A vendor tenant-screening AI scored voucher-holder applicants "
        "below a tenancy threshold without documenting why. The threshold "
        "was undisclosed; the override path was undocumented; the operator "
        "could not justify the cohort-level disparate outcome when "
        "challenged. The five-year score-use injunction effectively bars "
        "the operator from using the vendor's score for voucher-holder "
        "applicants for five years."
    )
    patterns_engaged = (
        ADRRef(number=2, title="Sovereign Veto"),
        ADRRef(number=8, title="Fair-Housing Pre-Flight Gate"),
    )

    _TOTAL_APPLICANTS = 1000
    _VOUCHER_PROXY_COUNT = 89
    _BLANKET_CRIM_EXCLUSION_COUNT = 12

    def synthetic_dataset(self) -> Iterable[dict[str, object]]:
        records: list[dict[str, object]] = []

        # First 89: voucher-status proxy features
        for i in range(self._VOUCHER_PROXY_COUNT):
            records.append(
                {
                    "applicant_id": f"A-{i:04d}",
                    "has_voucher_proxy_feature": True,
                    "blanket_criminal_exclusion_attempted": False,
                }
            )

        # Next 12: blanket-criminal-history exclusion attempts
        for i in range(self._BLANKET_CRIM_EXCLUSION_COUNT):
            idx = self._VOUCHER_PROXY_COUNT + i
            records.append(
                {
                    "applicant_id": f"A-{idx:04d}",
                    "has_voucher_proxy_feature": False,
                    "blanket_criminal_exclusion_attempted": True,
                }
            )

        # Fill the remainder with clean records
        next_idx = len(records)
        while len(records) < self._TOTAL_APPLICANTS:
            records.append(
                {
                    "applicant_id": f"A-{next_idx:04d}",
                    "has_voucher_proxy_feature": False,
                    "blanket_criminal_exclusion_attempted": False,
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
        voucher_proxy_indices: list[int] = []
        blanket_exclusion_indices: list[int] = []

        for record in self.synthetic_dataset():
            applicant_id = str(record["applicant_id"])
            voucher_proxy = bool(record["has_voucher_proxy_feature"])
            blanket = bool(record["blanket_criminal_exclusion_attempted"])

            gate_verdicts = {"fair_housing_preflight": "allow"}
            if voucher_proxy:
                gate_verdicts["fair_housing_preflight"] = "FHA-VOUCHER"
            if blanket:
                gate_verdicts["sovereign_veto"] = "FHA-CRIM-BLANKET"

            entry = ledger.append(
                actor_kind=ActorKind.SYSTEM,
                actor_id="saferent_replay",
                decision_type="screening_decision",
                action_payload=json.dumps({"applicant_id": applicant_id}, sort_keys=True).encode(
                    "utf-8"
                ),
                gate_verdicts=gate_verdicts,
            )

            if voucher_proxy:
                voucher_proxy_indices.append(entry.sequence)
            if blanket:
                blanket_exclusion_indices.append(entry.sequence)

        first_voucher = voucher_proxy_indices[0] if voucher_proxy_indices else 0
        last_voucher = voucher_proxy_indices[-1] if voucher_proxy_indices else 0
        first_blanket = blanket_exclusion_indices[0] if blanket_exclusion_indices else 0
        last_blanket = blanket_exclusion_indices[-1] if blanket_exclusion_indices else 0

        findings = (
            Finding(
                pattern=ADRRef(number=8, title="Fair-Housing Pre-Flight Gate"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(first_voucher, last_voucher),
                    verdict=(
                        f"FairHousingPreflightGate flagged "
                        f"{len(voucher_proxy_indices)} entries with "
                        "voucher-status proxy features (FHA-VOUCHER)"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Block voucher-proxy decisions at preflight; require "
                    "documented override per HUD source-of-income guidance"
                ),
            ),
            Finding(
                pattern=ADRRef(number=2, title="Sovereign Veto"),
                severity=Severity.CRITICAL,
                evidence=Evidence(
                    chain_sequence_range=(first_blanket, last_blanket),
                    verdict=(
                        f"SovereignVeto blocked {len(blanket_exclusion_indices)} "
                        "blanket criminal-history exclusion attempts "
                        "(FHA-CRIM-BLANKET; HUD April 2016 guidance)"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Replace blanket criminal-history exclusion with the "
                    "HUD-aligned individualized-assessment workflow"
                ),
            ),
        )

        return ReplayResult(
            matter_id=self.matter_id,
            findings_produced=findings,
            chain_entries_written=len(ledger.entries),
        )

    def expected_findings(self) -> tuple[Finding, ...]:
        # First 89 records are voucher proxies (indices 0..88).
        # Next 12 (indices 89..100) are blanket-exclusion attempts.
        return (
            Finding(
                pattern=ADRRef(number=8, title="Fair-Housing Pre-Flight Gate"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(0, 88),
                    verdict=(
                        "FairHousingPreflightGate flagged 89 entries with "
                        "voucher-status proxy features (FHA-VOUCHER)"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Block voucher-proxy decisions at preflight; require "
                    "documented override per HUD source-of-income guidance"
                ),
            ),
            Finding(
                pattern=ADRRef(number=2, title="Sovereign Veto"),
                severity=Severity.CRITICAL,
                evidence=Evidence(
                    chain_sequence_range=(89, 100),
                    verdict=(
                        "SovereignVeto blocked 12 blanket criminal-history "
                        "exclusion attempts (FHA-CRIM-BLANKET; HUD April "
                        "2016 guidance)"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Replace blanket criminal-history exclusion with the "
                    "HUD-aligned individualized-assessment workflow"
                ),
            ),
        )


matter = SafeRentVoucherScreeningReplay()
