"""Tests for Regulation Loader — ADR-0005.

The runtime loader reads JSON (compliance_rules.json) so the package has zero
runtime dependencies. YAML is author-time only; scripts/build_compliance_json.py
emits the checked-in JSON artifact from the human-edited YAML.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cre_agent_audit.governance.regulation_loader import (
    InvalidComplianceRulesError,
    RegulationCitation,
    RegulationLoader,
)

SAMPLE_DATA: dict[str, object] = {
    "version": "1.0.0",
    "last_repo_review": "2026-05-22",
    "maintainer": "Kunjar Bhaduri",
    "patterns": {
        "defcon_state_machine": {
            "adr": "0001",
            "regulations": [
                {
                    "name": "NIST AI Risk Management Framework",
                    "statute": "NIST AI RMF 1.0 GOVERN 1.6",
                    "clause": "incident response procedures documented and tested",
                    "jurisdiction_level": "federal",
                    "jurisdictions": ["us_federal"],
                    "effective_date": "2023-01-26",
                    "pattern_function": "DefconController.transition_to",
                }
            ],
        },
        "fair_housing_preflight_gate": {
            "adr": "0008",
            "regulations": [
                {
                    "name": "Fair Housing Act",
                    "statute": "42 U.S.C. § 3604",
                    "clause": "discrimination in the sale or rental of housing",
                    "jurisdiction_level": "federal",
                    "jurisdictions": ["us_federal"],
                    "effective_date": "1968-04-11",
                    "pattern_function": "protected_class_proxy_detection",
                },
                {
                    "name": "Colorado AI Act",
                    "statute": "SB24-205",
                    "clause": "impact assessments for consequential decisions",
                    "jurisdiction_level": "state",
                    "jurisdictions": ["CO"],
                    "effective_date": "2026-02-01",
                    "pattern_function": "disparate_impact_monitor",
                },
            ],
        },
    },
}


@pytest.fixture()
def sample_yaml_file(tmp_path: Path) -> Path:
    """Backwards-compat fixture name; now writes JSON (loader is JSON-only at runtime)."""
    path = tmp_path / "compliance_rules.json"
    path.write_text(json.dumps(SAMPLE_DATA), encoding="utf-8")
    return path


class TestLoading:
    def test_from_file_returns_loader(self, sample_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(sample_yaml_file)
        assert isinstance(loader, RegulationLoader)

    def test_loader_exposes_version_and_metadata(self, sample_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(sample_yaml_file)
        assert loader.version == "1.0.0"
        assert loader.last_repo_review == "2026-05-22"
        assert loader.maintainer == "Kunjar Bhaduri"


class TestPatternLookup:
    def test_regulations_for_known_pattern_returns_all_citations(
        self, sample_yaml_file: Path
    ) -> None:
        loader = RegulationLoader.from_file(sample_yaml_file)
        regs = loader.regulations_for("fair_housing_preflight_gate")
        assert len(regs) == 2
        assert all(isinstance(r, RegulationCitation) for r in regs)
        names = {r.name for r in regs}
        assert names == {"Fair Housing Act", "Colorado AI Act"}

    def test_regulations_for_unknown_pattern_returns_empty(self, sample_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(sample_yaml_file)
        assert loader.regulations_for("does_not_exist") == ()

    def test_pattern_names_returns_all_known(self, sample_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(sample_yaml_file)
        names = loader.pattern_names()
        assert set(names) == {"defcon_state_machine", "fair_housing_preflight_gate"}


class TestReverseLookup:
    def test_patterns_satisfying_named_regulation(self, sample_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(sample_yaml_file)
        patterns = loader.patterns_satisfying("Fair Housing Act")
        assert "fair_housing_preflight_gate" in patterns

    def test_patterns_satisfying_returns_empty_for_unknown(self, sample_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(sample_yaml_file)
        assert loader.patterns_satisfying("Made Up Regulation") == ()


class TestCitationShape:
    def test_citation_carries_jurisdiction_and_effective_date(self, sample_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(sample_yaml_file)
        regs = loader.regulations_for("fair_housing_preflight_gate")
        co_act = next(r for r in regs if r.name == "Colorado AI Act")
        assert co_act.jurisdiction_level == "state"
        assert co_act.jurisdictions == ("CO",)
        assert co_act.effective_date == "2026-02-01"
        assert co_act.statute == "SB24-205"
        assert co_act.pattern_function == "disparate_impact_monitor"


class TestValidation:
    def test_missing_patterns_key_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"version": "1.0.0"}), encoding="utf-8")
        with pytest.raises(InvalidComplianceRulesError, match="patterns"):
            RegulationLoader.from_file(path)

    def test_pattern_without_regulations_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text(
            json.dumps({"patterns": {"weird_pattern": {"adr": "0099"}}}),
            encoding="utf-8",
        )
        with pytest.raises(InvalidComplianceRulesError, match="regulations"):
            RegulationLoader.from_file(path)

    def test_regulation_without_name_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text(
            json.dumps(
                {
                    "patterns": {
                        "weird_pattern": {
                            "adr": "0099",
                            "regulations": [{"statute": "Some statute"}],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(InvalidComplianceRulesError, match="name"):
            RegulationLoader.from_file(path)

    def test_loader_reads_json_not_yaml(self, tmp_path: Path) -> None:
        """RegulationLoader must read JSON to preserve zero-dep claim."""
        config_path = tmp_path / "compliance_rules.json"
        config_path.write_text(json.dumps(SAMPLE_DATA), encoding="utf-8")
        loader = RegulationLoader.from_file(config_path)
        assert loader.version == "1.0.0"
        assert "defcon_state_machine" in loader.pattern_names()

    def test_loader_rejects_yaml_extension(self, tmp_path: Path) -> None:
        """Runtime loader is JSON-only; YAML is build-time only."""
        yaml_path = tmp_path / "compliance_rules.yaml"
        yaml_path.write_text("version: 1.0.0\n", encoding="utf-8")
        with pytest.raises(ValueError, match="JSON"):
            RegulationLoader.from_file(yaml_path)

    def test_from_dict_works_without_file(self) -> None:
        data = {
            "version": "test",
            "patterns": {
                "p1": {
                    "adr": "0001",
                    "regulations": [
                        {
                            "name": "R1",
                            "statute": "S1",
                            "clause": "C1",
                            "jurisdiction_level": "federal",
                            "jurisdictions": ["us_federal"],
                            "effective_date": "2026-01-01",
                            "pattern_function": "fn1",
                        }
                    ],
                }
            },
        }
        loader = RegulationLoader.from_dict(data)
        assert loader.version == "test"
        assert len(loader.regulations_for("p1")) == 1


class TestNistAndTreasuryMapping:
    """Per Gap-Finding G-58 (G_58 in Memos/Gap_Finding_Synthesis_Report_2026-05-22.md).

    Every pattern carries at least one NIST AI RMF function + one Treasury
    FS AI RMF control range. The loader exposes both as queryable fields.
    """

    DATA_WITH_MAPPINGS: dict[str, object] = {
        "version": "1.1.0",
        "patterns": {
            "defcon_state_machine": {
                "adr": "0001",
                "regulations": [
                    {
                        "name": "NIST AI RMF",
                        "statute": "NIST AI RMF 1.0 GOVERN 1.6",
                        "clause": "incident response",
                        "jurisdiction_level": "federal",
                        "jurisdictions": ["us_federal"],
                        "effective_date": "2023-01-26",
                        "pattern_function": "DefconController.transition_to",
                        "nist_ai_rmf_function": "GOVERN",
                        "treasury_fs_ai_rmf_controls": ["TFRMF-LG-01", "TFRMF-LG-02"],
                    }
                ],
            },
            "sovereign_veto": {
                "adr": "0002",
                "regulations": [
                    {
                        "name": "NIST AI RMF GOVERN",
                        "statute": "GOVERN 2.3",
                        "clause": "risk decisions documented",
                        "jurisdiction_level": "federal",
                        "jurisdictions": ["us_federal"],
                        "effective_date": "2023-01-26",
                        "pattern_function": "SovereignVeto.check",
                        "nist_ai_rmf_function": "GOVERN",
                        "treasury_fs_ai_rmf_controls": ["TFRMF-DA-01", "TFRMF-DA-02"],
                    },
                    {
                        "name": "NIST AI RMF MEASURE",
                        "statute": "MEASURE 2.1",
                        "clause": "veto outcomes measured",
                        "jurisdiction_level": "federal",
                        "jurisdictions": ["us_federal"],
                        "effective_date": "2023-01-26",
                        "pattern_function": "SovereignVeto.check",
                        "nist_ai_rmf_function": "MEASURE",
                        "treasury_fs_ai_rmf_controls": ["TFRMF-DA-04"],
                    },
                ],
            },
        },
    }

    @pytest.fixture()
    def mapped_yaml_file(self, tmp_path: Path) -> Path:
        path = tmp_path / "compliance_rules.json"
        path.write_text(json.dumps(self.DATA_WITH_MAPPINGS), encoding="utf-8")
        return path

    def test_citation_carries_nist_function(self, mapped_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(mapped_yaml_file)
        regs = loader.regulations_for("defcon_state_machine")
        assert regs[0].nist_ai_rmf_function == "GOVERN"

    def test_citation_carries_treasury_controls(self, mapped_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(mapped_yaml_file)
        regs = loader.regulations_for("defcon_state_machine")
        assert regs[0].treasury_fs_ai_rmf_controls == ("TFRMF-LG-01", "TFRMF-LG-02")

    def test_nist_functions_for_returns_distinct_set(self, mapped_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(mapped_yaml_file)
        functions = loader.nist_functions_for("sovereign_veto")
        assert set(functions) == {"GOVERN", "MEASURE"}

    def test_treasury_controls_for_returns_distinct_set(self, mapped_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(mapped_yaml_file)
        controls = loader.treasury_controls_for("sovereign_veto")
        assert set(controls) == {"TFRMF-DA-01", "TFRMF-DA-02", "TFRMF-DA-04"}

    def test_nist_functions_for_unknown_pattern_returns_empty(self, mapped_yaml_file: Path) -> None:
        loader = RegulationLoader.from_file(mapped_yaml_file)
        assert loader.nist_functions_for("does_not_exist") == ()

    def test_treasury_controls_for_unknown_pattern_returns_empty(
        self, mapped_yaml_file: Path
    ) -> None:
        loader = RegulationLoader.from_file(mapped_yaml_file)
        assert loader.treasury_controls_for("does_not_exist") == ()

    def test_legacy_yaml_without_mappings_still_loads(self, sample_yaml_file: Path) -> None:
        """Backwards compatibility — the v1.0 YAML in the test fixture has no NIST/Treasury fields."""
        loader = RegulationLoader.from_file(sample_yaml_file)
        regs = loader.regulations_for("defcon_state_machine")
        assert regs[0].nist_ai_rmf_function is None
        assert regs[0].treasury_fs_ai_rmf_controls == ()
