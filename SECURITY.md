# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.2.x | ✓ Active |
| < 0.2  | ✗ Not supported |
| `main` | ✓ Active |

## Reporting a vulnerability

Report security issues through GitHub's private security advisory channel:

`https://github.com/linus10x/cre-agent-audit/security/advisories/new`

Do not file public issues for security findings. Public disclosure before the maintainer has had a chance to fix the issue puts every operator running the framework at risk.

## Response service-level

- **Acknowledgment** — within 72 hours of receipt
- **Triage** — within 1 week of acknowledgment
- **Fix proposal** — within 2 weeks of triage for confirmed vulnerabilities
- **Disclosure** — within 90 days of acknowledgment unless the reporter and the maintainer mutually agree to a different window for severity, complexity, or coordinated-disclosure reasons

## Severity rubric

The maintainer classifies reports against this rubric:

- **Critical** — the framework allows an unauthorized actor to forge an audit-ledger entry, bypass the sovereign veto without a logged exception, or read tenant PII across jurisdictions without a `LegalBasis` tag.
- **High** — the framework leaks a regulated decision class (tenant screening, rent pricing, lease abstraction) through a non-audited code path.
- **Medium** — the framework computes an incorrect veto reason code or returns an inconsistent state across DEFCON transitions.
- **Low** — the framework's diagnostic output is misleading or the documentation overstates a guarantee.

## Out of scope

- **Third-party integrations** — vendor adapters, named PMS / IWMS systems, broker bridges are operator-owned and out of scope here.
- **Operational deployments** — security of any specific deployment (network, secrets, infrastructure) is operator-owned. This repo ships reference architecture; production hardening lives with the operator.
- **Strategy logic** — the framework is governance code. Strategy logic that consumes the framework lives elsewhere and is out of scope.

## Credit

Confirmed reporters who follow the disclosure process are credited in `CHANGELOG.md` and in the release notes for the version that ships the fix. Anonymous reporting is supported on request.

## Bounty

This is an open-source MIT-licensed reference architecture maintained by a single operator. There is no monetary bounty program at this time. Recognition is the credit mechanism. The maintainer is open to negotiating contract work directly with researchers whose findings materially improve the framework.

## Maintainer

Kunjar Bhaduri · `autonomy-ladder.io` · Autonomy Ladder™ framework
