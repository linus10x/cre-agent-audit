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

In agentic AI workflows operating inside regulated financial-services or commercial-real-estate operations, an autonomous agent may propose or execute an action that crosses a constraint surface the agent does not have the authority to clear unilaterally. The failure mode is not random — it is concentrated in decisions where the agent's training distribution misaligns with regulatory or fiduciary constraint surfaces.

Examples in financial services: an autonomous allocator proposes a portfolio rebalance that exceeds a board-approved Value-at-Risk cap. A buy-side options-strategy agent recommends a position size that exceeds a FINRA threshold limit.

Examples in commercial real estate: a rent-pricing AI recommends prices across owners in the same market in a way that creates the antitrust-coordination surface the DOJ-RealPage consent decree (November 24, 2025) targeted. A tenant-screening AI scores housing-voucher applicants negatively in violation of the Fair Housing Act (the SafeRent failure mode, $2.3M settlement, November 2024).

## Contributing factors and root causes

- Agent design prioritizes execution speed over runtime boundary checks
- Constraint surfaces (mandate · fiduciary · regulatory) are not encoded in machine-readable form
- Human-in-the-loop review is bottlenecked at production volume and degrades to rubber-stamp
- No runtime mechanism exists to enforce non-overridable boundaries
- Vendor application logs are not tamper-evident and cannot be replayed by a regulator
- Operator does not have a single non-overridable check at the agent boundary

## Financial-services-specific examples

- Autonomous allocator proposes a rebalance exceeding board-approved VaR cap on a quarterly volatility regime
- Buy-side options-strategy agent recommends position sizes exceeding FINRA limits
- Rent-pricing AI recommends prices coordinated across owners in the same market — direct DOJ-RealPage failure mode
- Tenant-screening AI scores voucher applicants negatively — SafeRent failure mode

## Severity classification

**Severity: Critical.** Each named example above carries either a settled-case precedent ($15M TransUnion · $2.3M SafeRent · 7-year DOJ-RealPage structural restrictions) or a binding regulatory standard (FINRA position limits · board-approved VaR). The cost of an unmitigated failure is measured in millions per incident.

## Related research

- Autonomy Ladder™ ADR-0002 (Sovereign Veto pattern) — `github.com/linus10x/cre-agent-audit/blob/main/docs/adr/0002-sovereign-veto.md`
- Reference implementation in MIT-licensed code — `github.com/linus10x/cre-agent-audit/blob/main/src/cre_agent_audit/governance/sovereign_veto.py`
- Bessemer Venture Partners "AI Agent Autonomy Scale" (July 2025)
- Knight First Amendment Institute, Feng/McDonald/Zhang, "Levels of Autonomy for AI Agents" (July 28, 2025)
- DOJ-RealPage consent decree (United States v. RealPage Inc., November 24, 2025)
- SafeRent class settlement (Louis v. SafeRent Solutions, D. Mass., November 20, 2024)
- FTC + CFPB consent order with TransUnion Rental Screening Solutions (October 2023)

## Detection

A program lacking this control will show one or more of:
- Vendor logs of AI decisions that are not append-only and not regulator-replayable
- Absence of a runtime layer between agent reasoning and system-of-record write
- Inability to produce, on demand, the count of agent actions that were considered but not executed in a 30-day window
- Decisions recorded with no associated reason code (vetoes that fired) or with prose-only justifications

## Related mitigations

- `AIR-MIT-RC-VETO-01` — Autonomy Ladder™ Sovereign Veto pattern (preventative control)
