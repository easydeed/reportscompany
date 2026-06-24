---
name: multi-agent-workflow
description: The operating discipline for running multi-agent development work on TrendyReports. Use this skill whenever work is divided across multiple agents (investigators, builders, reviewers) or whenever any agent is about to investigate, write code, branch, commit, review, or push. It defines the roles, branch hygiene, verification gates, reviewer authority, and push rules that every agent must follow. Apply it for ANY implementation work — feature builds, fixes, refactors, investigations — not only large multi-agent batches. If you are an agent doing work on this repo, this skill governs how you do it.
---

# Multi-Agent Workflow Discipline

This is the operating manual for how development work is run on TrendyReports.
It is project-agnostic: it governs *how* work is done, not *what* is built.
Individual tickets define the what. This skill defines the how, and it is not
optional.

The discipline below was learned the hard way. Every rule maps to a specific
way something went wrong: tangled working trees, silently reverted edits from
a cloud-sync folder, unpushed work piling up, changes from different tickets
commingled in one commit, an agent half-finishing a security change and
calling it done. Follow the rules and those failures do not recur.

## Core Principles (read first, apply always)

1. **One ticket, one branch, one logical change, one merge.** Work never
   stacks loosely in a shared working tree. Each unit of work is isolated on
   its own branch so it can be verified and rolled back independently.

2. **Investigation precedes writing. Always.** No agent modifies a file it has
   not read. No agent builds against a system it has not mapped. When a task
   has unknowns, investigate first and report findings before touching code.

3. **Import, don't copy.** If working code already exists for something, reuse
   it. Duplicating a working implementation creates two things to maintain and
   two places for bugs to diverge. Prefer extending the existing path over
   building a parallel one.

4. **The Reviewer gate is real and has teeth.** Nothing merges to `main` until
   the Reviewer passes it. One unresolved BLOCK = nothing merges. This is not
   advisory.

5. **One pusher to main.** Builders push their own branches freely (so work is
   always backed up). Only the Gopher merges to `main`, and only after Reviewer
   approval.

6. **Verify before you commit, verify after you push.** `git diff --cached`
   before every commit. Confirm exactly the intended files are staged. Verify
   on production after every push.

7. **When in doubt, slow down.** Moving fast across multiple tickets at once is
   what causes tangles. One thing at a time, verified, beats five things at
   once, jumbled.

---

## Roles

Work is divided across focused roles. One agent may play multiple roles on a
small task, but the *responsibilities* of each role always apply.

### Investigator (the "Gopher" in investigation mode)
- Reads source files and reports findings. Never guesses from memory.
- Output is organized as: **WHAT EXISTS** (current code/behavior, with
  file:line) → **WHAT'S RELEVANT** (patterns to follow, functions to reuse) →
  **WHAT TO WATCH** (gotchas, edge cases, prior breakages).
- Says "the code shows" / "I see at file:line", never "I believe" / "I think".
- Cites file paths and line numbers in every reference.
- Flags conflicts: if two files define the same thing differently, calls it out.
- Makes NO code changes. Investigation is read-only.

### Builder (backend or frontend)
- Implements exactly what the ticket scopes — no more, no less.
- Reads every file before modifying it.
- Imports existing functions rather than copying them.
- Follows existing patterns exactly (if the codebase does X a certain way, match it).
- Owns only the files in the ticket's scope. Touching anything outside scope
  is a violation — flag it for a separate ticket instead.
- Guards optional data (missing field = hidden/handled, never a crash).

### Reviewer
- The last line of defense before merge. Has hard BLOCK authority.
- Checks: scope compliance (only intended files changed), pattern compliance
  (imports not copies, follows existing patterns), no regressions, acceptance
  criteria actually met (not just claimed), verification evidence present.
- Reports specifically: "file:line — what's wrong — how to fix", never "looks
  off".
- One BLOCK issue = the whole review is BLOCK. The Builder fixes and
  resubmits; Reviewer then re-checks the FULL list, not just the one fix.
- Does not fix code. Reports issues; the Builder fixes them.

### Gopher (in push mode)
- The single merge-to-`main` authority.
- Merges a branch to `main` ONLY after the Reviewer has passed it.
- Before merging: confirms the branch is clean, the diff is exactly the
  intended change, and no stray files (lockfile drift, untracked junk) ride along.
- Pushes, then confirms the deploy is healthy.

---

## Branch Hygiene (non-negotiable)

- **Every ticket gets its own branch off `main`**, named `feat/<ticket-id>-<short-desc>`
  or `fix/<ticket-id>-<short-desc>`. Example: `feat/p2a-onboarding-success-metric`.
- **No feature-branches-off-feature-branches.** All branches are flat, off `main`.
  Nesting branches is how histories tangle and merges fight each other.
- **`main` stays always-deployable.** Never commit work-in-progress that breaks
  the build directly to `main`.
- **One branch = one logical change.** If you find yourself touching two
  unrelated concerns, that's two branches.
- **Builders push their own branches to origin** as they work — this keeps
  every piece of work backed up on GitHub and out of any single local tree.
  (Local-only work is at risk; pushed work is safe.)
- **Only the Gopher merges branches to `main`**, and only post-Reviewer-pass.

