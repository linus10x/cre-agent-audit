# ADR-0010 · Audit-Chain Retention, Privilege & Discovery Posture

**Status:** Accepted · v0.2.0 · layered policy ADR (no separate runtime primitive)
**Date:** 2026-05-27
**Decider:** Kunjar Bhaduri

> **⚠ Reference pattern, not legal advice.** Regulatory characterizations are summaries; readers must consult qualified counsel licensed in the relevant jurisdictions. No attorney-client relationship is formed by use of this ADR. See repo-root [`DISCLAIMER.md`](../../DISCLAIMER.md).

## Context

The patterns in this repository generate evidentiary artifacts by design — the hash-chained Audit Ledger (ADR-0003), the Fair-Housing exception log (ADR-0008 `FairHousingException`), the Tenant-PII cross-jurisdiction request log (ADR-0009 `CrossJurisdictionRequest`), the lease-clause provenance object (ADR-0007 `Provenance`), and the Sovereign Veto bypass-justification fields (ADR-0002).

These artifacts are **discoverable in litigation**. A SafeRent-pattern plaintiff propounds RFP #1: "Produce all `FairHousingException` records with `FHA-DISPARATE` reason codes from 2026 to present, including each entry's `bypass_owner`, `bypass_justification`, and `audit_chain_sigil`." The exception log produces the answer — and the answer can prove disparate impact was *known* and *bypassed*, with a named human owner. That is potentially worse for the operator than not having the log, depending on the underlying facts and the framing of the bypass justifications.

The patterns alone do not address this. They produce the artifacts; the operator owns the **retention schedule, the privilege envelope, the work-product framing, and the litigation-hold integration**. This ADR documents the policy layer the adopter must put on top of the engineering primitives.

## Decision

Adopters of Patterns 2, 3, 7, 8, 9 must layer four policy artifacts on top of the engineering primitives:

### 1. Retention schedule synchronized to statutes of limitations

The audit chain retains decision records for the longer of:

- **Fair Housing Act** — 2-year administrative SOL · 2-year private right of action (42 U.S.C. § 3613(a)(1)(A))
- **Equal Credit Opportunity Act** — 5-year retention (Regulation B, 12 C.F.R. § 1002.12)
- **FCRA** — 2-year statute of limitations from discovery, 5-year repose (15 U.S.C. § 1681p)
- **SEC 17a-4** — 6 years for broker-dealer records (where applicable to institutional-investor-owned CRE)
- **State-specific statutes** — varies; consult counsel for the operator's jurisdictions
- **Any litigation hold** — overrides retention-based deletion

After the retention window expires (and absent a litigation hold), the operator's deletion process runs. Deletion is itself an audit-chain entry — the deletion record stays in the chain after the deleted entries are tombstoned. Forensic-grade deletion (cryptographic shredding) is recommended for production deployments.

### 2. Attorney-client privilege routing on bypass-justification fields

The `bypass_justification` field on `SovereignVeto` events and the analogous field on `FairHousingException` records can contain attorney-client-privileged content if the bypass decision was made on counsel advice. Adopters route those entries through General Counsel review before commit and tag them in the chain metadata:

```python
# Conceptual extension — implement in the deployer's stack, not in cre-agent-audit
@dataclass(frozen=True)
class PrivilegedAuditEntry(AuditEntry):
    privilege_basis: str | None = None       # "attorney-client" | "work-product" | None
    counsel_id: str | None = None            # named outside or inside counsel
    privilege_log_entry_id: str | None = None
```

The privilege tag supports a privilege-log objection at discovery. The justification text itself stays in the encrypted ledger; the privilege metadata stays in the chain. See *Upjohn Co. v. United States*, 449 U.S. 383 (1981) for the corporate attorney-client privilege scope.

### 3. Work-product framing for disparate-impact monitor outputs

The disparate-impact monitor on ADR-0008's Fair-Housing Pre-Flight Gate produces statistical output (selection rates by cohort, four-fifths-rule ratios). If the monitor was **deployed at counsel direction in anticipation of litigation**, its output may qualify for work-product protection under FRCP 26(b)(3). The trigger is documented in the deployment record: which counsel directed the deployment, when, and against what anticipated litigation.

The work-product framing is **not automatic** — it depends on the facts of the deployment. The default position is that the output is discoverable; the work-product position is the operator's burden to establish, and the documentation requirement is a precondition.

### 4. Litigation-hold integration with the audit chain

