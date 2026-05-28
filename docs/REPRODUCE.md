# REPRODUCE — from cold clone to all-green in 5 commands

> **Reference reproduction guide.** This document tells a senior engineer or a Big-4 audit reviewer how to reproduce the v0.2.0 verification results from a fresh clone in under 60 seconds (warm pip cache; first-run cold-cache typically 90–120 seconds on M-series macOS).

## The 5 commands

```bash
# 1. Clone
git clone https://github.com/linus10x/cre-agent-audit.git
cd cre-agent-audit

# 2. Install (zero runtime deps; PyYAML in dev for the YAML→JSON build script)
pip install -e ".[dev]"

# 3. Run the full verification gate
make verify

# 4. Run one of the three worked examples (demonstrates governance behavior)
python examples/02_tenant_screening_preflight/run.py

# 5. (Optional) Run the other two examples
python examples/01_lease_abstraction_provenance/run.py
python examples/03_rent_optimization_sovereign_veto/run.py
```

## What `make verify` runs

The `Makefile` `verify` target chains these subtargets:

| Target | Tool | Expected output |
|---|---|---|
| `lint` | `ruff check .` | "All checks passed!" |
| `format` | `ruff format --check .` | "N files already formatted" |
| `typecheck` | `mypy --strict src/ tests/` | "Success: no issues found in N source files" |
| `test` | `pytest --cov=src/cre_agent_audit --cov-fail-under=85` | "142 passed" + "Total coverage: 89%+" |
| `json-sync` | `python scripts/build_compliance_json.py` + `git diff --exit-code config/compliance_rules.json` | empty diff |
| `build` | `python -m build --wheel` | wheel artifact in `dist/` |
| `smoke` | Import test of 9 patterns from `cre_agent_audit` package | "quickstart imports OK" |

The full chain runs in well under a second on a warm install; first-run dependency install plus the chain runs in 90–120 seconds on M-series macOS.

## What the example shows

`python examples/02_tenant_screening_preflight/run.py` demonstrates:

1. The Fair-Housing Pre-Flight Gate (Pattern 8 / ADR-0008) firing on protected-class proxy features
2. The Sovereign Veto (Pattern 2 / ADR-0002) rejecting decisions with structured reason codes (`FHA-VOUCHER`, `FHA-CRIM`)
3. The hash-chained Audit Ledger (Pattern 3 / ADR-0003) recording every decision (executed + vetoed)
4. `AuditLedger.verify_chain()` confirming the chain is internally consistent
5. The human-review handoff for bypassed decisions

Expected output ends with:
```
Total audit entries: 7 (every decision recorded)
Audit chain verified intact ✓
```

## Reproducing on CI matrix

The GitHub Actions workflow `.github/workflows/test.yml` runs the equivalent gate on a Python 3.10 / 3.11 / 3.12 matrix on `ubuntu-latest`. CI badge on the repo's main page reflects current status. To reproduce CI locally:

```bash
for py in 3.10 3.11 3.12; do
  python$py -m pip install -e ".[dev]"
  python$py -m pytest --cov=src/cre_agent_audit --cov-fail-under=85
done
```

(Requires each Python version installed; use `pyenv` or `uv` for parallel installations.)

## Reproducing the wheel

```bash
make build       # writes dist/cre_agent_audit-0.2.0-py3-none-any.whl
pip install --force-reinstall dist/cre_agent_audit-0.2.0-py3-none-any.whl
make smoke       # confirms public API imports work from the installed wheel
```

The wheel contains the `py.typed` marker (PEP 561), so downstream `mypy --strict` consumers get type information.

## If anything fails

| Failure | Likely cause | Fix |
|---|---|---|
| `make: *** No rule to make target 'verify'` | Older Make on Linux | `gmake verify` (BSD/macOS Make is the default) |
| `mypy: command not found` | Dev deps not installed | `pip install -e ".[dev]"` |
| `pytest --cov-fail-under` fails at 85 | Coverage regressed | This is a real failure — open an issue or PR; do not lower the threshold |
| `git diff --exit-code config/compliance_rules.json` fails | YAML was edited without re-running the build script | `python scripts/build_compliance_json.py && git add config/compliance_rules.json` |
| `python -m build` fails | `build` package missing | `pip install build` (already in dev extras) |
| Example script raises | Code regression | This is a real failure — open an issue with the traceback |

## Reporting reproduction failures

If `make verify` fails on a clean clone of a tagged release (e.g., v0.2.0), please open an issue at https://github.com/linus10x/cre-agent-audit/issues with:

1. Your platform (OS + version, Python version, pip version)
2. The exact command that failed
3. The full output (or first ~50 lines of it)
4. The commit SHA you're testing against (`git rev-parse HEAD`)

Reproduction failures are the highest-priority class of bug — please flag them.

## What this guide does NOT do

- Does not cover production-deployment patterns (those need an architectural design document specific to your stack — see [`ARCHITECTURE.md`](../ARCHITECTURE.md) for compose-order guidance and [`examples/FIRST_90_DAYS.md`](../examples/FIRST_90_DAYS.md) for adoption cadence)
- Does not cover the audit-chain external-witness-anchor integration (deployer responsibility; see [ADR-0003 Audit Evidence Properties](adr/0003-hash-chain-audit.md))
- Does not cover the vendor-mediated AI adoption path (see ADR-0011 + `docs/vendor-clauses/`)
