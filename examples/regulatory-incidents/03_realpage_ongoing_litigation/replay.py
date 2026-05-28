"""U.S. v. RealPage, Inc. et al. — replay (ALLEGED conduct, ongoing litigation).

IMPORTANT: This matter is ongoing antitrust litigation. The allegations
in the underlying complaint are NOT adjudicated. This replay surfaces
operator-side coordination signals; it does not assert that the
underlying conduct violates Sherman § 1.

Primary source:
- U.S. v. RealPage, Inc. et al., Civil Action No. (M.D.N.C.)
- Filed August 23, 2024 by the U.S. Department of Justice + 8 state AGs
- ONGOING antitrust litigation — NOT settled, NOT adjudicated

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
    case_name="U.S. v. RealPage, Inc. et al.",
    court="M.D.N.C. (DOJ + 8 state AGs)",
    docket="Civil Action (filed Aug 23, 2024) — ongoing",
    date_iso="2024-08-23",
    url=None,
)


class RealPageOngoingLitigationReplay(IncidentReplayBase):
    """ALLEGED CONDUCT — ongoing antitrust litigation, not adjudicated."""

    matter_id = "03_realpage_ongoing_litigation"
    matter_title = (
        "U.S. v. RealPage, Inc. et al. — M.D.N.C., filed August 23, 2024 "
        "(DOJ + 8 state AGs) — ONGOING antitrust litigation (alleged conduct)"
    )
    primary_sources = (_CIT,)
    failure_shape = (
        "ALLEGED (not adjudicated): multifamily revenue-management vendor "
        "software allegedly enabled operators to share competitively "
        "sensitive data and act on a common algorithmic price "
        "recommendation. Operators allegedly experienced pricing patterns "
        "that converged with peer operators using the same software. "
        "The complaint alleges this constituted unlawful information-"
        "sharing under Sherman § 1; defendants deny the allegations; the "
        "matter has not been adjudicated. This replay surfaces operator-"
        "side coordination signals only — NOT proof of antitrust violation."
    )
    patterns_engaged = (
        ADRRef(number=1, title="DEFCON State Machine"),
        ADRRef(number=11, title="Vendor-Output Adapter"),
    )

    _TOTAL_DECISIONS = 50

    def synthetic_dataset(self) -> Iterable[dict[str, object]]:
        """Synthesize 50 vendor-pricing-recommendation decisions.

        Each decision accepts the vendor's recommendation unmodified.
        Cohort statistical clustering is engineered into the score
        distribution. No real prices, no real operators, no real data.
        """
        records: list[dict[str, object]] = []
        for i in range(self._TOTAL_DECISIONS):
            records.append(
                {
                    "decision_id": f"D-{i:04d}",
                    "vendor_recommendation_accepted_unmodified": True,
                    # Cohort-clustered score (synthetic; not real pricing data)
                    "vendor_score": 0.75 + (i % 5) * 0.01,
                    "model_version": "v-alleged-clustering-mark",
                }
            )
        return records

    def run_replay(
        self,
        *,
        ledger: AuditLedger,
        gates: Mapping[str, object],
    ) -> ReplayResult:
        vendor_gate = InMemoryVendorScoreGate(ledger=ledger, raise_on_drift=False)
        defcon_review_indices: list[int] = []

        for record in self.synthetic_dataset():
            decision_id = str(record["decision_id"])
            unmodified = bool(record["vendor_recommendation_accepted_unmodified"])

            entry = ledger.append(
                actor_kind=ActorKind.SYSTEM,
                actor_id="realpage_replay_alleged",
                decision_type="vendor_recommendation_accepted",
                action_payload=json.dumps({"decision_id": decision_id}, sort_keys=True).encode(
                    "utf-8"
                ),
                gate_verdicts={
                    "defcon": "OPERATOR_REVIEW" if unmodified else "OPERATOR_INDEPENDENT",
                },
            )
            if unmodified:
                defcon_review_indices.append(entry.sequence)

            score_raw = record["vendor_score"]
            assert isinstance(score_raw, (int, float))
            vendor_gate.emit(
                vendor_id="vendor-pricing-alleged",
                input_hash=f"shared-cohort-input-{record['decision_id']}",
                score=float(score_raw),
                model_version=str(record["model_version"]),
            )

        first_review = defcon_review_indices[0] if defcon_review_indices else 0
        last_review = defcon_review_indices[-1] if defcon_review_indices else 0

        findings = (
            Finding(
                pattern=ADRRef(number=1, title="DEFCON State Machine"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(first_review, last_review),
                    verdict=(
                        f"DEFCON surfaced {len(defcon_review_indices)} "
                        "decisions accepting vendor recommendation "
                        "unmodified (operator-review signal; not proof of "
                        "antitrust violation)"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Operator-side independent-judgment workflow: document "
                    "the operator's deliberate independent decision for each "
                    "vendor recommendation accepted unmodified. Consult "
                    "antitrust counsel re: Sherman § 1 exposure."
                ),
            ),
            Finding(
                pattern=ADRRef(number=11, title="Vendor-Output Adapter"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(0, len(ledger.entries) - 1),
                    verdict=(
                        "VendorScoreGate recorded 50 cohort-statistical "
                        "clustering entries (operator-side documentation "
                        "signal; not proof of antitrust violation)"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Operator-side cohort-drift dashboard for the vendor's "
                    "outputs across the operator's portfolio. Consult "
                    "antitrust counsel re: information-sharing exposure."
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
                pattern=ADRRef(number=1, title="DEFCON State Machine"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(0, 98),
                    verdict=(
                        "DEFCON surfaced 50 decisions accepting vendor "
                        "recommendation unmodified (operator-review "
                        "signal; not proof of antitrust violation)"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Operator-side independent-judgment workflow: document "
                    "the operator's deliberate independent decision for each "
                    "vendor recommendation accepted unmodified. Consult "
                    "antitrust counsel re: Sherman § 1 exposure."
                ),
            ),
            Finding(
                pattern=ADRRef(number=11, title="Vendor-Output Adapter"),
                severity=Severity.HIGH,
                evidence=Evidence(
                    chain_sequence_range=(0, 99),
                    verdict=(
                        "VendorScoreGate recorded 50 cohort-statistical "
                        "clustering entries (operator-side documentation "
                        "signal; not proof of antitrust violation)"
                    ),
                ),
                regulatory_anchor=_CIT,
                remediation=(
                    "Operator-side cohort-drift dashboard for the vendor's "
                    "outputs across the operator's portfolio. Consult "
                    "antitrust counsel re: information-sharing exposure."
                ),
            ),
        )


matter = RealPageOngoingLitigationReplay()
