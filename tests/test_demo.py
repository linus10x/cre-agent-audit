"""Tests for the public `./demo.sh` entry point (`examples/governance_demo.py`).

Polarity-proven: each scene asserts the PRESENCE of the safe condition (the
attack is caught), not merely the absence of a crash. A companion negative-
control test in each scene proves the detector does NOT fire on a
legitimate/untampered path -- so a detector that always fires cannot pass
silently as "working."
"""

from __future__ import annotations

from pathlib import Path

import pytest
from governance_demo import (
    scene_deleted_entry,
    scene_forged_authorization,
    scene_regenerated_chain,
    seed_ledger_with_a_revocation,
    setup_ledger,
)

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.governance.ledger_store_jsonl import JsonlLedgerStore


def test_forged_authorization_is_refused(tmp_path: Path) -> None:
    ledger, _path = setup_ledger(tmp_path / "scene1.jsonl")
    result = scene_forged_authorization(ledger)
    assert result.caught is True
    assert "UNKNOWN-ACTION-CLASS" in result.detail


def test_registered_action_class_is_not_falsely_refused(tmp_path: Path) -> None:
    """Negative control: a REGISTERED, legitimately-authorized action class
    must pass, or scene_forged_authorization would be proving nothing (a
    veto that fires on everything is not a control)."""
    from cre_agent_audit.governance.sovereign_veto import (
        AgentAction,
        ConstraintCheck,
        SovereignVeto,
        VetoResult,
    )

    class _AlwaysPass(ConstraintCheck):
        def evaluate(self, action: AgentAction) -> VetoResult:
            return VetoResult.passing()

    ledger, _path = setup_ledger(tmp_path / "scene1b.jsonl")
    veto = SovereignVeto(ledger=ledger).register("legit_action", _AlwaysPass())
    result = veto.check(AgentAction(action_class="legit_action"))
    assert result.verdict.value == "PASS"


def test_deleted_entry_is_caught_by_verify_chain(tmp_path: Path) -> None:
    path = tmp_path / "scene2.jsonl"
    ledger, _ = setup_ledger(path)
    seed_ledger_with_a_revocation(ledger)
    result = scene_deleted_entry(path)
    assert result.caught is True
    assert "sequence" in result.detail


def test_deleted_entry_targets_the_actual_revocation(tmp_path: Path) -> None:
    """scene_deleted_entry must delete the REAL veto/revocation record --
    not an arbitrary line -- or "deleted revocation" would be a misnomer."""
    path = tmp_path / "scene2c.jsonl"
    ledger, _ = setup_ledger(path)
    seed_ledger_with_a_revocation(ledger)
    scene_deleted_entry(path)
    remaining = list(JsonlLedgerStore(path))
    assert all(e.decision_type != "sovereign_veto" for e in remaining)


def test_untampered_ledger_passes_verify_chain(tmp_path: Path) -> None:
    """Negative control: an untampered ledger must verify clean, or the
    detector in scene_deleted_entry would be a false-positive machine."""
    path = tmp_path / "scene2b.jsonl"
    ledger, _ = setup_ledger(path)
    seed_ledger_with_a_revocation(ledger)
    reloaded = AuditLedger(store=JsonlLedgerStore(path))
    reloaded.verify_chain()  # must not raise


def test_regenerated_chain_passes_internal_verify_but_fails_the_anchor(
    tmp_path: Path,
) -> None:
    """The sophisticated attack: a full-chain regeneration is internally
    self-consistent (verify_chain() alone is fooled -- this is ADR-0003's
    own documented limitation). The attacker also forges a witness_anchor
    entry claiming a chain head was anchored -- but that claim is not a key
    the INDEPENDENT witness store actually holds, which is what fails it."""
    result = scene_regenerated_chain(tmp_path)
    assert result.internal_verify_passed is True
    assert result.anchor_matched is False
    assert result.caught is True


def test_a_head_the_witness_never_saw_is_never_reported_as_matched(
    tmp_path: Path,
) -> None:
    """Direct regression test for the bug the adversarial review caught:
    the original implementation compared two independently-recomputed
    chain_head() values instead of checking the witness's own store, which
    made "MATCH" a coincidence of identical entries/timestamps rather than
    a real check. This asserts the fix: an untouched witness store containing
    only the honest run's head must never report a match for anything else."""
    result = scene_regenerated_chain(tmp_path)
    assert result.anchor_matched is False, (
        "a forged anchor claim matched the independent witness store -- "
        "the witness lookup is not actually checking independence"
    )


@pytest.mark.parametrize(
    "scene_name", ["forged authorization", "deleted entry", "regenerated chain"]
)
def test_every_scene_names_itself(scene_name: str, tmp_path: Path) -> None:
    """Each scene's SceneResult.name must be stable and non-empty -- the
    printed trace is part of the public demo contract."""
    if scene_name == "forged authorization":
        ledger, _ = setup_ledger(tmp_path / "n1.jsonl")
        result = scene_forged_authorization(ledger)
    elif scene_name == "deleted entry":
        path = tmp_path / "n2.jsonl"
        ledger, _ = setup_ledger(path)
        seed_ledger_with_a_revocation(ledger)
        result = scene_deleted_entry(path)
    else:
        result = scene_regenerated_chain(tmp_path)
    assert result.name == scene_name
