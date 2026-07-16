"""Zero-install demo — ``./demo.sh`` — ADR-0002, ADR-0003, ADR-0012.

Lives in ``examples/`` (not ``src/cre_agent_audit/``) — matching this repo's
own convention that runnable demonstration scripts stay out of the
distributed wheel. Import ``cre_agent_audit`` via ``PYTHONPATH=src`` (which
``demo.sh`` sets), the same as every other file in this directory.

Three scenes, each exercising real public API only (no test-only seams):

1. **Forged authorization, refused.** An agent submits a decision under an
   action_class no :class:`ConstraintCheck` was ever registered for. The
   Sovereign Veto (ADR-0002) fails closed by design: unregistered means
   VETO, never PASS. The refusal and its ledger trace are printed.
2. **Deleted revocation, caught by the hash chain.** An attacker with full
   storage write access (the threat model ``audit_chain.py`` documents
   explicitly) deletes the JSONL line holding a real veto/revocation entry.
   Reloading the ledger and calling ``verify_chain()`` (ADR-0003) raises
   ``AuditChainTamperError`` naming the sequence at which the chain breaks.
3. **Regenerated chain, caught only by the external anchor.** A single
   deleted line is the *naive* attack. The sophisticated one: an attacker
   who also rewrites every following entry produces a chain that is
   internally self-consistent — ``verify_chain()`` alone is fooled, exactly
   as ADR-0003 warns ("an attacker with full ledger-host write access can
   regenerate the entire chain end-to-end, and the regenerated chain will
   pass verify_chain()"). What catches it: the attacker can forge their own
   ``witness_anchor`` ledger entry claiming a chain head was anchored, but
   they have no way to make that claimed value a real key in the
   *independent* witness register's own records (ADR-0012) — they were
   never able to submit anything to it. The check below looks the claim up
   in the witness's own store, not in a value recomputed from the
   honest ledger — the two are not the same thing, and only the former
   proves what the scene claims.

Every scene uses ``cre_agent_audit`` production code paths: the real
``SovereignVeto`` dispatch, the real ``AuditLedger`` / ``JsonlLedgerStore``,
the real ``RFC3161TimestampSource`` (pointed at a loopback demo TSA so the
demo stays zero-network — swap in a real TSA URL for production), and the
real ``anchor_to_witness`` helper (pointed at an in-process demo witness —
swap in the repo's own ``RekorWitness`` or ``OpenTimestampsWitness`` for
production; both ship in ``witness_anchor.py``).

Zero install, no network, no make. (``./demo.sh`` sets ``PYTHONPATH=src`` and
runs this file directly; the loopback TSA server binds to ``127.0.0.1`` only
— no outbound network call is ever made.) Each run gets its own
``tempfile.mkdtemp()`` working directory, so concurrent runs never collide.
"""

from __future__ import annotations

import contextlib
import shutil
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

from cre_agent_audit.governance.audit_chain import (
    ActorKind,
    AuditChainTamperError,
    AuditLedger,
)
from cre_agent_audit.governance.ledger_store_jsonl import JsonlLedgerStore
from cre_agent_audit.governance.sovereign_veto import AgentAction, SovereignVeto
from cre_agent_audit.governance.timestamp_source import RFC3161TimestampSource
from cre_agent_audit.governance.witness_anchor import WitnessReceipt, anchor_to_witness


@dataclass(frozen=True)
class SceneResult:
    """Structured outcome of one demo scene — also asserted on by tests."""

    name: str
    caught: bool
    detail: str


@dataclass(frozen=True)
class _ReplayEntry:
    """One decision to replay through the real public ``append()`` API —
    typed so Scene 3 never needs to touch ``object`` or a private hash
    helper to build a self-consistent alternate chain."""

    actor_id: str
    decision_type: str
    payload: bytes


@dataclass(frozen=True)
class RegenerationResult(SceneResult):
    """Scene 3 needs two independent booleans, not one collapsed verdict —
    the whole point is that they disagree."""

    internal_verify_passed: bool = False
    anchor_matched: bool = False


def setup_ledger(path: Path) -> tuple[AuditLedger, Path]:
    """Build a fresh ledger backed by a JSONL file at ``path``."""
    ledger = AuditLedger(store=JsonlLedgerStore(path))
    return ledger, path