When the operator receives a litigation hold (preservation letter, internal counsel notice, regulatory inquiry), the audit-chain retention-based deletion is **suspended** for the held scope. The hold is itself an audit-chain entry — the hold's existence, scope, and effective date are recorded in the chain.

Operationally:

1. Hold notice received by the operator's litigation-hold workflow (e.g., a separate matter-management system).
2. The audit-chain retention engine queries the litigation-hold workflow before any deletion run.
3. Records matching the hold's scope are skipped for deletion until the hold is released.
4. Hold release is itself an audit-chain entry.

## Consequences

**Positive.** Operators have a defensible posture against regulator inquiries AND against plaintiff-side discovery overreach. Privilege objections are supported by structured metadata, not by post-hoc legal argument. Retention follows SOL — operators are not holding indefinite liability surface. Litigation holds work without operator-side error-prone manual processes.

**Negative.** The policy layer is the operator's work, not the framework's. The framework provides the engineering rails; the operator's General Counsel + Chief Compliance Officer own the policy. The policy must be documented in writing before adoption and reviewed annually.

**Architectural.** The framework's engineering primitives are agnostic to the policy layer (deliberate design choice). This means the operator can choose retention windows, privilege framings, and litigation-hold integrations appropriate to their jurisdictions and risk appetite — without modifying the pattern code.

## What this does NOT cover

- **Jurisdiction-specific privilege rules.** Privilege scope varies by state (and varies for in-house counsel vs outside counsel; varies in inter-jurisdictional litigation). Operators consult counsel licensed in each relevant jurisdiction.
- **Cross-border discovery.** Hague Convention on the Taking of Evidence Abroad (1970), GDPR Article 48 (cross-border data transfer to satisfy a foreign court order) — these are out-of-scope for this ADR's framing and require specialized counsel.
- **Criminal-investigation grand-jury subpoena posture.** Grand-jury process compels production even of otherwise-privileged material in limited circumstances; this ADR's framing addresses civil discovery.
- **Reasonable-anticipation-of-litigation trigger.** The work-product doctrine requires a litigation-anticipation showing; whether anticipation is reasonable in a given fact pattern is a counsel question.
- **Spoliation sanctions.** If retention is poorly designed and discoverable artifacts are deleted in good faith but before a hold issues, the operator may face spoliation sanctions. This ADR's policy framing reduces but does not eliminate that risk.

## Regulatory anchor

- Federal Rules of Civil Procedure: Rule 26(b)(3) (work-product); Rule 502 (privilege); Rule 37(e) (lost ESI)
- Federal Rules of Evidence: 501 (privilege); 801(d)(2) (party admissions)
- *Upjohn Co. v. United States*, 449 U.S. 383 (1981) — attorney-client privilege scope in corporate context
- *Hickman v. Taylor*, 329 U.S. 495 (1947) — origin of the work-product doctrine
- Fair Housing Act SOL — 42 U.S.C. § 3613(a)(1)(A)
- ECOA / Regulation B retention — 12 C.F.R. § 1002.12
- FCRA SOL — 15 U.S.C. § 1681p
- SEC 17a-4 — 17 C.F.R. § 240.17a-4 (broker-dealer record retention)

## Implementation guidance

This ADR is policy + design, not code. Adopters integrate the four policy artifacts above with their existing litigation-hold workflow, privilege-log workflow, and retention-engine workflow. The cre-agent-audit `AuditLedger` (ADR-0003) provides the foundational append-only chain; the deployer's stack adds the retention/privilege/hold layer.

Reference integration sketches (v0.3 candidates):
- A `RetentionScheduler` adapter that reads SOL config from `compliance_rules.json` and runs SOL-aware deletion sweeps
- A `LitigationHoldRegistry` Protocol that the deletion engine queries before any sweep
- A privilege-metadata extension to `AuditEntry` (subclass or wrapper)

## Related

- ADR-0002 (Sovereign Veto) — generates bypass-justification fields the privilege layer protects
- ADR-0003 (Hash-chained Audit Ledger) — the underlying chain this ADR's policy layer wraps
- ADR-0007 (Lease-Abstraction Provenance) — generates discoverable provenance objects
- ADR-0008 (Fair-Housing Pre-Flight Gate) — generates the highest-stakes discoverable artifacts (exception logs with `FHA-DISPARATE` reason codes)
- ADR-0009 (Tenant PII Data Residency) — generates cross-jurisdiction request logs that GDPR Article 48 may interact with
- ADR-0011 (Vendor-Output Adapter Pattern) — vendor-mediated decisions create their own discovery surface
