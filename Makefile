# Use python3 by default (macOS); override with `make PY=python verify` on CI where `python` resolves to 3.x
PY ?= python3

.PHONY: help verify lint format typecheck test json-sync build smoke clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "%-12s %s\n", $$1, $$2}'

verify: lint format typecheck test json-sync build smoke  ## Run the full verification gate (recommended pre-commit and pre-PR)

lint:  ## ruff check
	ruff check . --output-format=github

format:  ## ruff format check (no changes; fail if reformatting needed)
	ruff format --check .

typecheck:  ## mypy --strict on src/ and tests/
	mypy --strict src/ tests/

test:  ## pytest with branch coverage; fail under 85
	pytest tests/ --cov=src/cre_agent_audit --cov-report=term-missing --cov-fail-under=85

json-sync:  ## Verify compliance_rules.json is in sync with compliance_rules.yaml
	$(PY) scripts/build_compliance_json.py
	git diff --exit-code config/compliance_rules.json

build:  ## Build a wheel
	$(PY) -m build --wheel

smoke:  ## Public-API import smoke test
	$(PY) -c "from cre_agent_audit import DefconController, AutonomyTier, FairHousingPreflightGate, TenantPIIResidencyCheck, AuditLedger, SovereignVeto, LeaseProvenanceCheck, ShadowRouter, RegulationLoader; print('quickstart imports OK')"

clean:  ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info src/*.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
