"""cre-replay CLI — list / run / run-all / verify.

Entry point declared in ``pyproject.toml`` ``[project.scripts]``.

Discovery: matters are Python modules under
``examples/regulatory-incidents/<NN>_<slug>/replay.py`` exposing a
top-level ``matter`` instance of an ``IncidentReplayBase`` subclass.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Iterable
from pathlib import Path

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.regulatory_replay.evidence_bundle import EvidenceBundle
from cre_agent_audit.regulatory_replay.replay import IncidentReplayBase
from cre_agent_audit.regulatory_replay.scoring import pattern_coverage_score


def _examples_dir() -> Path:
    """Walk up from this file to find the repo root, then the examples dir."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "examples" / "regulatory-incidents"
        if candidate.is_dir():
            return candidate
    raise RuntimeError("Could not locate examples/regulatory-incidents/")


def _discover_matters() -> list[IncidentReplayBase]:
    """Scan the examples directory and load each ``matter`` instance."""
    out: list[IncidentReplayBase] = []
    base = _examples_dir()
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue
        replay_py = child / "replay.py"
        if not replay_py.is_file():
            continue
        spec = importlib.util.spec_from_file_location(f"_matter_{child.name}", replay_py)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        matter = getattr(mod, "matter", None)
        if isinstance(matter, IncidentReplayBase):
            out.append(matter)
    return out


def _cmd_list(args: argparse.Namespace) -> int:
    matters = _discover_matters()
    print(f"{'matter_id':<40} {'title'}")
    print("-" * 100)
    for m in matters:
        print(f"{m.matter_id:<40} {m.matter_title}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    matters = {m.matter_id: m for m in _discover_matters()}
    if args.matter_id not in matters:
        print(f"unknown matter_id: {args.matter_id}", file=sys.stderr)
        print("available:", ", ".join(matters), file=sys.stderr)
        return 2
    matter = matters[args.matter_id]
    ledger = AuditLedger()
    result = matter.run_replay(ledger=ledger, gates={})
    bundle = EvidenceBundle.assemble(matter=matter, ledger=ledger, result=result)
    out_path = _examples_dir() / matter.matter_id / "audit-evidence" / f"{matter.matter_id}.zip"
    bundle.write_zip(out_path)
    score = pattern_coverage_score(matter, result)
    print(f"matter:   {matter.matter_id}")
    print(f"findings: {len(result.findings_produced)}")
    print(f"coverage: {score:.2f}")
    print(f"bundle:   {out_path}")
    return 0


def _cmd_run_all(args: argparse.Namespace) -> int:
    exit_codes: list[int] = []
    for matter in _discover_matters():
        rc = _cmd_run(argparse.Namespace(matter_id=matter.matter_id))
        exit_codes.append(rc)
        print("---")
    return max(exit_codes, default=0)


def _cmd_verify(args: argparse.Namespace) -> int:
    """Re-validate a previously-generated bundle."""
    import zipfile

    zip_path = Path(args.bundle_path)
    if not zip_path.is_file():
        print(f"bundle not found: {zip_path}", file=sys.stderr)
        return 2
    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())
        required = {
            "audit_chain.jsonl",
            "verify_chain_report.json",
            "mi_proxy_attestation.json",
            "findings.json",
            "controls_description_table.md",
            "narrative.md",
        }
        missing = required - names
        if missing:
            print(
                f"bundle missing required artifacts: {sorted(missing)}",
                file=sys.stderr,
            )
            return 1
    print(f"bundle valid: {zip_path}")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cre-replay",
        description="Replay named regulatory matters against cre-agent-audit",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list discovered matters")

    p_run = sub.add_parser("run", help="run one matter")
    p_run.add_argument("matter_id")

    sub.add_parser("run-all", help="run all matters")

    p_verify = sub.add_parser("verify", help="re-validate a bundle")
    p_verify.add_argument("bundle_path")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "list":
        return _cmd_list(args)
    if args.cmd == "run":
        return _cmd_run(args)
    if args.cmd == "run-all":
        return _cmd_run_all(args)
    if args.cmd == "verify":
        return _cmd_verify(args)
    parser.error("unknown command")
    return 2  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
