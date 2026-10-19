# Dead Code Register

**Last updated:** 2026-10-19 (`docs/d196-d198-dead-admin-tree`)

Three lists: what was removed, what is dead and **not yet** removed, and what **looks** dead but is live. The third is the point of this document — it exists so the same code is not re-litigated by the next person who greps for importers and finds none. The second exists because establishing that something is dead and deleting it are separate pieces of work, and the gap between them is where a deletion deadline quietly expires.

## The standard applied here

A file is dead only when **all three** are true:

1. **Zero importers** — no `import`/`from` reference resolves to it.
2. **Zero route references** — no router, page, or config points at it.
3. **Zero runtime string construction** — its name or path never appears as a *string* that something builds a URL or a filesystem path from.

The third is the one that matters. Searching only for imports is how `/print/[runId]` came to be declared removed in two separate documents while the worker was still constructing URLs against it. **Grep for the filename as a string, not just as an import.**

---

## Removed

| What | Size | Proof of death |
|---|---|---|
| `apps/web/components/v0-report-builder/` (6 files) | 1,317 lines | `git grep "v0-report-builder"` across the whole repo: no import, no route reference, no runtime string, no `dynamic()` import. Symbol names such as `ReportBuilderState` and `AUDIENCE_FILTER_PRESETS` do appear elsewhere, but those are **separate definitions in a different directory** — `apps/web/components/report-builder/index.tsx:19` imports them locally as `"./types"`. |
| `_intake/real-estate-saa-s.zip`, `_intake/website-updates.zip`, `_intake/real-estate-email-template (1).zip` | ~9.9 MB | No reference anywhere to `_intake`, to the archive names, or to any path inside them. `.gitignore:29` already lists `_intake/`; these predate that rule, and gitignore does not untrack what is already committed. Two of them contain copies of files deleted in Phase 1 — a Phase 1 grep matched *inside the binaries*, which is noise, not a reference. |

Both remain in git history if anything needs recovering.

**Where the live market-report wizard lives, since `v0-report-builder` is gone:** `apps/web/components/unified-wizard/`, mounted by `apps/web/app/app/reports/new/page.tsx:6`, `app/app/schedules/new/page.tsx`, and `app/app/schedules/[id]/edit/page.tsx`.

---

## Looks dead — IS LIVE. Do not delete.

### `apps/web/app/print/[runId]/page.tsx` and everything it loads

**Also covers:** `apps/web/lib/templates.ts` and the seven `apps/web/templates/trendy-*.html` files.

**Why it looks dead.** The market-report PDF pipeline renders server-side in the worker now. `apps/worker/src/worker/tasks.py:1093-1099` says so in as many words: *"Always render via the new MarketReportBuilder … we never fall back to it."* No page in the application links to `/print/[runId]`. A P4-T3 cleanup ticket in a since-deleted playbook listed all of this as legacy.

**Why it is live anyway.**

- `apps/worker/src/worker/pdf_engine.py:83` and `:163` construct `${PRINT_BASE}/print/{run_id}` **at runtime**, in `render_pdf_playwright` and `render_pdf_pdfshift` respectively. That is the path taken whenever `render_pdf` is called without `html_content`.
- `PRINT_BASE` is a live environment variable (`pdf_engine.py:33`, plus both `ENV_TEMPLATE.md` files).
- `apps/api/src/api/routes/report_data.py:21` documents this page as the consumer of `/v1/reports/{id}/data`, and `INTERNAL_RENDER_TOKEN` (`apps/api/src/api/settings.py`) exists specifically so this page can fetch report data server-side.
- The page maps all seven templates **by filename string** at `page.tsx:122-131` (`'trendy-market-snapshot.html'`, …) and loads them from disk. An import-only search finds no reference to those HTML files at all.

**The honest nuance,** so nobody has to re-derive it: all three current callers of `render_pdf` pass `html_content=` — `tasks.py:1203` (market), `tasks.py:1795` (consumer reports), `property_tasks/property_report.py:474` (property). So the print-URL branch is **not exercised by any known caller today**. It is still constructed at runtime, still reachable by URL, and still the documented fallback. Unexercised is not the same as dead, and deleting it would silently remove the fallback rather than fail loudly.

**If you want this gone,** the work is: remove the URL branch from `render_pdf_playwright`/`render_pdf_pdfshift` first, confirm nothing calls `render_pdf` without `html_content`, retire `PRINT_BASE` and `INTERNAL_RENDER_TOKEN`, *then* delete the route, `lib/templates.ts` and the seven HTML files. That is a behaviour change, not a cleanup, and it belongs in its own ticket.

