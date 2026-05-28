> **Provenance.** This file was drafted by the author in the FINOS AI Risk Initiative artifact format.
> **It has not been reviewed, endorsed, or accepted by FINOS or the AIR Working Group as of v0.2.0 (2026-06-02).**
> It is released independently under MIT alongside the patterns it accompanies. The full 19-artifact submission
> package — including 16 additional risk and mitigation files in author-draft form — is under separate
> working-group-bound development on a private branch (`finos-submission-wip`) and is not in this folder by design.
>
> Adopters: fork freely; cite in your own control catalog; do not infer FINOS endorsement from the use of the
> FINOS AIR schema. See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md).

---

## Description

The **Autonomy Ladder™ Sovereign Veto** is a non-overridable check that runs at the agent boundary before any action that crosses a constraint surface the agent does not have the authority to clear. The check is constraint-surface-specific — tenant screening dispatches to the Fair-Housing Pre-Flight Gate, lease abstraction dispatches to the Provenance Chain check, rent optimization dispatches to the DOJ-RealPage antitrust check, autonomous portfolio rebalancing dispatches to the three-boundary IPS/risk-limit/fiduciary-reasonableness check.

Four properties define the control:

1. **Non-overridable by the agent.** No prompt, no chain-of-thought, no reasoning step can bypass the veto. The veto sits outside the agent's reachable code path.
2. **Bypass-able by a human only with a logged exception.** A human can override the veto for a single decision, but the override generates a logged exception carrying a named owner, a regulatory basis, and a timestamp. The exception is durable.
3. **Constraint-surface-specific.** Different action classes dispatch to different domain checks. The veto layer is a registry, not a monolithic gate.
4. **Returns a structured reason code.** Vetoes are not "no." Vetoes are named reason codes (FHA-VOUCHER · PROV-INCOMPLETE-MATERIAL · ANTITRUST-COORDINATION · RESIDENCY-CROSS-JURISDICTION-UNTAGGED) that map to the audit chain and the regulator-readable explanation.

## How it works

The reference implementation is a Python class `SovereignVeto` with a registry of `action_class` → `ConstraintCheck`. Calls to `veto.check(action)` dispatch to the registered surface, evaluate the check, log the verdict to the audit ledger (ADR-0003), and return a structured `VetoResult` carrying the verdict (PASS / VETO), the reason code (if VETO), the owner-required for any bypass, and the diagnostic detail.

Calls for an unregistered `action_class` are conservatively vetoed with `UNKNOWN-ACTION-CLASS` — the framework refuses to let an agent sneak past the veto by inventing a new action class.

## Effectiveness

The control prevents the failure modes named in `AIR-RC-004` by structurally interposing between the agent's proposed action and the system-of-record write. The agent's reasoning is not the path of record; the typed action object plus the veto verdict is.

In the worked anonymized case study at `autonomy-ladder.io/case-studies/01`, the sovereign-veto layer fired 2,341 times in the first 30 days of production deployment across three regulated decision-class pilots — surfacing configuration drift, vendor-default changes, cross-team workflow assumptions, and bypass-by-default workarounds that no other control would have made visible.

## Implementation guidance

- The veto layer must sit outside the agent's process or, at minimum, outside the agent's reasoning context
- The check function returns `VetoResult` synchronously — async checks are an anti-pattern because they create reordering risk
- Every veto and every PASS is written to the hash-chain audit ledger (ADR-0003) — the veto layer does not silently approve
- The bypass mechanism requires a named human owner + a regulatory basis. Anonymous bypasses are an anti-pattern.
- Three bypasses by the same owner in a 90-day window auto-escalate to the General Counsel. Five bypasses on the same reason code in 90 days force the program to a restricted operational state.

## Reference materials

- Autonomy Ladder™ ADR-0002 — `github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0002-sovereign-veto.md`
- Reference Python implementation — `src/cre_agent_audit/governance/sovereign_veto.py`
- Companion ADR-0003 (Hash-chain Audit Ledger) — every veto is recorded immutably
- Companion ADR-0008 (Fair-Housing Pre-Flight Gate) — domain-specific check for tenant screening
- Companion ADR-0007 (Lease Provenance Chain) — domain-specific check for lease abstraction
- Companion ADR-0009 (Tenant PII Residency) — domain-specific check for cross-jurisdiction reads

## License

MIT-licensed. Fork the reference implementation freely. Cite Autonomy Ladder™ as the named pattern source.
