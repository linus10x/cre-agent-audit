"""Audit-evidence bundle assembly.

Produces a 6-file zip per matter:

- ``audit_chain.jsonl`` — the recorded decisions
- ``verify_chain_report.json`` — ``verify_chain()`` output
- ``mi_proxy_attestation.json`` — verifier integrity placeholder
- ``findings.json`` — ``Finding[]`` from the replay
- ``controls_description_table.md`` — CTRL-NNN → finding mapping
- ``narrative.md`` — executive summary

The bundle is the deliverable a Big-4 partner, BigLaw counsel, or PE
operating partner can hand to their client.

> Patterns are software, not legal advice. Regulatory citations are
> reference mappings; consult counsel for applicability to your control
> environment.
"""

from __future__ import annotations

import json
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from cre_agent_audit.governance.audit_chain import AuditLedger
from cre_agent_audit.regulatory_replay.replay import (
    IncidentReplayBase,
    ReplayResult,
)


@dataclass(frozen=True)
class EvidenceBundle:
    """A 6-artifact bundle ready to write as a zip."""

    matter_id: str
    artifacts: Mapping[str, str]

    @classmethod
    def assemble(
        cls,
        *,
        matter: IncidentReplayBase,
        ledger: AuditLedger,
        result: ReplayResult,
    ) -> EvidenceBundle:
        """Assemble the six artifacts from the replay outputs."""
        audit_chain_jsonl = _format_audit_chain(ledger)
        verify_report = _format_verify_report(ledger)
        mi_proxy_att = _format_mi_proxy_placeholder(matter.matter_id)
        findings_json = json.dumps(result.to_dict(), indent=2, sort_keys=True)
        controls_table = _format_controls_table(matter, result)
        narrative = _format_narrative(matter, result)

        return cls(
            matter_id=matter.matter_id,
            artifacts={
                "audit_chain.jsonl": audit_chain_jsonl,
                "verify_chain_report.json": verify_report,
                "mi_proxy_attestation.json": mi_proxy_att,
                "findings.json": findings_json,
                "controls_description_table.md": controls_table,
                "narrative.md": narrative,
            },
        )

    def write_zip(self, path: Path) -> None:
        """Write the bundle to a zip file at ``path``."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, content in self.artifacts.items():
                z.writestr(name, content)


def _format_audit_chain(ledger: AuditLedger) -> str:
    """One JSON object per chain entry, newline-delimited."""
    lines: list[str] = []
    for entry in ledger.entries:
        lines.append(
            json.dumps(
                {
                    "sequence": entry.sequence,
                    "timestamp": entry.timestamp.isoformat(),
                    "actor_kind": entry.actor_kind.value,
                    "actor_id": entry.actor_id,
                    "decision_type": entry.decision_type,
                    "action_payload_hex": entry.action_payload.hex(),
                    "gate_verdicts": dict(entry.gate_verdicts),
                    "prior_hash": entry.prior_hash,
                    "self_hash": entry.self_hash,
                },
                sort_keys=True,
            )
        )
    return "\n".join(lines) + ("\n" if lines else "")


def _format_verify_report(ledger: AuditLedger) -> str:
    """Run ``verify_chain()`` and capture the pass/fail signal."""
    from cre_agent_audit.governance.audit_chain import AuditChainTamperError

    try:
        ledger.verify_chain()
        return json.dumps(
            {
                "verified": True,
                "chain_head": ledger.chain_head(),
                "entry_count": len(ledger.entries),
            },
            indent=2,
        )
    except AuditChainTamperError as e:  # pragma: no cover
        return json.dumps(
            {
                "verified": False,
                "error": str(e),
                "chain_head": ledger.chain_head(),
                "entry_count": len(ledger.entries),
            },
            indent=2,
        )


def _format_mi_proxy_placeholder(matter_id: str) -> str:
    """Opt-in MI Proxy attestation placeholder for replay context.

    Production deployments pass ``mi_proxy`` through
    ``verify_chain(mi_proxy=...)`` and capture the real attestation
    here. The placeholder documents that the seam exists; the matter
    replay does not exercise it by default.
    """
    return json.dumps(
        {
            "matter_id": matter_id,
            "mi_proxy_invoked": False,
            "note": (
                "MI Proxy attestation is the opt-in fail-closed hook "
                "documented in ADR-0013. For deployment-time bundles, the "
                "deployer wires LocalMIProxy via verify_chain(mi_proxy=...)."
            ),
        },
        indent=2,
    )


def _format_controls_table(matter: IncidentReplayBase, result: ReplayResult) -> str:
    """Markdown table mapping each finding's ADR pattern to CTRL-NNN."""
    rows = ["# Controls description table", ""]
    rows.append(f"**Matter:** {matter.matter_title}")
    rows.append(f"**Matter ID:** `{matter.matter_id}`")
    rows.append("")
    rows.append("| Finding | Pattern | CTRL ref | Severity | Regulatory anchor |")
    rows.append("|---|---|---|---|---|")
    for i, f in enumerate(result.findings_produced, start=1):
        ctrl_ref = f"CTRL-{f.pattern.number:03d}"
        anchor = (
            f"{f.regulatory_anchor.case_name} "
            f"({f.regulatory_anchor.court}, {f.regulatory_anchor.date_iso})"
        )
        rows.append(
            f"| F-{i:02d} | {f.pattern} ({f.pattern.title}) | "
            f"[{ctrl_ref}](../../../docs/controls/) | "
            f"{f.severity.value} | {anchor} |"
        )
    rows.append("")
    rows.append(
        "> Patterns are software, not legal advice. "
        "Regulatory citations are reference mappings; "
        "consult counsel for applicability to your control environment."
    )
    return "\n".join(rows) + "\n"


def _format_narrative(matter: IncidentReplayBase, result: ReplayResult) -> str:
    """One-page executive summary of the replay."""
    paragraphs = [
        f"# Replay narrative — {matter.matter_title}",
        "",
        f"**Matter ID:** `{matter.matter_id}`",
        "",
        "## Failure shape",
        "",
        matter.failure_shape,
        "",
        "## Patterns engaged",
        "",
    ]
    for adr in matter.patterns_engaged:
        paragraphs.append(f"- {adr} — {adr.title}")
    paragraphs.extend(
        [
            "",
            "## What this replay produced",
            "",
            f"- {result.chain_entries_written} audit-chain entries written",
            f"- {len(result.findings_produced)} findings surfaced",
            "",
            "## Primary-source citations",
            "",
        ]
    )
    for cit in matter.primary_sources:
        line = f"- *{cit.case_name}* — {cit.court}, {cit.docket}, {cit.date_iso}"
        if cit.url:
            line += f" — [link]({cit.url})"
        paragraphs.append(line)
    paragraphs.extend(
        [
            "",
            "## Disclaimer",
            "",
            (
                "This replay is a worked example. It is not legal advice and "
                "does not adjudicate the underlying matter. Patterns are "
                "software; regulatory characterizations are reference "
                "mappings — consult counsel for applicability."
            ),
        ]
    )
    return "\n".join(paragraphs) + "\n"