def seed_ledger_with_a_revocation(ledger: AuditLedger) -> None:
    """Append two legitimate decisions, one *real* revocation, then one more
    legitimate decision — the revocation deliberately mid-chain, not last.

    The revocation is a genuine ``SovereignVeto`` VETO (an unregistered
    action_class, same mechanism as Scene 1) — not a relabeled ordinary
    entry. Placement matters: deleting the LAST entry in a hash chain
    breaks nothing downstream (there is no following entry whose
    ``prior_hash`` would mismatch) — a tail deletion needs the external
    anchor to catch, same as Scene 3. Placing the revocation mid-chain
    means deleting it breaks the entry that follows it, which is the
    thing ``verify_chain()`` (Scene 2's point) actually detects.
    """
    ledger.append(
        actor_kind=ActorKind.AGENT,
        actor_id="demo-agent",
        decision_type="tenant_screening",
        action_payload=b"decision-0",
        gate_verdicts={"verdict": "PASS"},
    )
    ledger.append(
        actor_kind=ActorKind.AGENT,
        actor_id="demo-agent",
        decision_type="tenant_screening",
        action_payload=b"decision-1",
        gate_verdicts={"verdict": "PASS"},
    )
    SovereignVeto(ledger=ledger).check(
        AgentAction(action_class="lease_termination_forged_authority")
    )
    ledger.append(
        actor_kind=ActorKind.AGENT,
        actor_id="demo-agent",
        decision_type="tenant_screening",
        action_payload=b"decision-3",
        gate_verdicts={"verdict": "PASS"},
    )


# --------------------------------------------------------------------------- #
# Scene 1 — forged authorization, refused                                     #
# --------------------------------------------------------------------------- #


def scene_forged_authorization(ledger: AuditLedger) -> SceneResult:
    """An agent invents an action_class no check was ever registered for."""
    veto = SovereignVeto(ledger=ledger)
    action = AgentAction(action_class="pricing_override_forged_authority")
    result = veto.check(action)
    trace = ledger.entries[-1]
    caught = result.verdict.value == "VETO" and result.reason_code == "UNKNOWN-ACTION-CLASS"
    detail = (
        f"agent claimed action_class={action.action_class!r} with no registered "
        f"authority to clear it -> verdict={result.verdict.value} "
        f"reason_code={result.reason_code!r} owner_required={result.owner_required!r}\n"
        f"  ledger trace: seq={trace.sequence} decision_type={trace.decision_type!r} "
        f"gate_verdicts={trace.gate_verdicts}"
    )
    return SceneResult(name="forged authorization", caught=caught, detail=detail)


# --------------------------------------------------------------------------- #
# Scene 2 — deleted revocation, caught by the hash chain                      #
# --------------------------------------------------------------------------- #


def scene_deleted_entry(ledger_path: Path) -> SceneResult:
    """Delete the real revocation entry (the naive attack); reload and
    verify_chain().

    Finds the victim through the store's own structured iteration
    (``JsonlLedgerStore`` + ``AuditEntry.decision_type``), not text
    matching, then removes that specific JSONL line. Falls back to the
    middle line if no veto entry is present (keeps the function usable
    against any ledger shape a caller hands it).
    """
    entries = list(JsonlLedgerStore(ledger_path))
    if len(entries) < 3:
        raise RuntimeError("need >= 3 ledger entries before staging a deletion")
    victim_sequence = next(
        (e.sequence for e in entries if e.decision_type == "sovereign_veto"),
        len(entries) // 2,
    )

    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    victim_index = victim_sequence  # sequence == append order == line order here
    lines.pop(victim_index)
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    tampered = AuditLedger(store=JsonlLedgerStore(ledger_path))
    try:
        tampered.verify_chain()
    except AuditChainTamperError as exc:
        return SceneResult(
            name="deleted entry",
            caught=True,
            detail=f"deleted revocation at sequence {victim_sequence} -> verify_chain() raised: {exc}",
        )
    return SceneResult(
        name="deleted entry",
        caught=False,
        detail="verify_chain() did not detect the deletion",
    )


# --------------------------------------------------------------------------- #
# Scene 3 — full-chain regeneration, caught only by the external anchor       #
# --------------------------------------------------------------------------- #


