# TrendyReports — Agent Skills

This directory contains reusable skills for AI agents working on the TrendyReports codebase. Each skill defines a role, its workflow, and the conventions it must follow.

## Available Skills

| Skill | When to Use |
|-------|-------------|
| `trendyreports-ui-builder` | Frontend changes — Next.js, React, Tailwind, shadcn |
| `trendyreports-backend-builder` | Backend changes — FastAPI, Celery, SQL, Jinja2 |
| `trendyreports-investigator` | Read-only audits, root cause analysis, no edits |
| `trendyreports-gopher` | Database queries, verification SQL, cleanup tasks |
| `trendyreports-reviewer` | Quality gate before commits/deploys |

## Shared References

All skills read these references first:

- `references/architecture.md` — System overview, tech stack, directory structure
- `references/forbidden.md` — What NEVER to change without approval
- `references/conventions.md` — Coding patterns, file locations, naming
- `references/pdf-pipeline.md` — Canonical PDF generation explanation

## Standard Agent Workflow

For most tickets:

```
1. Investigator (optional) — root cause / audit
   ↓
2. Builder (UI or Backend) — implement the fix
   ↓
3. Gopher (if DB involved) — run verification SQL
   ↓
4. Reviewer — quality gate
   ↓
5. User pushes to main
```

For urgent hotfixes, you can skip steps 1, 3, and 4 — but always at least run the Reviewer before deploy.

## How to Trigger a Skill

In Cursor or another agent runner, paste the ticket and tell the agent which skill to use. The skill's frontmatter description tells the agent when to apply it.

Example ticket header:
```
You are the UI Builder agent for TrendyReports.

Read .cursor/rules/skills/trendyreports-ui-builder/SKILL.md.

Ticket: PRICING-UI-RENAME — ...
```

## Skill Composition

Skills can be combined for complex tickets:

```
Ticket: Fix the schedules crash and rename Starter to Growth.

→ Use trendyreports-investigator first (find the schedules crash cause)
→ Then trendyreports-backend-builder (fix the layout backend if needed)
→ Then trendyreports-ui-builder (rename Starter → Growth in copy)
→ Then trendyreports-reviewer (gate before push)
```

## Updating Skills

When a new convention emerges (e.g., "always invalidate React Query after mutations"):

1. Update the relevant skill's SKILL.md
2. Or add it to `references/conventions.md` if it applies broadly
3. Commit the update

The skills evolve with the codebase. Treat them as living documentation.

## Skill File Format

Each skill follows this structure:

```
trendyreports-{role}/
├── SKILL.md           # Role definition, workflow, rules
└── references/        # (optional) Role-specific deep dives
    └── *.md
```

The shared `references/` at this directory level is read by ALL skills.

## What Skills Are NOT

- They are NOT a replacement for code review by a human
- They are NOT a substitute for testing
- They do NOT eliminate the need for clear tickets
- They CANNOT prevent every bug — they reduce common mistakes
