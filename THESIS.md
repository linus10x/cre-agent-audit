# THESIS — A 3-Year Project (2026 → 2028)

**Status:** Public commitment · maintained by Kunjar Bhaduri · last refreshed 2026-05-28

This document records what this project is, why it persists across years not weeks, and what the public surface should look like at each milestone. Writing it down means visitors three months from now or three years from now can verify the framework was advanced as committed — not abandoned mid-arc.

## The thesis

Operator-side AI governance for regulated industries is a category of software that does not exist as a defined market in 2026 because the buyers — operators carrying the liability when their vendor AI fails — have not yet named what they need. The named-matter record (TransUnion 2023, SafeRent 2024, RealPage ongoing) is changing that. Operators now know what audit-evidence they need to produce. Few have it. Almost none can produce it from their existing vendor stack.

This project is the public framework + the productized services + the published commentary that names that category, populates it with reference implementations, and earns the right to be cited as canonical over the 2026–2028 window.

## Cornered resource (Five Pillars — non-replicable)

The reason this project is durable: the author's specific combination of operator credentials cannot be assembled by anyone starting from scratch in less than 20 years.

1. **$750M wealth-platform anchor account rescue** at a top-3 wealth-platform vendor — deal architecture + delivery
2. **12-day ransomware crisis** rebuilt on Azure in 50 days — SOC 2 Type 2 + ISO 27001 in the same window
3. **$7M → $140M P&L growth** over an 18-year arc — JPMorgan Chase Partner of the Year 2007 · 2009 · 2010
4. **Autonomy Ladder™ governance framework** — author of A0→A4 (`linus10x/cre-agent-audit`, `linus10x/finserv-agent-audit`, [`autonomy-ladder.io`](https://autonomy-ladder.io))
5. **PE-acquisition-to-divestiture operating arc** at a regulated-industry technology platform — full hold-period operating cadence

Every chapter is rare. The combination is irreproducible. The framework is the public surface of the combination.

## Three-year roadmap

### 2026 — Foundation + category claim

- ✅ **v0.2.0** released 2026-06-02 — 9 governance patterns, 142 tests, zero runtime dependencies
- ✅ **v0.2.1** released 2026-05-28 — 4 hardening ADRs (persistence, timestamps, witness anchor, MI Proxy), 234 tests, `FAILURE-MODES.md` matrix-as-contract, DOI [10.5281/zenodo.20434575](https://doi.org/10.5281/zenodo.20434575)
- **v0.2.2** target Q3 2026 — Regulatory-Incident Replay framework + 3 named-matter examples + ADR-0014 (operator-side category claim) + this `THESIS.md`
- **v0.3.0** target Q4 2026 — Production-deployment hardening, state-by-state regulatory coverage (TX, NY, CA, WA, FL), full ISO/IEC 42001 mapping

### 2027 — Commercial wedge + peer-reviewed credibility

- **v0.4.0** target Q2 2027 — PyPI publication, FINOS AIR Working Group submission, mermaid sequence diagrams for all 9 patterns, lease-abstraction litigation-discovery worked example
- **First $5K Diagnostic engagement signed** — committed milestone 2026-08-21 per `Applications-May-2026/v2-Refresh/Memos/Regulated_Operations_AI_Governance_Business_Plan_v3_LOCKED_2026-05-21.md`
- **First peer-reviewed publication** — ACM SEMS or FAccT submission on the matrix-as-contract pattern
- **finserv-agent-audit parity** — bring the FSI sibling to v0.2.1-equivalent state

### 2028 — Category-cited + scaled

- **v0.5.0** target Q1 2028 — Multi-agent topology audit (extending `AuditConsumer`); commercial-extras layer documented as separate repos for Postgres / S3 / DynamoDB backends
- **3 cumulative peer-reviewed publications** (target: 1 per year, cumulative)
- **State of CRE-AI Governance** quarterly report cadence established
- **Practitioner bench (private community)** — 30–60 paying members across Big-4 / BigLaw / PE / CTO seats

## Publishing cadence (load-bearing for the brand moat)

- **Weekly** — LinkedIn Mon/Wed/Fri + X Tue/Thu per CLAUDE.md cadence
- **Quarterly** — *State of CRE-AI Governance* published report
- **Annually** — One peer-reviewed paper submission to ACM SEMS / FAccT / SAFE consortium / Journal of Risk & Financial Management
- **Per release** — Framework release notes + DOI on major releases

## Productization commitment (the revenue stream)

Per `Applications-May-2026/v2-Refresh/Memos/Regulated_Operations_AI_Governance_Business_Plan_v3_LOCKED_2026-05-21.md` (Path B), seven productized services anchored on the framework:

- **$5K Diagnostic** — 90-minute interview + 20-page deliverable
- **$40K Audit** — 4-week engagement; produces full audit-evidence bundle
- **$15K/q Retainer** — quarterly rerun + new-matter coverage + regulatory-update brief
- **$25K–$50K Workshop** — 1-day on-site or 2-day virtual
- **$50K–$200K Cohort** — 8-week program; 20–40 seats
- **$25K–$100K/yr private intel subscription** — gated newsletter + private failure-mode catalog + deposition-shaped playbooks
- **$10K–$50K/yr practitioner bench** — invite-only community

See [`docs/services/`](docs/services/) for the public templates. The framework is open-source (MIT) and free. The engagements are not. The framework is the credential; the engagement is the deliverable.

## What this project will NOT become

- A vendor-side AI-governance product — would compromise the category claim (ADR-0014)
- A consultancy that competes on Big-4 RFPs — different buying motion, pricing collapses, reputation dilutes
- A SaaS product — out of scope for solo operator capacity; commercial-extras model preserves option value
- A free-tier consulting practice — pricing IS the moat; sub-$5K work declined as a matter of standing rule
- A multi-vertical framework before CRE + FSI are at parity — focus is the moat; rushing to insurance / healthcare before the two priors mature dilutes everything

## Verifiability

The commitments in this document are verifiable against the repo. Every milestone above maps to:

- A version tag (`git tag`)
- A DOI on Zenodo
- A peer-reviewed publication (when applicable)
- A dated commit on `main`

If the project drifts from this thesis without a public revision, future readers should treat the drift as a signal — not as silent re-scoping. Honest revisions are welcomed; silent abandonment is a credibility failure.

This document updates with the revision date at the top. Older versions remain in `git log`.

---

*Patterns are software, not legal advice. Regulatory citations are reference mappings; consult counsel for applicability to your control environment.*