class _LoopbackTSAHandler(BaseHTTPRequestHandler):
    """Minimal RFC 3161 responder — asserts "now", loopback only.

    Builds the same DER shape (SEQUENCE > GeneralizedTime) the real codec's
    own test suite uses to validate ``parse_timestamp_response``
    (``tests/test_rfc3161_codec.py::test_parse_synthetic_generalized_time``).
    A stand-in for a real TSA (FreeTSA, DigiCert, Sectigo, internal) — swap
    ``tsa_url`` in production; the client code exercised here
    (``RFC3161TimestampSource``) is unchanged either way.
    """

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        gentime = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "Z"
        body = gentime.encode("ascii")
        tsr = bytes([0x30, len(body) + 2, 0x18, len(body)]) + body
        self.send_response(200)
        self.send_header("Content-Type", "application/timestamp-reply")
        self.send_header("Content-Length", str(len(tsr)))
        self.end_headers()
        self.wfile.write(tsr)

    def log_message(self, *args: object) -> None:  # noqa: ARG002
        pass  # silence — the demo prints its own narration


@contextlib.contextmanager
def _loopback_tsa() -> Iterator[str]:
    """Start/stop a loopback demo TSA; yield its base URL. Real context
    manager (not a bare generator driven by manual ``next()`` calls) so
    ``server_close()`` always runs, even if the caller raises."""
    server = HTTPServer(("127.0.0.1", 0), _LoopbackTSAHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/tsr"
    finally:
        server.shutdown()
        thread.join(timeout=2.0)
        server.server_close()  # release the listening socket fd


@dataclass
class _DemoLocalWitness:
    """Stand-in for :class:`RekorWitness` / :class:`OpenTimestampsWitness`
    (both ship in ``witness_anchor.py`` for production use). Implements the
    real ``WitnessRegister`` protocol. ``records`` is the independent,
    out-of-band store an attacker with full ledger-storage write access has
    no path to write into — that is the entire property Scene 3 proves, so
    the scene's verdict is computed by looking a claim UP in this store, not
    by recomputing a value from the ledger a second time.
    """

    records: dict[str, WitnessReceipt]

    def anchor(self, chain_head_hex: str) -> WitnessReceipt:
        receipt = WitnessReceipt(
            register_name="demo-local-witness",
            register_url="in-process (swap in RekorWitness/OpenTimestampsWitness for production)",
            submitted_at=datetime.now(timezone.utc),
            receipt_blob=chain_head_hex.encode("ascii"),
            inclusion_uuid=None,
            log_index=len(self.records),
        )
        self.records[chain_head_hex] = receipt
        return receipt


def _claimed_anchor(ledger: AuditLedger) -> str | None:
    """Read the ledger's OWN claim about what chain head was anchored, from
    its own ``witness_anchor`` entry (if any) — not from a value recomputed
    independently. A rewritten ledger can carry a *forged* claim here; that
    is exactly what makes the witness-store lookup meaningful."""
    for entry in reversed(ledger.entries):
        if entry.decision_type == "witness_anchor":
            claimed = entry.gate_verdicts.get("chain_head_anchored")
            return claimed
    return None


def scene_regenerated_chain(tmp_dir: Path) -> RegenerationResult:
    """Build a real ledger with RFC 3161-stamped entries, anchor its head to
    an independent witness store, then simulate an attacker who regenerates
    the whole chain (including a forged anchor claim) via the real public
    ``AuditLedger.append(now=...)`` API — no private seam.
    """
    good_path = tmp_dir / "scene3_good.jsonl"
    tampered_path = tmp_dir / "scene3_tampered.jsonl"

    witness = _DemoLocalWitness(records={})

    entries_to_replay: list[_ReplayEntry] = [
        _ReplayEntry("demo-agent", "tenant_screening", b"applicant-001"),
        _ReplayEntry("demo-agent", "tenant_screening", b"applicant-002"),
        _ReplayEntry("sovereign_veto", "sovereign_veto", b"vetoed-003"),
    ]

    with _loopback_tsa() as tsa_url:
        good_ledger = AuditLedger(
            store=JsonlLedgerStore(good_path),
            timestamp_source=RFC3161TimestampSource(
                tsa_url=tsa_url, fallback_to_local_on_failure=False
            ),
        )
        for spec in entries_to_replay:
            good_ledger.append(
                actor_kind=ActorKind.AGENT,
                actor_id=spec.actor_id,
                decision_type=spec.decision_type,
                action_payload=spec.payload,
                gate_verdicts={"verdict": "PASS"},
            )
        # The ONLY value ever written into the independent witness store.
        anchor_to_witness(ledger=good_ledger, witness=witness)

    # --- Attacker: full storage write access, regenerates the whole chain --
    # Same actor/decision/payload sequence, but the FIRST entry is backdated.
    # Uses only the real public `append(now=...)` parameter -- no private
    # hash helper is touched.
    attacker_ledger = AuditLedger(store=JsonlLedgerStore(tampered_path))
    backdated = datetime.now(timezone.utc) - timedelta(days=400)
    for i, spec in enumerate(entries_to_replay):
        attacker_ledger.append(
            actor_kind=ActorKind.AGENT,
            actor_id=spec.actor_id,
            decision_type=spec.decision_type,
            action_payload=spec.payload,
            gate_verdicts={"verdict": "PASS"},
            now=backdated if i == 0 else datetime.now(timezone.utc),
        )
    # A sophisticated attacker also forges a plausible-looking witness_anchor
    # entry, claiming their own regenerated head was anchored. They have no
    # path to actually submit to the real, independent witness register --
    # that is the point of an external register -- so this claim is built
    # by hand, not by calling `anchor_to_witness` against a witness they
    # don't have access to.
    forged_head = attacker_ledger.chain_head()
    attacker_ledger.append(
        actor_kind=ActorKind.SYSTEM,
        actor_id="system:witness_anchor",
        decision_type="witness_anchor",
        action_payload=b"forged-receipt",
        gate_verdicts={
            "witness_register": "demo-local-witness",
            "chain_head_anchored": forged_head,
        },
    )
    shutil.copyfile(tampered_path, good_path)  # simulate the storage-layer overwrite

    reloaded = AuditLedger(store=JsonlLedgerStore(good_path))
    internal_verify_passed = True
    try:
        reloaded.verify_chain()
    except AuditChainTamperError:
        internal_verify_passed = False

    claimed = _claimed_anchor(reloaded)
    # The check that matters: is the ledger's OWN claim about what was
    # anchored actually a key the INDEPENDENT witness genuinely holds?
    anchor_matched = claimed is not None and claimed in witness.records

    caught = internal_verify_passed and not anchor_matched
    detail = (
        f"verify_chain() on the regenerated chain: "
        f"{'PASSED (fooled — this is ADR-0003’s own documented limit)' if internal_verify_passed else 'FAILED'}\n"
        f"  ledger's own claim of what was anchored: {claimed}\n"
        f"  independent witness store actually holds: {sorted(witness.records)}\n"
        f"  anchor comparison: {'MATCH' if anchor_matched else 'MISMATCH — the claim is not a real witness record; tamper detected'}"
    )
    return RegenerationResult(
        name="regenerated chain",
        caught=caught,
        detail=detail,
        internal_verify_passed=internal_verify_passed,
        anchor_matched=anchor_matched,
    )


# --------------------------------------------------------------------------- #
# main                                                                         #
# --------------------------------------------------------------------------- #


def main() -> int:
    print("cre-agent-audit — demo\n" + "=" * 60)

    with tempfile.TemporaryDirectory(prefix="cre-agent-audit-demo-") as tmp:
        with_tmp = Path(tmp)

        print("\n[1/3] An agent forges its own authorization (no evidence behind it)")
        print("-" * 60)
        ledger1, _ = setup_ledger(with_tmp / "scene1.jsonl")
        r1 = scene_forged_authorization(ledger1)
        print(r1.detail)
        print(f"  -> {'REFUSED, as designed' if r1.caught else 'NOT CAUGHT — FAIL'}")

        print("\n[2/3] An attacker deletes a revocation entry (naive tamper)")
        print("-" * 60)
        ledger2, path2 = setup_ledger(with_tmp / "scene2.jsonl")
        seed_ledger_with_a_revocation(ledger2)
        r2 = scene_deleted_entry(path2)
        print(r2.detail)
        print(f"  -> {'CAUGHT by the hash chain' if r2.caught else 'NOT CAUGHT — FAIL'}")

        print("\n[3/3] An attacker regenerates the whole chain with a backdated record")
        print("-" * 60)
        r3 = scene_regenerated_chain(with_tmp)
        print(r3.detail)
        print(f"  -> {'CAUGHT by the external anchor' if r3.caught else 'NOT CAUGHT — FAIL'}")

        all_caught = r1.caught and r2.caught and r3.caught
        print("\n" + "=" * 60)
        if all_caught:
            print("All three attacks refused or caught. A plain append-only log with")
            print("no hash chain and no external anchor would have missed the last two.")
        else:
            print("REGRESSION: at least one scene did not behave as designed.")
        return 0 if all_caught else 1


if __name__ == "__main__":
    sys.exit(main())
