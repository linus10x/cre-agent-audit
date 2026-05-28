# FINOS AI Risk Initiative submission cadence — Week-7 workflow

> **Reference workflow document, not legal or organizational advice.** This is the author's plan-of-record for completing the 19-file FINOS AIR submission package and contributing it to the [FINOS AI Risk Initiative](https://air.finos.org/) Working Group. Adapt to your relationship with the WG. See repo-root [`DISCLAIMER.md`](../DISCLAIMER.md).

## State as of v0.2.0 (2026-05-28)

The 19-file FINOS AIR submission package was originally drafted alongside the v0.2.0 release. Three of the 19 files (`AIR-RC-004`, `AIR-RC-007`, `AIR-MIT-RC-VETO-01`) were author-complete to a release-defensible standard and were carved out, cleaned up, and shipped on main under MIT in [`../governance-artifacts/`](../governance-artifacts/) with explicit non-endorsement provenance headers per the Stage 5 council decision.

The remaining 16 files are author-draft (council-approved structural stubs) awaiting Week-7 fill-in.

### Where the 16 draft files live

| Location | State | Status |
|---|---|---|
| Local git branch `finos-submission-wip` on the maintainer's machine | All 19 files at commit `e9d2f6eb5e81ac28018576d1fdfb39e724f11f6c` | Active working copy |
| Local-only safety tag `archive/finos-submission-wip-20260528T044124Z` | Same commit pinned by tag | Recoverable reference; NOT pushed to origin by design |
| Timestamped tarball at `~/Documents/110 - Kunjar's Resume/_archives/finos-submission-wip-snapshot-20260528T044124Z.tar.gz` | All 19 files + the submission-package README | Disaster-recovery backup |
| `origin/finos-submission-wip` | **Deleted 2026-05-28** | The branch was previously on origin (carried over from pre-Stage-5 work) and was deleted after the public-visibility flip revealed that GitHub has no concept of a private branch on a public repo. See "Historical-commit acknowledgement" below. |

### Historical-commit acknowledgement

The 16 draft files were committed to this repository's main branch *before* the public-visibility flip on 2026-05-28 and therefore exist in the repository's git history at commit `e9d2f6e` (the pre-Stage-5-removal main HEAD). They are not part of the current main tree but they are reachable via the historical commit SHA by anyone who clones the repository or browses the historical commit URL directly.

The author chose **not** to rewrite git history to remove the historical commit because: (a) the repo's published rules explicitly prohibit rewriting public hashes ("public hashes are permanent references"); (b) the draft files do not name confidential clients, vendors, or counterparties; (c) the content is consistent in framing with the rest of the repo; (d) the existence of the draft package in pre-public history is itself transparent — the author was working on a FINOS-WG-bound submission, the v0.2.0 carve-out shipped the three release-defensible files, and the remainder is documented in this very document as "awaiting Week-7 fill-in."

The 16 draft files in the historical commit are **author-draft only**. They have not been reviewed, endorsed, or accepted by FINOS or the AIR Working Group at any point. Adopters who encounter the historical commit content should treat those 16 files as identical in status to any author-draft work — useful as design context, not as adopted catalog entries.

## Week-7 fill-in workflow

When the maintainer is ready to complete the 16 draft files (target: Q3 2026 per `ROADMAP.md`):

```bash
# 1. Working copy is already in the local cre-agent-audit checkout
cd "/path/to/cre-agent-audit"
git checkout finos-submission-wip   # branch is local-only post-2026-05-28

# 2. Verify the safety tag still resolves
git show archive/finos-submission-wip-20260528T044124Z --no-patch --pretty=oneline

# 3. Fill in each of the 16 draft files following the FINOS AIR schema
#    See https://air.finos.org/ for the current schema and intake guidance.
#    Files to fill (16 of 19):
#    - mitigations/AIR-MIT-OP-AUDIT-01-autonomy-ladder-audit-chain.md
#    - mitigations/AIR-MIT-OP-DEFCON-01-autonomy-ladder-defcon.md
#    - mitigations/AIR-MIT-OP-PROV-01-autonomy-ladder-lease-provenance.md
#    - mitigations/AIR-MIT-OP-SHADOW-01-autonomy-ladder-shadow-mode.md
#    - mitigations/AIR-MIT-RC-FHA-01-autonomy-ladder-fair-housing.md
#    - mitigations/AIR-MIT-RC-LADDER-01-autonomy-ladder-a0-a4.md
#    - mitigations/AIR-MIT-RC-MAPPING-01-autonomy-ladder-regulation-mapping.md
#    - mitigations/AIR-MIT-SEC-PII-01-autonomy-ladder-tenant-pii.md
#    - risks/operational/AIR-OP-012-defcon-state-machine.md
#    - risks/operational/AIR-OP-013-hash-chain-audit.md
#    - risks/operational/AIR-OP-014-shadow-mode-rollout.md
#    - risks/operational/AIR-OP-015-lease-abstraction-provenance.md
#    - risks/regulatory-and-compliance/AIR-RC-005-autonomy-ladder-tier-mismatch.md
#    - risks/regulatory-and-compliance/AIR-RC-006-untraceable-regulation-mapping.md
#    - risks/security/AIR-SEC-010-tenant-pii-cross-jurisdiction.md
#    - (The 16th file is the submission-package README; refresh it to current state)
#
#    NOTE: as of Stage 5, three files (AIR-RC-004, AIR-RC-007, AIR-MIT-RC-VETO-01)
#    were carved out to ../governance-artifacts/ on main and CLEANED UP to remove
#    FINOS-internal jargon for non-WG readers. When preparing the WG PR, restore
#    the AIR schema frontmatter on those three from this branch's pre-carve-out
#    versions and reconcile with the latest schema.

# 4. Per-file checklist (apply to each of the 16):
#    [ ] Risk-statement scenario written with concrete CRE example
#    [ ] Likelihood + impact + severity assigned per AIR schema
#    [ ] Detection + prevention controls mapped to this repo's ADR
#    [ ] Mitigation cross-link to the corresponding AIR-MIT-* file
#    [ ] Regulatory anchors cited (NIST AI RMF + Treasury FS AI RMF +
#        EU AI Act + state statutes as applicable)
#    [ ] Implementation reference to src/cre_agent_audit/governance/*.py

# 5. Run the local verification gate before WG submission
make verify                                              # full gate
python3 -c "from cre_agent_audit import ..."             # quickstart smoke
# Also run a banned-word audit on the 19 files:
grep -niE 'delve|navigate|journey|transformative|unleash|unlock|game-changer' \
  finos-air-submission/

# 6. Engage the FINOS AIR Working Group through the public process
#    See https://github.com/finos/ai-governance-framework for current
#    contribution guidance. Open a PR there; do NOT push the WIP branch
#    to this repository's origin or any other public repo until the WG
#    has reviewed.
```

