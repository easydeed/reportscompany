# Dead Code Register

**Last updated:** 2026-08-18 (Phase 5, `chore/p5-dead-code`)

Two lists: what was removed, and what **looks** dead but is live. The second list is the point of this document — it exists so the same code is not re-litigated by the next person who greps for importers and finds none.

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

## Candidates not acted on

| Candidate | Why it was left |
|---|---|
| `_intake/` extracted directories — including a complete second Next.js application at `_intake/real-estate-saas/` | Unreferenced, and `.gitignore:29` says the directory should not be tracked at all. But removing a vendored application is a larger decision than a cleanup ticket should make unilaterally. Needs an explicit call. |
| `apps/web/components/report-builder/` | Distinct from the deleted `v0-report-builder/`. Not on the Phase 5 candidate list and not investigated. Its similar name is exactly the sort of thing that invites a careless deletion — check it properly before touching it. |
| `apps/web/components/v0/`, `apps/web/components/v0-styling/` | Flagged in the 2026-08-17 docs audit as undocumented, never assessed for liveness. |
