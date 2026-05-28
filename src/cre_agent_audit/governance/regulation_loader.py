"""Regulation Loader — ADR-0005.

Loads the source-of-truth `compliance_rules.json` and exposes a structured
lookup from governance patterns to the regulations they satisfy (and the
reverse direction: regulations to patterns).

The runtime reads this to label every audit-ledger entry with the regulations
satisfied by the gates that passed. A vetoed entry records which regulation
triggered the veto.

Format note: the runtime loader is **JSON-only** so the package has zero
runtime dependencies. The human-edited source of truth is YAML
(`config/compliance_rules.yaml`); `scripts/build_compliance_json.py` emits
the checked-in JSON artifact. CI verifies the two stay in sync.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class InvalidComplianceRulesError(ValueError):
    """Raised when ``compliance_rules.json`` does not conform to ADR-0005's schema."""


@dataclass(frozen=True)
class RegulationCitation:
    """One regulation citation satisfied by a pattern.

    The ``nist_ai_rmf_function`` and ``treasury_fs_ai_rmf_controls`` fields
    were added in compliance_rules.yaml v1.1.0 per Gap-Finding G-58 — the
    NIST + Treasury overlay is the credibility anchor for Private Capital
    buyer conversations. Legacy v1.0 YAML files load with ``None`` /
    empty-tuple defaults so the upgrade is backwards-compatible.
    """

    name: str
    statute: str
    clause: str
    jurisdiction_level: str  # 'federal' | 'state' | 'municipal' | 'international'
    jurisdictions: tuple[str, ...]
    effective_date: str  # ISO date string per ADR-0005
    pattern_function: str
    last_reviewed: str | None = None
    nist_ai_rmf_function: str | None = None
    """One of GOVERN, MAP, MEASURE, MANAGE per NIST AI RMF 1.0 (2023)."""
    treasury_fs_ai_rmf_controls: tuple[str, ...] = ()
    """List of TFRMF-* control IDs from Treasury FS AI RMF (Feb 19, 2026)."""


@dataclass(frozen=True)
class RegulationLoader:
    """Read-only view of compliance_rules.yaml — built once, queried many times."""

    version: str
    last_repo_review: str
    maintainer: str
    _by_pattern: dict[str, tuple[RegulationCitation, ...]]
    _by_regulation: dict[str, tuple[str, ...]]

    # ----------------------------- builders ----------------------------- #

    @classmethod
    def from_file(cls, path: Path | str) -> RegulationLoader:
        p = Path(path)
        if p.suffix.lower() != ".json":
            raise ValueError(
                f"RegulationLoader.from_file is JSON-only at runtime "
                f"(got {p.suffix!r}); use scripts/build_compliance_json.py "
                f"to convert author-time YAML to runtime JSON"
            )
        with p.open(encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegulationLoader:
        if not isinstance(data, dict) or "patterns" not in data:
            raise InvalidComplianceRulesError(
                "compliance_rules.yaml must have a top-level 'patterns' key"
            )

        by_pattern: dict[str, tuple[RegulationCitation, ...]] = {}
        by_regulation: dict[str, list[str]] = {}

        for pattern_name, pattern_block in data["patterns"].items():
            if not isinstance(pattern_block, dict) or "regulations" not in pattern_block:
                raise InvalidComplianceRulesError(
                    f"pattern {pattern_name!r} missing 'regulations' key"
                )
            citations: list[RegulationCitation] = []
            for raw in pattern_block["regulations"]:
                citations.append(_build_citation(raw, pattern_name=pattern_name))
                by_regulation.setdefault(raw["name"], []).append(pattern_name)
            by_pattern[pattern_name] = tuple(citations)

        return cls(
            version=str(data.get("version", "")),
            last_repo_review=str(data.get("last_repo_review", "")),
            maintainer=str(data.get("maintainer", "")),
            _by_pattern=by_pattern,
            _by_regulation={name: tuple(p) for name, p in by_regulation.items()},
        )

    # ----------------------------- queries ------------------------------ #

    def regulations_for(self, pattern_name: str) -> tuple[RegulationCitation, ...]:
        return self._by_pattern.get(pattern_name, ())

    def patterns_satisfying(self, regulation_name: str) -> tuple[str, ...]:
        return self._by_regulation.get(regulation_name, ())

    def pattern_names(self) -> tuple[str, ...]:
        return tuple(self._by_pattern.keys())

    def nist_functions_for(self, pattern_name: str) -> tuple[str, ...]:
        """Return the distinct NIST AI RMF functions a pattern satisfies.

        Order is the order the functions first appear across the pattern's
        regulation entries. Returns an empty tuple for unknown patterns or
        patterns whose YAML predates v1.1.0.
        """
        seen: list[str] = []
        for citation in self._by_pattern.get(pattern_name, ()):
            if citation.nist_ai_rmf_function and citation.nist_ai_rmf_function not in seen:
                seen.append(citation.nist_ai_rmf_function)
        return tuple(seen)

    def treasury_controls_for(self, pattern_name: str) -> tuple[str, ...]:
        """Return the distinct Treasury FS AI RMF control IDs a pattern maps to.

        Order preserves first-appearance across the pattern's regulation entries.
        Returns an empty tuple for unknown patterns or patterns whose YAML
        predates v1.1.0.
        """
        seen: list[str] = []
        for citation in self._by_pattern.get(pattern_name, ()):
            for control in citation.treasury_fs_ai_rmf_controls:
                if control not in seen:
                    seen.append(control)
        return tuple(seen)


def _build_citation(raw: dict[str, Any], *, pattern_name: str) -> RegulationCitation:
    if not isinstance(raw, dict) or "name" not in raw:
        raise InvalidComplianceRulesError(
            f"pattern {pattern_name!r}: regulation entry missing 'name' key"
        )
    jurisdictions = tuple(raw.get("jurisdictions", ()))
    nist_function = raw.get("nist_ai_rmf_function")
    treasury_controls = tuple(raw.get("treasury_fs_ai_rmf_controls", ()))
    return RegulationCitation(
        name=str(raw["name"]),
        statute=str(raw.get("statute", "")),
        clause=str(raw.get("clause", "")),
        jurisdiction_level=str(raw.get("jurisdiction_level", "")),
        jurisdictions=jurisdictions,
        effective_date=str(raw.get("effective_date", "")),
        pattern_function=str(raw.get("pattern_function", "")),
        last_reviewed=raw.get("last_reviewed"),
        nist_ai_rmf_function=str(nist_function) if nist_function else None,
        treasury_fs_ai_rmf_controls=treasury_controls,
    )