## What NOT to do during Week-7 fill-in

- **Do not push `finos-submission-wip` to `origin/cre-agent-audit`** until the WG has reviewed. The branch was previously on origin and was deliberately deleted (2026-05-28) to honor the Stage 5 council vote ("publishing a draft WG submission unilaterally would front-run the WG"). Re-pushing the branch reverses that decision without WG sign-off.
- **Do not publish the 16 fill-in commits to any other public GitHub repository** (a personal fork, a forked private-repo-made-public-later, etc.). The discipline is: drafts in private working copies → FINOS WG PR → adopted-or-revised through the WG → catalog entry. Skipping the middle two steps is front-running.
- **Do not create a public discussion thread on this repository asking for feedback on the 16 files** before WG submission. Same principle.
- **Do not name specific FINOS WG members in the file content** unless they have explicitly consented to attribution. The WG operates on consensus; attribution should be a WG-process decision, not an author-side decision.

## What to do during Week-7 fill-in

- **Work locally first.** Use the local branch + the safety tag + the tarball as your three-way backup.
- **Iterate on the content before engaging the WG.** Each file is one PR's worth of WG attention; quality of the initial draft determines turnaround.
- **Coordinate with FINOS AIR maintainers privately before the WG PR.** A 15-minute conversation aligns expectations and accelerates review. Their slack and contact information are at https://air.finos.org/.
- **Reference the three already-shipped artifacts in `../governance-artifacts/`** as the established standard. The carved-out drafts are already MIT-licensed and citable; the 16 fill-in files should match their structural quality before WG submission.

## Recovery paths (if something goes wrong locally)

If the local `cre-agent-audit` checkout is lost, corrupted, or accidentally has its `finos-submission-wip` branch deleted:

1. **First:** `git reflog --all | grep finos-submission` — the reflog typically retains the branch tip for 90 days after deletion.
2. **Second:** `git show archive/finos-submission-wip-20260528T044124Z` — the local-only safety tag preserves the commit reference at the snapshot moment.
3. **Third:** restore from the tarball at `~/Documents/110 - Kunjar's Resume/_archives/finos-submission-wip-snapshot-20260528T044124Z.tar.gz`. The tarball is a complete snapshot of the 19 files at the moment of branch-deletion.
4. **Last resort:** the historical commit `e9d2f6e` on origin/main still contains the full `finos-air-submission/` folder via git history. `git fetch origin && git checkout e9d2f6e -- finos-air-submission/` retrieves the files from public history.

The disaster-recovery surface is intentionally multi-layered. The Week-7 work is too valuable to lose to a stray `git branch -D`.

## After WG submission

Once the FINOS AIR Working Group reviews the 16-file PR:

- **If accepted:** the controls become FINOS-catalog entries with official FINOS-assigned IDs. Update `../governance-artifacts/` to cross-link to the FINOS catalog entries. Update `CHANGELOG.md` with a v0.2.1 (or v0.3) entry recording the catalog adoption. Update `../README.md` Governance-artifacts section to note the WG-accepted status.
- **If revised:** apply WG feedback, update the local working copies, return to step 5 of the Week-7 workflow.
- **If rejected (unlikely given the schema fidelity):** treat the local working copies as design context only; do not publish.

## Why this document exists

The Stage 5 council decision protected the FINOS WG relationship by removing the 16 stub files from the public main HEAD. The post-launch audit (Stage 17) verified that the original "preserve on a private branch" framing was structurally incorrect — GitHub has no concept of a private branch on a public repo — and the WIP branch was therefore publicly accessible until 2026-05-28. The branch deletion + this document together close the gap: the active working copy is now local-only, the leak path through git history is acknowledged transparently, and the Week-7 workflow is documented so the maintainer can complete the submission without ambiguity about state, location, or sequence.

If you are reading this in Week-7 (Q3 2026) and any of the file paths above have changed, treat this document as the historical record and update the on-main version with the current state.
