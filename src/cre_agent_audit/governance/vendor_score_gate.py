"""VendorScoreGate — third-party AI scoring captured into the audit chain.

Third-party scorers (background-check vendors, AVM vendors, fraud-score
vendors) ship behind opaque release cycles. Same input + same advertised
model version + a silently-patched scoring function = a score that drifts
without an operator-visible signal. FAILURE-MODES.md § Row 8 names this
class; ADR-0011 (Vendor-Output Adapter Pattern) is the architectural seam.

This module provides the concrete implementation. Every vendor-score event
hits the audit chain with full provenance — vendor_id, input_hash,
score, model_version, timestamp — and the gate watches for drift on the
(vendor_id, input_hash, model_version) key. Drift surfaces as a flagged
chain entry (`decision_type="vendor_score_drift"`) and, by default, raises
``VendorScoreDriftDetected`` so the caller's pipeline halts rather than
silently absorbing the change.

The Protocol surface is two methods (``emit`` and ``history_for``); the
in-memory default backend writes through to a provided ``AuditLedger``.
Opt-in sub-chain backends (separate vendor-scored ledger that can be
independently verified) are documented in ADR-0012 § Seam 1 integration
shape — they implement ``VendorScoreGate`` against a second ``AuditLedger``.

> Patterns are software, not legal advice. Regulatory citations live in
> ADR-0011 and FAILURE-MODES.md; consult counsel for applicability to
> your control environment.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditEntry,
    AuditLedger,
)


class VendorScoreDriftDetected(RuntimeError):
    """Raised when a vendor returns a different score for the same input + model.

    The flagged event is written to the audit chain BEFORE the exception
    propagates, so the drift is auditable even if the caller swallows the
    error. Recovery is operator-driven: vendor review playbook, freeze the
    vendor's signal, escalate per ADR-0011.
    """


@dataclass(frozen=True)
class VendorScoreEntry:
    """One vendor-scoring event, as returned by ``VendorScoreGate.emit``.

    Wraps the chain entry with the vendor-specific fields decoded for the
    caller, plus the drift signal (``drift_detected`` + ``previous_score``).
    """

    vendor_id: str
    input_hash: str
    score: float
    model_version: str
    sequence: int
    drift_detected: bool = False
    previous_score: float | None = None


@runtime_checkable
class VendorScoreGate(Protocol):
    """Capture third-party AI scoring decisions into the audit chain.

    ``emit`` records a (vendor_id, input_hash, score, model_version) tuple
    and watches for score drift on the (vendor_id, input_hash, model_version)
    key. ``history_for`` returns the recorded score events for a given
    (vendor_id, input_hash) — the audit-friendly read path.
    """

    def emit(
        self,
        *,
        vendor_id: str,
        input_hash: str,
        score: float,
        model_version: str,
    ) -> VendorScoreEntry: ...

    def history_for(
        self,
        *,
        vendor_id: str,
        input_hash: str,
    ) -> list[VendorScoreEntry]: ...


_EMIT_DECISION = "vendor_score_emit"
_DRIFT_DECISION = "vendor_score_drift"


@dataclass
class InMemoryVendorScoreGate:
    """Default backend: write through to a caller-provided ``AuditLedger``.

    All durability, retention, and verification semantics come from the
    underlying ``AuditLedger`` — the gate is a thin shim that enforces
    the vendor-scoring schema and the drift check.

    ``raise_on_drift`` (default True) controls whether drift propagates
    as ``VendorScoreDriftDetected`` after the flagged entry is written.
    Set False for shadow-mode rollouts where the caller wants to record
    drift but not halt the pipeline.
    """

    ledger: AuditLedger
    raise_on_drift: bool = True
    _seen: dict[tuple[str, str, str], float] = field(default_factory=dict)

    def emit(
        self,
        *,
        vendor_id: str,
        input_hash: str,
        score: float,
        model_version: str,
    ) -> VendorScoreEntry:
        _validate_inputs(
            vendor_id=vendor_id,
            input_hash=input_hash,
            score=score,
            model_version=model_version,
        )

        key = (vendor_id, input_hash, model_version)
        previous = self._seen.get(key)
        drift = previous is not None and not math.isclose(
            previous, score, rel_tol=0.0, abs_tol=1e-12
        )

        if drift:
            return self._emit_drift(
                vendor_id=vendor_id,
                input_hash=input_hash,
                score=score,
                model_version=model_version,
                previous=previous,  # type: ignore[arg-type]
            )

        chain_entry = self.ledger.append(
            actor_kind=ActorKind.SYSTEM,
            actor_id=vendor_id,
            decision_type=_EMIT_DECISION,
            action_payload=_encode_payload(
                vendor_id=vendor_id,
                input_hash=input_hash,
                score=score,
                model_version=model_version,
            ),
            gate_verdicts={"vendor_score": "recorded"},
        )
        self._seen[key] = score
        return VendorScoreEntry(
            vendor_id=vendor_id,
            input_hash=input_hash,
            score=score,
            model_version=model_version,
            sequence=chain_entry.sequence,
            drift_detected=False,
            previous_score=None,
        )

    def history_for(
        self,
        *,
        vendor_id: str,
        input_hash: str,
    ) -> list[VendorScoreEntry]:
        out: list[VendorScoreEntry] = []
        for chain_entry in self.ledger.entries:
            if chain_entry.decision_type not in {_EMIT_DECISION, _DRIFT_DECISION}:
                continue
            if chain_entry.actor_id != vendor_id:
                continue
            payload = _decode_payload(chain_entry)
            if payload.get("input_hash") != input_hash:
                continue
            previous_raw = payload.get("previous_score")
            out.append(
                VendorScoreEntry(
                    vendor_id=vendor_id,
                    input_hash=input_hash,
                    score=_as_float(payload["score"]),
                    model_version=str(payload["model_version"]),
                    sequence=chain_entry.sequence,
                    drift_detected=chain_entry.decision_type == _DRIFT_DECISION,
                    previous_score=(
                        _as_float(previous_raw) if previous_raw is not None else None
                    ),
                )
            )
        return out

    def _emit_drift(
        self,
        *,
        vendor_id: str,
        input_hash: str,
        score: float,
        model_version: str,
        previous: float,
    ) -> VendorScoreEntry:
        chain_entry = self.ledger.append(
            actor_kind=ActorKind.SYSTEM,
            actor_id=vendor_id,
            decision_type=_DRIFT_DECISION,
            action_payload=_encode_payload(
                vendor_id=vendor_id,
                input_hash=input_hash,
                score=score,
                model_version=model_version,
                previous_score=previous,
            ),
            gate_verdicts={"vendor_score_drift": "flagged"},
        )
        # Update the seen-table to the latest score so a third call with the
        # same drift target does not re-flag against the original score.
        # Operators reviewing the chain see the full sequence regardless.
        self._seen[(vendor_id, input_hash, model_version)] = score
        entry = VendorScoreEntry(
            vendor_id=vendor_id,
            input_hash=input_hash,
            score=score,
            model_version=model_version,
            sequence=chain_entry.sequence,
            drift_detected=True,
            previous_score=previous,
        )
        if self.raise_on_drift:
            raise VendorScoreDriftDetected(
                f"Vendor {vendor_id!r} returned score={score} for "
                f"input_hash={input_hash!r} under model_version={model_version!r}; "
                f"previous score was {previous}. Flagged chain entry at sequence "
                f"{chain_entry.sequence}."
            )
        return entry


# --------------------------------------------------------------------------- #
# Module-private helpers                                                      #
# --------------------------------------------------------------------------- #


def _validate_inputs(
    *,
    vendor_id: str,
    input_hash: str,
    score: float,
    model_version: str,
) -> None:
    if not vendor_id:
        raise ValueError("vendor_id must be a non-empty string")
    if not input_hash:
        raise ValueError("input_hash must be a non-empty string")
    if not model_version:
        raise ValueError("model_version must be a non-empty string")
    if math.isnan(score) or math.isinf(score):
        raise ValueError(f"score must be finite; got {score!r}")
    if not (0.0 <= score <= 1.0):
        raise ValueError(
            f"score must be in [0.0, 1.0] (the canonical risk-score interval); "
            f"got {score!r}"
        )


def _encode_payload(
    *,
    vendor_id: str,
    input_hash: str,
    score: float,
    model_version: str,
    previous_score: float | None = None,
) -> bytes:
    payload = {
        "vendor_id": vendor_id,
        "input_hash": input_hash,
        "score": score,
        "model_version": model_version,
    }
    if previous_score is not None:
        payload["previous_score"] = previous_score
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _decode_payload(chain_entry: AuditEntry) -> dict[str, object]:
    payload: dict[str, object] = json.loads(
        chain_entry.action_payload.decode("utf-8")
    )
    return payload


def _as_float(value: object) -> float:
    """Narrow an Any-from-json-loads value to float.

    Surfaces a clear error if the chain entry was somehow written with a
    non-numeric score field — we'd rather raise here than silently coerce.
    """
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(f"Expected numeric score, got {type(value).__name__}")


__all__ = [
    "InMemoryVendorScoreGate",
    "VendorScoreDriftDetected",
    "VendorScoreEntry",
    "VendorScoreGate",
]
