"""cre-agent-audit — governance patterns for AI in commercial real estate.

Nine MIT-licensed patterns, zero runtime dependencies, primary-source
regulatory citations. Companion to ``finserv-agent-audit`` for financial
services.

See https://autonomy-ladder.io for the full framework. Patterns documented
in ``docs/adr/0001`` through ``docs/adr/0011``.

This package is a **reference architecture, not legal, regulatory, audit,
or fairness-testing advice.** See repo-root ``DISCLAIMER.md``.
"""

from __future__ import annotations

from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditChainTamperError,
    AuditEntry,
    AuditLedger,
)
from cre_agent_audit.governance.autonomy_ladder import (
    AutonomyTier,
    PromotionGateNotMet,
    PromotionGateReport,
    PromotionRequirements,
)
from cre_agent_audit.governance.defcon import (
    Capability,
    CapabilityRule,
    DefconController,
    DefconState,
    DefconTransition,
)
from cre_agent_audit.governance.fair_housing_preflight import (
    BypassRegistry,
    DisparateImpactMonitor,
    FairHousingPreflightGate,
)
from cre_agent_audit.governance.lease_provenance import (
    LeaseProvenanceCheck,
    LeaseRepository,
)
from cre_agent_audit.governance.ledger_store import (
    InMemoryLedgerStore,
    LedgerStore,
)
from cre_agent_audit.governance.ledger_store_jsonl import JsonlLedgerStore
from cre_agent_audit.governance.ledger_store_sqlite import SqliteLedgerStore
from cre_agent_audit.governance.mi_proxy import (
    Attestation,
    IntegrityVerificationError,
    LocalMIProxy,
    MIProxy,
    MIProxyKeyMissingWarning,
)
from cre_agent_audit.governance.mi_threshold_detector import (
    InvalidReferenceError,
    MIReferenceUndersizedWarning,
    MIThresholdDetector,
    MutualInformationCalculator,
    ProtectedClassReference,
    ProxyFinding,
)
from cre_agent_audit.governance.regulation_loader import (
    InvalidComplianceRulesError,
    RegulationCitation,
    RegulationLoader,
)
from cre_agent_audit.governance.shadow_mode import (
    DecisionClass,
    DecisionOutcome,
    PromotionVerdict,
    ShadowRouter,
    VetoDirection,
)
from cre_agent_audit.governance.sovereign_veto import (
    AgentAction,
    ConstraintCheck,
    SovereignBypass,
    SovereignVeto,
    VetoResult,
    VetoVerdict,
)
from cre_agent_audit.governance.tenant_pii_residency import (
    CrossJurisdictionRequest,
    LegalBasis,
    TenantPIIAction,
    TenantPIIResidencyCheck,
)
from cre_agent_audit.governance.vendor_score_gate import (
    InMemoryVendorScoreGate,
    VendorScoreDriftDetected,
    VendorScoreEntry,
    VendorScoreGate,
)
from cre_agent_audit.regulatory_replay import (
    ADRRef,
    Citation,
    Evidence,
    EvidenceBundle,
    Finding,
    IncidentReplay,
    IncidentReplayBase,
    ReplayResult,
    Severity,
    pattern_coverage_score,
)

__version__ = "0.2.3"
__all__ = [
    # Pattern 1 — DEFCON state machine (ADR-0001)
    "Capability",
    "CapabilityRule",
    "DefconController",
    "DefconState",
    "DefconTransition",
    # Pattern 2 — Sovereign Veto (ADR-0002)
    "AgentAction",
    "ConstraintCheck",
    "SovereignBypass",
    "SovereignVeto",
    "VetoResult",
    "VetoVerdict",
    # Pattern 3 — Hash-chain Audit Ledger (ADR-0003)
    "ActorKind",
    "AuditChainTamperError",
    "AuditEntry",
    "AuditLedger",
    "InMemoryLedgerStore",
    "JsonlLedgerStore",
    "LedgerStore",
    "SqliteLedgerStore",
    # Pattern 4 — Autonomy Ladder A0→A4 (ADR-0004)
    "AutonomyTier",
    "PromotionGateNotMet",
    "PromotionGateReport",
    "PromotionRequirements",
    # Pattern 5 — Regulation Mapping (ADR-0005)
    "InvalidComplianceRulesError",
    "RegulationCitation",
    "RegulationLoader",
    # Pattern 6 — Shadow-Mode Rollout (ADR-0006)
    "DecisionClass",
    "DecisionOutcome",
    "PromotionVerdict",
    "ShadowRouter",
    "VetoDirection",
    # Pattern 7 — Lease-Abstraction Provenance (ADR-0007)
    "LeaseProvenanceCheck",
    "LeaseRepository",
    # Pattern 8 — Fair-Housing Pre-Flight Gate (ADR-0008)
    "BypassRegistry",
    "DisparateImpactMonitor",
    "FairHousingPreflightGate",
    # Fair-housing MI-threshold detector (ADR-0008 update; v0.2.2)
    "InvalidReferenceError",
    "MIReferenceUndersizedWarning",
    "MIThresholdDetector",
    "MutualInformationCalculator",
    "ProtectedClassReference",
    "ProxyFinding",
    # Pattern 9 — Tenant PII Data Residency (ADR-0009)
    "CrossJurisdictionRequest",
    "LegalBasis",
    "TenantPIIAction",
    "TenantPIIResidencyCheck",
    # MI Proxy — verifier chain-of-custody (ADR-0013)
    "Attestation",
    "IntegrityVerificationError",
    "LocalMIProxy",
    "MIProxy",
    "MIProxyKeyMissingWarning",
    # VendorScoreGate — third-party AI scoring (ADR-0011 update)
    "InMemoryVendorScoreGate",
    "VendorScoreDriftDetected",
    "VendorScoreEntry",
    "VendorScoreGate",
    # Regulatory-incident replay framework (ADR-0014)
    "ADRRef",
    "Citation",
    "Evidence",
    "EvidenceBundle",
    "Finding",
    "IncidentReplay",
    "IncidentReplayBase",
    "ReplayResult",
    "Severity",
    "pattern_coverage_score",
    # Package metadata
    "__version__",
]
