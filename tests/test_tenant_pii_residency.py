"""Tests for Tenant-PII Data-Residency Partitioning — ADR-0009."""

from __future__ import annotations

import pytest

from cre_agent_audit.governance.sovereign_veto import VetoVerdict
from cre_agent_audit.governance.tenant_pii_residency import (
    CrossJurisdictionRequest,
    LegalBasis,
    TenantPIIAction,
    TenantPIIResidencyCheck,
)


def _request(
    *,
    requesting_jurisdiction: str = "US_CA",
    target_jurisdiction: str = "US_CA",
    legal_basis: LegalBasis | None = None,
    purpose: str = "delinquency-risk modeling for Q3 2026 occupancy report",
    statute_citation: str | None = None,
    lia_document_id: str | None = None,
    consent_record_id: str | None = None,
) -> CrossJurisdictionRequest:
    return CrossJurisdictionRequest(
        requesting_actor="agent:strategy_v1",
        requesting_jurisdiction=requesting_jurisdiction,
        target_record_jurisdiction=target_jurisdiction,
        legal_basis=legal_basis,
        purpose=purpose,
        statute_citation=statute_citation,
        lia_document_id=lia_document_id,
        consent_record_id=consent_record_id,
    )


def _action(request: CrossJurisdictionRequest) -> TenantPIIAction:
    return TenantPIIAction(action_class="tenant_pii_read", request=request)


class TestIntraJurisdiction:
    def test_intra_jurisdiction_read_passes(self) -> None:
        check = TenantPIIResidencyCheck()
        result = check.evaluate(
            _action(
                _request(
                    requesting_jurisdiction="US_CA",
                    target_jurisdiction="US_CA",
                    legal_basis=None,
                )
            )
        )
        assert result.verdict is VetoVerdict.PASS


class TestCrossJurisdictionWithoutBasis:
    def test_cross_jurisdiction_without_legal_basis_vetoes(self) -> None:
        check = TenantPIIResidencyCheck()
        result = check.evaluate(
            _action(
                _request(
                    requesting_jurisdiction="US_CA",
                    target_jurisdiction="EU_DE",
                    legal_basis=None,
                )
            )
        )
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "RESIDENCY-CROSS-JURISDICTION-UNTAGGED"


class TestLegalBasisCompleteness:
    def test_consent_without_record_id_vetoes(self) -> None:
        check = TenantPIIResidencyCheck()
        result = check.evaluate(
            _action(
                _request(
                    requesting_jurisdiction="US_CA",
                    target_jurisdiction="EU_DE",
                    legal_basis=LegalBasis.CONSENT,
                    consent_record_id=None,
                )
            )
        )
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "RESIDENCY-CONSENT-MISSING"

    def test_lia_without_document_id_vetoes(self) -> None:
        check = TenantPIIResidencyCheck()
        result = check.evaluate(
            _action(
                _request(
                    requesting_jurisdiction="US_CA",
                    target_jurisdiction="EU_DE",
                    legal_basis=LegalBasis.LEGITIMATE_INTEREST,
                    lia_document_id=None,
                )
            )
        )
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "RESIDENCY-LIA-MISSING"

    def test_legal_obligation_without_statute_vetoes(self) -> None:
        check = TenantPIIResidencyCheck()
        result = check.evaluate(
            _action(
                _request(
                    requesting_jurisdiction="US_CA",
                    target_jurisdiction="EU_DE",
                    legal_basis=LegalBasis.LEGAL_OBLIGATION,
                    statute_citation=None,
                )
            )
        )
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "RESIDENCY-STATUTE-MISSING"

    def test_contract_basis_passes_without_additional_fields(self) -> None:
        check = TenantPIIResidencyCheck()
        result = check.evaluate(
            _action(
                _request(
                    requesting_jurisdiction="US_CA",
                    target_jurisdiction="US_NY",
                    legal_basis=LegalBasis.CONTRACT,
                )
            )
        )
        assert result.verdict is VetoVerdict.PASS


class TestPurposeSpecificity:
    @pytest.mark.parametrize(
        "vague_purpose",
        ["analytics", "operations", "reporting", "business intelligence", "ops", "BI"],
    )
    def test_vague_purpose_vetoes(self, vague_purpose: str) -> None:
        check = TenantPIIResidencyCheck()
        result = check.evaluate(
            _action(
                _request(
                    requesting_jurisdiction="US_CA",
                    target_jurisdiction="EU_DE",
                    legal_basis=LegalBasis.LEGITIMATE_INTEREST,
                    lia_document_id="lia-2026-q3-001",
                    purpose=vague_purpose,
                )
            )
        )
        assert result.verdict is VetoVerdict.VETO
        assert result.reason_code == "RESIDENCY-PURPOSE-VAGUE"

    def test_specific_purpose_passes(self) -> None:
        check = TenantPIIResidencyCheck()
        result = check.evaluate(
            _action(
                _request(
                    requesting_jurisdiction="US_CA",
                    target_jurisdiction="EU_DE",
                    legal_basis=LegalBasis.LEGITIMATE_INTEREST,
                    lia_document_id="lia-2026-q3-001",
                    purpose="delinquency-risk modeling for occupancy-cost report Q3 2026",
                )
            )
        )
        assert result.verdict is VetoVerdict.PASS


class TestRequestValidation:
    def test_request_construction_requires_non_empty_purpose(self) -> None:
        with pytest.raises(ValueError, match="purpose"):
            CrossJurisdictionRequest(
                requesting_actor="agent:x",
                requesting_jurisdiction="US_CA",
                target_record_jurisdiction="EU_DE",
                legal_basis=LegalBasis.CONTRACT,
                purpose="",
                statute_citation=None,
                lia_document_id=None,
                consent_record_id=None,
            )

    def test_request_construction_requires_non_empty_actor(self) -> None:
        with pytest.raises(ValueError, match="requesting_actor"):
            CrossJurisdictionRequest(
                requesting_actor="",
                requesting_jurisdiction="US_CA",
                target_record_jurisdiction="EU_DE",
                legal_basis=LegalBasis.CONTRACT,
                purpose="legitimate purpose",
                statute_citation=None,
                lia_document_id=None,
                consent_record_id=None,
            )