Both files now carry a `NOT DEAD CODE` comment pointing here.

---

---

## Dead, established, NOT YET REMOVED

One entry, and it is here rather than under **Removed** because the deletion is a bigger sweep than
it looks.

### `apps/web/app/admin/**` — 15 route files, a standalone admin panel superseded by `/app/admin`

**Filed as D-197.** Its own first line has said so since launch:

    // DEPRECATED: This standalone admin panel is superseded by /app/admin
    // Safe to delete after verifying all pages migrated (see ADMIN-MIGRATE tickets)
    // Target deletion: 1 week after launch

There are no ADMIN-MIGRATE tickets in this repository, so the condition on its own deletion cannot
be checked from here. The deadline was five months ago.

**Against the three conditions above:**

| | |
|---|---|
| 1. Zero importers | **holds** — nothing outside the tree resolves an import into it |
| 2. Zero route references | **one**: `app/access-denied/page.tsx:12` navigates to `/admin/login` |
| 3. Zero runtime string construction | **holds** — repo-wide, nothing in `apps/api`, `apps/worker`, `next.config.ts` (which has no rewrites at all) or any email builds a `/admin` page URL |

Condition 2's single reference points at a **URL**, not at a file: `middleware.ts` redirects every
`/admin/*` to `/app/admin/*` before any auth check, so `/admin/login` resolves to `/app/admin` and
then, with no session, to `/login`. **Nothing reaches the files.** Every one of the tree's 13 URLs
has a live counterpart under `/app/admin`, so the shadowing is total and nothing 404s.

**This is the weaker kind of deadness, and the distinction is the point of recording it.** D-131's
templates are dead because nothing names them. This tree is dead because something *intercepts* it
— one `pathname.replace()` and one matcher entry. Narrowing that matcher is a one-token edit, and
D-196 is a recorded instance of exactly that edit being left in a working tree by accident.

**Why not deleted yet:**

1. It orphans `apps/web/components/admin/` (7 files, already consumerless) and leaves
   `packages/ui`'s parallel copies with no caller — a 20-plus-file sweep across three packages,
   needing its own proof.
2. Its layout holds **the only correct server-side admin verification in the codebase** —
   `createServerApi().get('/v1/me')` then `data.is_platform_admin`, read off the API's response
   rather than a client-supplied token. `app/app/admin/**` has no layout of its own and no file
   under it mentions `is_platform_admin`; its only gate is the middleware's unverified decode
   (D-194). The pattern is quoted verbatim on D-197 so it survives the deletion.
3. **Do not de-tint it.** It holds 19 of the 46 remaining `bg-indigo-*` surfaces and
   `tests/test_tint_answer_is_current.py` records it as out of scope deliberately — the same
   reasoning D-131's gate states, so nobody spends an afternoon restyling a panel that renders for
   nobody.

**When it is deleted, keep the redirect.** `middleware.ts`'s `/admin` → `/app/admin` remap is what
makes old bookmarks and that one `access-denied` link resolve. It is independent of whether the
files exist.

## Candidates not acted on

| Candidate | Why it was left |
|---|---|
| `_intake/` extracted directories — including a complete second Next.js application at `_intake/real-estate-saas/` | Unreferenced, and `.gitignore:29` says the directory should not be tracked at all. But removing a vendored application is a larger decision than a cleanup ticket should make unilaterally. Needs an explicit call. |
| `apps/web/components/report-builder/` | Distinct from the deleted `v0-report-builder/`. Not on the Phase 5 candidate list and not investigated. Its similar name is exactly the sort of thing that invites a careless deletion — check it properly before touching it. |
| `apps/web/components/v0/`, `apps/web/components/v0-styling/` | **Both assessed since.** `components/v0/` was dead and was **deleted** (D-050, 2026-10-18). `components/v0-styling/` is **LIVE** — `AffiliateDashboardShell.tsx` is imported by `app/app/affiliate/page.tsx` and renders the affiliate dashboard. The directory name is the only thing about it that suggests otherwise. |
| `apps/web/components/admin/` — 7 files | **No consumer outside itself**, and `packages/ui/src/index.ts:16-19` re-exports a parallel set of copies from `packages/ui/src/components/admin/`. Left because it is the orphan set that deleting `app/admin/**` creates, and the two should be assessed in one pass rather than one of them leaving first. See D-197. |
