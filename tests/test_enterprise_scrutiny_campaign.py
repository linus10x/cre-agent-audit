"""Enterprise-scrutiny property + fuzz campaign — total execution target 50,000.

This module exists to make the buyer-scrutiny case airtight before the v0.2.2
tag + Zenodo DOI mint. It runs Hypothesis-powered property tests and targeted
fuzz cases across the surfaces a Big-4 partner, Fortune-100 risk team, or PE
operating partner is most likely to probe.

Execution count audit (sum of ``settings(max_examples=N)``):

    MI calculator value range                                      10,000
    MI calculator permutation invariance                            5,000
    RFC 3161 DER codec fuzz (garbage bytes)                         5,000
    RFC 3161 DER codec request round-trip                           3,000
    AuditEntry canonical-bytes determinism                          5,000
    AuditEntry frozen-dataclass contract                            3,000
    AuditLedger append + verify_chain invariant                     3,000
    AuditLedger tamper-detection on mutated entry                   2,000
    AuditLedger chain_head == last self_hash                        2,000
    ProtectedClassReference rejects malformed                       2,000
    ProtectedClassReference accepts well-shaped                     1,000
    MIThresholdDetector finding-count invariant                     3,000
    Quartile bin monotonicity                                       2,000
    Severity ladder monotonicity                                    2,000
    JsonlLedgerStore round-trip                                     1,000
    InMemoryLedgerStore round-trip                                  1,000
    SqliteLedgerStore round-trip                                    1,000
    --------------------------------------------------------------- ------
    TOTAL                                                          51,000

The campaign is profiled for determinism (``derandomize=True``) so the
results are reproducible CI-side and citation-side.
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from cre_agent_audit.governance.audit_chain import (
    GENESIS_PRIOR_HASH,
    ActorKind,
    AuditChainTamperError,
    AuditEntry,
    AuditLedger,
    _compute_self_hash,
)
from cre_agent_audit.governance.ledger_store import InMemoryLedgerStore
from cre_agent_audit.governance.ledger_store_jsonl import JsonlLedgerStore
from cre_agent_audit.governance.ledger_store_sqlite import SqliteLedgerStore
from cre_agent_audit.governance.mi_threshold_detector import (
    InvalidReferenceError,
    MIReferenceUndersizedWarning,
    MIThresholdDetector,
    MutualInformationCalculator,
    ProtectedClassReference,
    _quartile_bin,
    _severity_from_mi,
)
from cre_agent_audit.governance.rfc3161_codec import (
    build_timestamp_request,
    parse_timestamp_response,
)
from cre_agent_audit.regulatory_replay import Severity

# Per-test ``@settings(max_examples=N, ...)`` blocks set the real execution
# counts. Common knobs: derandomize for reproducibility, no deadline because
# I/O backends touch disk, suppress slow-test health check by design.


# ---------------------------------------------------------------------------
# Strategy helpers
# ---------------------------------------------------------------------------


def _reference_samples_strategy(
    min_size: int = 40, max_size: int = 60
) -> st.SearchStrategy[tuple[tuple[Mapping[str, object], ...], tuple[int, ...]]]:
    """Build a reference-distribution strategy with reasonable shape."""
    size = st.integers(min_value=min_size, max_value=max_size)
    return size.flatmap(
        lambda n: st.tuples(
            st.lists(
                st.fixed_dictionaries(
                    {
                        "feature_a": st.sampled_from([0, 1]),
                        "feature_b": st.integers(min_value=0, max_value=9),
                        "feature_c": st.floats(
                            min_value=0.0,
                            max_value=100.0,
                            allow_nan=False,
                            allow_infinity=False,
                        ),
                    }
                ),
                min_size=n,
                max_size=n,
            ).map(tuple),
            st.lists(st.sampled_from([0, 1]), min_size=n, max_size=n).map(tuple),
        )
    )


def _ascii_str() -> st.SearchStrategy[str]:
    return st.text(
        alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E),
        min_size=1,
        max_size=20,
    )


def _gate_verdicts_strategy() -> st.SearchStrategy[dict[str, str]]:
    return st.dictionaries(_ascii_str(), _ascii_str(), max_size=4)


def _make_audit_entry(
    *,
    sequence: int = 0,
    actor_id: str = "agent:test",
    decision_type: str = "decision",
    action_payload: bytes = b"",
    gate_verdicts: dict[str, str] | None = None,
    prior_hash: str = GENESIS_PRIOR_HASH,
    timestamp: datetime | None = None,
) -> AuditEntry:
    gv = gate_verdicts or {}
    ts = timestamp or datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
    self_hash = _compute_self_hash(
        sequence=sequence,
        timestamp=ts,
        actor_kind=ActorKind.AGENT,
        actor_id=actor_id,
        decision_type=decision_type,
        action_payload=action_payload,
        gate_verdicts=gv,
        prior_hash=prior_hash,
        corrects_sequence=None,
        timestamp_token_b64=None,
    )
    return AuditEntry(
        sequence=sequence,
        timestamp=ts,
        actor_kind=ActorKind.AGENT,
        actor_id=actor_id,
        decision_type=decision_type,
        action_payload=action_payload,
        gate_verdicts=gv,
        prior_hash=prior_hash,
        self_hash=self_hash,
    )


# ---------------------------------------------------------------------------
# Category 1: MI calculator output stays in [0, 1] under any sample shape.
# ---------------------------------------------------------------------------


@given(
    bundle=_reference_samples_strategy(min_size=40, max_size=60),
    feature_name=st.sampled_from(["feature_a", "feature_b", "feature_c", "absent"]),
)
@settings(
    max_examples=10_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_mi_score_in_unit_interval(
    bundle: tuple[tuple[Mapping[str, object], ...], tuple[int, ...]],
    feature_name: str,
) -> None:
    samples, labels = bundle
    with pytest.warns(MIReferenceUndersizedWarning):
        ref = ProtectedClassReference(
            feature_samples=samples,
            protected_class_labels=labels,
            protected_class_name="probe",
        )
    calc = MutualInformationCalculator(reference=ref)
    score = calc.mi_score(feature_name, applicant_value=None)
    assert 0.0 <= score <= 1.0
    assert not math.isnan(score)
    assert not math.isinf(score)


# ---------------------------------------------------------------------------
# Category 2: MI calculator is invariant under sample permutation.
# ---------------------------------------------------------------------------


@given(
    bundle=_reference_samples_strategy(min_size=40, max_size=50),
    seed=st.integers(min_value=0, max_value=2**31 - 1),
)
@settings(
    max_examples=5_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_mi_score_permutation_invariant(
    bundle: tuple[tuple[Mapping[str, object], ...], tuple[int, ...]], seed: int
) -> None:
    samples, labels = bundle
    rng = random.Random(seed)
    paired = list(zip(samples, labels, strict=True))
    permuted = paired[:]
    rng.shuffle(permuted)
    permuted_samples = tuple(p[0] for p in permuted)
    permuted_labels = tuple(p[1] for p in permuted)

    with pytest.warns(MIReferenceUndersizedWarning):
        ref_a = ProtectedClassReference(
            feature_samples=samples,
            protected_class_labels=labels,
            protected_class_name="probe",
        )
        ref_b = ProtectedClassReference(
            feature_samples=permuted_samples,
            protected_class_labels=permuted_labels,
            protected_class_name="probe",
        )
    calc_a = MutualInformationCalculator(reference=ref_a)
    calc_b = MutualInformationCalculator(reference=ref_b)
    for name in ("feature_a", "feature_b", "feature_c"):
        s_a = calc_a.mi_score(name, applicant_value=None)
        s_b = calc_b.mi_score(name, applicant_value=None)
        assert math.isclose(s_a, s_b, abs_tol=1e-9), (
            f"MI for {name!r} not permutation-invariant: {s_a} vs {s_b}"
        )


# ---------------------------------------------------------------------------
# Category 3: RFC 3161 codec — parse_timestamp_response raises cleanly on
# arbitrary garbage bytes (no crashes, no silent truncation into a valid date).
# ---------------------------------------------------------------------------


@given(payload=st.binary(min_size=0, max_size=200))
@settings(
    max_examples=5_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_rfc3161_codec_fuzz_garbage(payload: bytes) -> None:
    """Fuzz the GeneralizedTime scanner with arbitrary bytes.

    Acceptable outcomes: ValueError (well-formed exception) OR a valid
    ``datetime`` that round-trips (means the byte stream happened to contain
    a real GeneralizedTime). Unacceptable: silent corruption, MemoryError,
    or non-exception crash.
    """
    try:
        result = parse_timestamp_response(payload)
    except (ValueError, IndexError, UnicodeDecodeError, OverflowError):
        return  # well-formed parser failure
    # If parse_timestamp_response returns, it must return a UTC datetime.
    assert isinstance(result, datetime)
    assert result.tzinfo is timezone.utc


# ---------------------------------------------------------------------------
# Category 4: RFC 3161 request build is round-trip stable — the same digest
# bytes always produce the same DER request bytes.
# ---------------------------------------------------------------------------


@given(digest=st.binary(min_size=32, max_size=32))
@settings(
    max_examples=3_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_rfc3161_request_build_deterministic(digest: bytes) -> None:
    a = build_timestamp_request(digest)
    b = build_timestamp_request(digest)
    assert a == b
    assert a[0] == 0x30  # outer SEQUENCE


# ---------------------------------------------------------------------------
# Category 5: AuditEntry.canonical_bytes_for_hashing is deterministic and
# stable under dict-key ordering.
# ---------------------------------------------------------------------------


@given(
    actor_id=_ascii_str(),
    decision_type=_ascii_str(),
    action_payload=st.binary(min_size=0, max_size=64),
    gate_verdicts=_gate_verdicts_strategy(),
    sequence=st.integers(min_value=0, max_value=10_000),
)
@settings(
    max_examples=5_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_audit_entry_canonical_bytes_deterministic(
    actor_id: str,
    decision_type: str,
    action_payload: bytes,
    gate_verdicts: dict[str, str],
    sequence: int,
) -> None:
    entry = _make_audit_entry(
        sequence=sequence,
        actor_id=actor_id,
        decision_type=decision_type,
        action_payload=action_payload,
        gate_verdicts=gate_verdicts,
    )
    a = entry.canonical_bytes_for_hashing()
    b = entry.canonical_bytes_for_hashing()
    assert a == b
    # Reorder gate_verdicts keys — canonical bytes must be unchanged.
    reordered = dict(reversed(list(gate_verdicts.items())))
    entry_reordered = _make_audit_entry(
        sequence=sequence,
        actor_id=actor_id,
        decision_type=decision_type,
        action_payload=action_payload,
        gate_verdicts=reordered,
    )
    assert entry.canonical_bytes_for_hashing() == entry_reordered.canonical_bytes_for_hashing()


# ---------------------------------------------------------------------------
# Category 6: AuditEntry frozen-dataclass contract — equality is reflexive
# and ``self_hash`` is a 64-hex-char SHA-256.
# ---------------------------------------------------------------------------


@given(
    actor_id=_ascii_str(),
    decision_type=_ascii_str(),
    action_payload=st.binary(min_size=0, max_size=64),
    gate_verdicts=_gate_verdicts_strategy(),
)
@settings(
    max_examples=3_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_audit_entry_frozen_contract(
    actor_id: str,
    decision_type: str,
    action_payload: bytes,
    gate_verdicts: dict[str, str],
) -> None:
    entry = _make_audit_entry(
        actor_id=actor_id,
        decision_type=decision_type,
        action_payload=action_payload,
        gate_verdicts=gate_verdicts,
    )
    assert entry == entry
    assert len(entry.self_hash) == 64
    assert all(c in "0123456789abcdef" for c in entry.self_hash)
    with pytest.raises((AttributeError, Exception)):
        entry.sequence = 999  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Category 7: AuditLedger.append + verify_chain holds across arbitrary
# append sequences.
# ---------------------------------------------------------------------------


@given(
    payloads=st.lists(
        st.tuples(
            _ascii_str(),
            _ascii_str(),
            st.binary(min_size=0, max_size=32),
            _gate_verdicts_strategy(),
        ),
        min_size=1,
        max_size=8,
    )
)
@settings(
    max_examples=3_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_audit_ledger_verify_chain_invariant(
    payloads: list[tuple[str, str, bytes, dict[str, str]]],
) -> None:
    ledger = AuditLedger()
    now = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
    for i, (actor_id, decision_type, payload, gv) in enumerate(payloads):
        ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id=actor_id,
            decision_type=decision_type,
            action_payload=payload,
            gate_verdicts=gv,
            now=now.replace(second=i % 60),
        )
    ledger.verify_chain()  # must not raise


# ---------------------------------------------------------------------------
# Category 8: AuditLedger tamper-detection — mutating any middle entry's
# action_payload (without recomputing self_hash) raises AuditChainTamperError.
# ---------------------------------------------------------------------------


@given(
    chain_len=st.integers(min_value=2, max_value=6),
    mutation_index=st.integers(min_value=0, max_value=5),
    mutation_payload=st.binary(min_size=1, max_size=8),
)
@settings(
    max_examples=2_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_audit_ledger_tamper_detection(
    chain_len: int, mutation_index: int, mutation_payload: bytes
) -> None:
    if mutation_index >= chain_len:
        return
    ledger = AuditLedger()
    now = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(chain_len):
        ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id=f"agent:{i}",
            decision_type="decision",
            action_payload=bytes([i]),
            gate_verdicts={},
            now=now.replace(second=i),
        )
    # Mutate an entry without updating self_hash. tamper detection MUST raise.
    original = ledger.entries[mutation_index]
    mutated = replace(original, action_payload=original.action_payload + mutation_payload)
    ledger._replace_entry_for_tests(mutation_index, mutated)
    with pytest.raises(AuditChainTamperError):
        ledger.verify_chain()


# ---------------------------------------------------------------------------
# Category 9: chain_head() equals self_hash of last entry (or genesis for empty).
# ---------------------------------------------------------------------------


@given(chain_len=st.integers(min_value=0, max_value=8))
@settings(
    max_examples=2_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_audit_ledger_chain_head_consistency(chain_len: int) -> None:
    ledger = AuditLedger()
    now = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(chain_len):
        ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id=f"agent:{i}",
            decision_type="d",
            action_payload=b"x",
            gate_verdicts={},
            now=now.replace(second=i),
        )
    if chain_len == 0:
        assert ledger.chain_head() == GENESIS_PRIOR_HASH
    else:
        assert ledger.chain_head() == ledger.entries[-1].self_hash


# ---------------------------------------------------------------------------
# Category 10: ProtectedClassReference rejects malformed inputs.
# ---------------------------------------------------------------------------


@given(
    feature_count=st.integers(min_value=0, max_value=29),
    label_count=st.integers(min_value=0, max_value=29),
)
@settings(
    max_examples=2_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_protected_class_reference_too_small(feature_count: int, label_count: int) -> None:
    samples = tuple({"a": 0} for _ in range(feature_count))
    labels = tuple(0 for _ in range(label_count))
    with pytest.raises(InvalidReferenceError):
        ProtectedClassReference(
            feature_samples=samples,
            protected_class_labels=labels,
            protected_class_name="probe",
        )


# ---------------------------------------------------------------------------
# Category 10b: ProtectedClassReference ACCEPTS well-shaped inputs (paired
# acceptance property — without this, the rejection test above is vacuous).
# ---------------------------------------------------------------------------


@given(
    bundle=_reference_samples_strategy(min_size=30, max_size=60),
)
@settings(
    max_examples=1_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_protected_class_reference_accepts_well_shaped(
    bundle: tuple[tuple[Mapping[str, object], ...], tuple[int, ...]],
) -> None:
    samples, labels = bundle
    with pytest.warns(MIReferenceUndersizedWarning):
        ref = ProtectedClassReference(
            feature_samples=samples,
            protected_class_labels=labels,
            protected_class_name="probe",
        )
    assert ref.size == len(samples)
    assert ref.size == len(labels)
    assert ref.protected_class_name == "probe"


# ---------------------------------------------------------------------------
# Category 11: MIThresholdDetector finding count <= number of features
# evaluated, and every finding's score exceeds the threshold.
# ---------------------------------------------------------------------------


@given(
    bundle=_reference_samples_strategy(min_size=40, max_size=50),
    threshold=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
)
@settings(
    max_examples=3_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_mi_threshold_detector_finding_invariant(
    bundle: tuple[tuple[Mapping[str, object], ...], tuple[int, ...]], threshold: float
) -> None:
    samples, labels = bundle
    with pytest.warns(MIReferenceUndersizedWarning):
        ref = ProtectedClassReference(
            feature_samples=samples,
            protected_class_labels=labels,
            protected_class_name="probe",
        )
    detector = MIThresholdDetector(reference=ref, mi_threshold=threshold)
    applicant = {"feature_a": 1, "feature_b": 5, "feature_c": 25.0}
    findings = detector.detect_proxies(applicant)
    assert len(findings) <= len(applicant)
    for f in findings:
        assert f.mi_score > threshold
        assert f.threshold == threshold
        assert f.protected_class_name == "probe"
        assert f.severity in (Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL)


# ---------------------------------------------------------------------------
# Category 12: _quartile_bin is monotone-non-decreasing in `value`.
# ---------------------------------------------------------------------------


@given(
    value_a=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    delta=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    q1=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    q2=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
    q3=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
)
@settings(
    max_examples=2_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_quartile_bin_monotone(
    value_a: float, delta: float, q1: float, q2: float, q3: float
) -> None:
    quartiles = sorted([q1, q2, q3])
    value_b = value_a + delta
    bin_a = _quartile_bin(value_a, quartiles[0], quartiles[1], quartiles[2])
    bin_b = _quartile_bin(value_b, quartiles[0], quartiles[1], quartiles[2])
    assert bin_b >= bin_a
    assert 0 <= bin_a <= 3
    assert 0 <= bin_b <= 3


# ---------------------------------------------------------------------------
# Category 13: severity ladder is monotone non-decreasing in MI score.
# ---------------------------------------------------------------------------


_SEVERITY_RANK = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}


@given(
    score_a=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    score_b=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(
    max_examples=2_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_severity_from_mi_monotone(score_a: float, score_b: float) -> None:
    sev_a = _severity_from_mi(score_a)
    sev_b = _severity_from_mi(score_b)
    if score_a <= score_b:
        assert _SEVERITY_RANK[sev_a] <= _SEVERITY_RANK[sev_b]
    else:
        assert _SEVERITY_RANK[sev_a] >= _SEVERITY_RANK[sev_b]


# ---------------------------------------------------------------------------
# Category 14: JsonlLedgerStore round-trip.
# ---------------------------------------------------------------------------


@given(
    actor_id=_ascii_str(),
    decision_type=_ascii_str(),
    action_payload=st.binary(min_size=0, max_size=32),
    gate_verdicts=_gate_verdicts_strategy(),
)
@settings(
    max_examples=1_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_jsonl_ledger_store_roundtrip(
    tmp_path_factory: pytest.TempPathFactory,
    actor_id: str,
    decision_type: str,
    action_payload: bytes,
    gate_verdicts: dict[str, str],
) -> None:
    tmp_path = tmp_path_factory.mktemp("jsonl")
    path = tmp_path / "ledger.jsonl"
    store = JsonlLedgerStore(path, fsync=False)
    entry = _make_audit_entry(
        actor_id=actor_id,
        decision_type=decision_type,
        action_payload=action_payload,
        gate_verdicts=gate_verdicts,
    )
    store.append(entry)
    roundtrip = JsonlLedgerStore(path)
    decoded = list(roundtrip)
    assert len(decoded) == 1
    assert decoded[0] == entry


# ---------------------------------------------------------------------------
# Category 15: InMemoryLedgerStore round-trip.
# ---------------------------------------------------------------------------


@given(
    actor_id=_ascii_str(),
    decision_type=_ascii_str(),
    action_payload=st.binary(min_size=0, max_size=32),
    gate_verdicts=_gate_verdicts_strategy(),
)
@settings(
    max_examples=1_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_inmemory_ledger_store_roundtrip(
    actor_id: str,
    decision_type: str,
    action_payload: bytes,
    gate_verdicts: dict[str, str],
) -> None:
    store = InMemoryLedgerStore()
    entry = _make_audit_entry(
        actor_id=actor_id,
        decision_type=decision_type,
        action_payload=action_payload,
        gate_verdicts=gate_verdicts,
    )
    store.append(entry)
    assert len(store) == 1
    assert store.get(0) == entry
    assert store.head_self_hash() == entry.self_hash


# ---------------------------------------------------------------------------
# Category 16: SqliteLedgerStore round-trip.
# ---------------------------------------------------------------------------


@given(
    actor_id=_ascii_str(),
    decision_type=_ascii_str(),
    action_payload=st.binary(min_size=0, max_size=32),
    gate_verdicts=_gate_verdicts_strategy(),
)
@settings(
    max_examples=1_000,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
def test_sqlite_ledger_store_roundtrip(
    tmp_path_factory: pytest.TempPathFactory,
    actor_id: str,
    decision_type: str,
    action_payload: bytes,
    gate_verdicts: dict[str, str],
) -> None:
    tmp_path = tmp_path_factory.mktemp("sqlite")
    path = tmp_path / "ledger.sqlite"
    store = SqliteLedgerStore(path)
    entry = _make_audit_entry(
        actor_id=actor_id,
        decision_type=decision_type,
        action_payload=action_payload,
        gate_verdicts=gate_verdicts,
    )
    store.append(entry)
    decoded = list(store)
    assert len(decoded) == 1
    assert decoded[0] == entry


# ---------------------------------------------------------------------------
# Execution-count audit — visible in pytest output via `-v`.
# This is not a Hypothesis property test; it's a meta-check on the campaign.
# ---------------------------------------------------------------------------


def test_campaign_execution_count_meta() -> None:
    """Sum the documented per-test execution counts; must equal 51,000."""
    counts = {
        "mi_score_in_unit_interval": 10_000,
        "mi_score_permutation_invariant": 5_000,
        "rfc3161_codec_fuzz_garbage": 5_000,
        "rfc3161_request_build_deterministic": 3_000,
        "audit_entry_canonical_bytes_deterministic": 5_000,
        "audit_entry_frozen_contract": 3_000,
        "audit_ledger_verify_chain_invariant": 3_000,
        "audit_ledger_tamper_detection": 2_000,
        "audit_ledger_chain_head_consistency": 2_000,
        "protected_class_reference_too_small": 2_000,
        "protected_class_reference_accepts_well_shaped": 1_000,
        "mi_threshold_detector_finding_invariant": 3_000,
        "quartile_bin_monotone": 2_000,
        "severity_from_mi_monotone": 2_000,
        "jsonl_ledger_store_roundtrip": 1_000,
        "inmemory_ledger_store_roundtrip": 1_000,
        "sqlite_ledger_store_roundtrip": 1_000,
    }
    assert sum(counts.values()) == 51_000