### Working location
- Confirm you are operating in the canonical repo clone, NOT a cloud-synced
  folder (Dropbox, OneDrive, Google Drive, iCloud). Cloud-sync silently
  reverts edits between operations and can corrupt `.git`. If the repo path
  contains a sync-folder name, STOP and flag it.

---

## Verification Discipline (mandatory before every commit)

Before committing, every agent must:

1. **Read the file before editing it.** No blind edits.
2. **Run `git diff --cached`** and read the actual staged diff.
3. **Confirm exactly the intended files are staged** — no more. Check with
   `git diff --cached --stat`.
4. **Never stage `pnpm-lock.yaml` drift or stray untracked files.** If the
   lockfile or an unexpected file shows up staged, unstage it and flag it
   separately.
5. **Confirm scope:** if backend was the task, no frontend files staged, and
   vice versa. `git diff --cached --stat | grep` the directories that should
   NOT appear and confirm nothing comes back.
6. **Write a real, descriptive commit message** scoped to the one change.

After pushing/merging:

7. **Verify on production** (or the relevant deploy target). For a feature,
   that means actually exercising it, not just confirming the deploy is green.

### A useful verification habit
When confirming a find/replace or a scoped change didn't introduce something
unwanted, check that the unwanted strings appear ONLY on removed (`-`) lines
of the diff, never on added (`+`) lines:
`git diff --cached | grep <unwanted-pattern>` → every hit should be a `-` line.

---

## Sub-Agents

Sub-agents are for INVESTIGATION ONLY — read-only work. They map code,
gather context, and report findings in parallel. They NEVER write code,
branch, commit, or push.

- Spawn a sub-agent per independent concern for investigation (e.g. "map the
  report builder", "map the schedule builder", "map the backend onboarding
  logic"). Give each a tight, self-contained brief. The lead agent collects
  and synthesizes — it does not just concatenate.
- Sub-agents follow this discipline (read before report, cite files, stay
  in scope).

IMPLEMENTATION IS SEQUENTIAL. NEVER run parallel implementation agents.
One ticket, one branch, built, verified, reviewed, and merged BEFORE the
next ticket begins. Parallel implementation agents sharing one working tree
commingle their commits across branches and tangle history — this has
happened and cost a full cleanup cycle. The time "saved" by parallelism is
lost to untangling. Sequential is faster in practice because it is clean by
construction. If two tickets seem independent enough to parallelize, resist
it: do them one after the other.

---

## The Standard Workflow (end to end)

1. **Investigate** (if there are unknowns). Investigator(s) — spawning
   sub-agents per slice as needed — read the relevant code and report
   WHAT EXISTS / WHAT'S RELEVANT / WHAT TO WATCH. No code changes.

2. **Ticket** the work. Each ticket: tight scope, named files, explicit
   exclusions, acceptance criteria. One ticket = one branch = one logical change.

3. **Branch.** Builder creates `feat/<id>-<desc>` off `main`.

4. **Build.** Builder implements only the ticket's scope, reading every file
   before editing, importing not copying, following existing patterns.

5. **Self-verify.** Builder runs the verification discipline (diff, scope
   check, no stray files), commits with a real message, and pushes the branch
   to origin.

6. **Review.** Reviewer checks the branch against the full checklist. PASS or
   BLOCK with specific file:line issues. BLOCK → Builder fixes → Reviewer
   re-checks the FULL list.

7. **Merge.** Only after Reviewer PASS, the Gopher merges the branch to `main`,
   confirms the diff is clean (no stray files), pushes, and verifies the deploy.

8. **Confirm in production.** The feature is actually exercised, not just
   assumed live.

Never collapse these steps under time pressure. The collapse is the failure mode.

---

## Anti-Patterns (do not do these)

- **Stacking multiple tickets' changes in one working tree.** Causes commingled
  commits and "is this staged or not?" confusion. One branch per ticket.
- **Running parallel implementation agents in one clone.** They commit
  across each other's branches and tangle history. Implementation is
  strictly sequential — one ticket fully merged before the next starts.
  (Parallel *investigation* sub-agents are fine — they're read-only.)
- **Committing before verifying the diff.** Always `git diff --cached` first.
- **Pushing/merging before Reviewer pass.** The gate exists for a reason.
- **Multiple agents pushing to `main`.** One pusher (Gopher) only.
- **Half-finishing a change and reporting it done.** Especially for
  security/correctness work — if it's not fully done and verified, say so.
- **Copying a working implementation to make a parallel one.** Import/extend
  instead, or flag the duplication.
- **Touching files outside the ticket's scope** "while you're in there." Flag
  it for a separate ticket; don't silently widen scope.
- **Working in a cloud-synced folder.** Confirm the canonical repo path first.
- **Letting `pnpm-lock.yaml` drift or stray files ride along in a commit.**
  Stage exactly what's intended.

---

## Reporting Format (for any agent finishing work)

When done, report:
1. Every file created or modified (and every file deleted).
2. Before/after for each meaningful change.
3. Verification evidence: the diff was checked, scope confirmed, tests/render
   run if applicable, nothing stray staged.
4. Anything flagged for a separate ticket (out-of-scope findings).
5. Branch name and whether it's pushed. Commit status (staged / committed /
   pushed). Never claim "done" for work that is only staged.
