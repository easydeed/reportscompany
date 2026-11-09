# LR-002 release-check rollout

Status: implementation proposed; platform enforcement and independent review still pending. Branch fix/lr-002-required-release-checks starts at 5ddc7f04. This ticket changes CI selection/gating, not application behavior or database major version. LR-031 follows after this workflow change is reviewed and merged.

## Check behavior

Release checks runs on every pull request, push to main, merge-group event and manual dispatch. Its complete Git comparison includes deletions and both sides of renames, with no GitHub file-list truncation. A missing base/history runs both suites. The default PR checkout tests the proposed merge tree.

Backend Tests and Frontend Tests are reusable workflows. The existing step names, dependency installs, database setup, Chromium measurement, typecheck, Jest and full pytest execution are retained. Automatic branch-push duplicates are removed; manual execution of either suite remains available.

Only the final **Release gate** is intended to become required. Its always condition handles normal upstream dependency failures/skips. Whole-run cancellation, commit skip directives or platform startup failures can still prevent execution; those must remain blocking rather than count as success. Selected suites must succeed. Missing selection, failed classification, cancellation, failure or unexpected skipping is not a pass. Unselected suites may be skipped without leaving a conditional workflow pending. Documentation under docs selects backend because the suite reads docs; unrelated Markdown can skip both and still obtains a terminal gate.

Shared runtime/lockfiles, workspace packages, classifier code/tests and workflow changes select both suites. e2e changes select frontend typecheck/Jest; they do not run manual Playwright specs or claim LR-026 complete. See the effective path table in SOURCE_OF_TRUTH.md.

## Before enabling platform enforcement

1. Obtain Claude's independent PASS for the exact head, plus green hosted results for the new workflow.
2. Exercise a harmless failing suite in an isolated draft PR, verify Release gate fails, then restore it. Also verify a docs/unrelated-Markdown PR reaches a terminal gate. Retain run URLs and exact SHAs.
3. Identify an eligible reviewer identity distinct from the PR author. Currently both agents author as easydeed and only easydeed has collaborator access. GitHub cannot count author self-approval. Jerry has been asked for the separate account. No invented identity or blanket admin bypass is an acceptable substitute.
4. Read and save existing effective main branch protection/rulesets. Configure the final Release gate as required, reviewed PRs with stale approval handling, force-push/deletion restrictions, and the approved named-merger/emergency process. Record the actual GitHub App/source of the status context. Do not require the conditional backend/frontend check names.
5. Verify the effective rules using the platform API and an ordinary builder identity. Demonstrate unreviewed/failing PRs cannot merge. Do not lock out the named recovery operator.

Native approval enforcement is **not complete** while the separate identity is unresolved. Installing the workflow alone does not enforce review or prevent an administrator from merging a red PR. D-361 remains open until the platform proof is recorded.

## Emergency and recovery

Codex is the named merger after the other lane's PASS. An emergency must record reason, exact SHA, bypass actor/method and independent-review deadline within 24 hours. Ordinary work does not use that path. The smallest approved temporary relaxation must be restored and verified afterward; no recurring all-admin bypass.

If required gating is misconfigured, the authorized recovery operator restores the saved rules through repository administration, records why, and reapplies the corrected reviewed rule. This document contains no command that silently changes permissions or disables review.

## Verification evidence

Local gate tests cover path families, mixed and unknown changes, full rename/deletion Git comparisons, invalid history, incomplete comparisons, malformed classifier outputs, and the selected/unselected × suite-outcome matrix. Existing CI documentation, database provisioning, serial install, failure annotation and pinned-runner guards remain active. Hosted run evidence and the harmless failure/docs PR proofs must be added before enforcement is declared complete.

On November 9, local verification passed 162 tests and actionlint 1.7.12. The intended hosted negative probe at 0420308e (run 42673392668) stalled before any job started during GitHub's confirmed Actions/Checks outage (incident tp8cghg7tlc4). It is not a failed-gate proof. The temporary probe is restored in the subsequent commit; the draft is not mergeable until the final head receives real hosted validation and Claude's review. The post-#273 main run 42672765519 also failed twice at platform startup with no jobs/logs and an internal-server-error annotation. No application failure is inferred from those attempts. See https://www.githubstatus.com/incidents/tp8cghg7tlc4.

Database-major alignment and failing required database proofs when prerequisites disappear remain LR-031. The existing root npm install and browser-required flag are preserved here; no new dependency or lockfile is introduced.
