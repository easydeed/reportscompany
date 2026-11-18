# LR-003 dependency upgrade evidence

Base: `4e248ae12c9473b4ea80e8c2d6c923f636f4dc2b` (main). Branch:
`fix/lr-003-patched-dependencies`. Verified locally on 2026-11-16.

## Upgrade

- Next.js: 16.0.7 → 16.4.6. `eslint-config-next` and the bundle analyzer
  now match Next exactly.
- React / React DOM: 19.2.0 → 19.3.1. Shared UI peer ranges match.
- Testing Library React: 14.3.1 resolved → 16.3.3, with its DOM peer declared,
  to support React 19 rather than keep the React 18 peer mismatch.
- Update vulnerable transitive dependencies and Zod within its existing major.
  Both npm and pnpm enforce patched floors for lodash, Babel core,
  browserslist and source-map-js. These overrides intentionally affect both
  consumers; removing them requires rechecking both audits.
- No application behavior, authentication logic, Stripe configuration,
  checkout flow, database schema or worker code changed.

Selection: the [November Next security release](https://nextjs.org/blog/november-2026-security-release)
requires at least 16.4.5 on this line. The npm registry reported 16.4.6 as
current stable, so this uses that release, not the earlier ticket minimum.
Next 16 is covered by the [support policy](https://nextjs.org/support-policy).

## Lockfile consumers and scope

| Consumer | Evidence / treatment |
|---|---|
| `apps/web`, `packages/ui` | Workspace pnpm lock regenerated; frozen install passes. |
| Backend CI | Uses root `npm ci` for browser/render dependencies; root npm lock regenerated in a clean directory, separately validated. |
| Production web | `reportscompany-web`, root `apps/web`, Node 22.x; deployment remains gated on review and merge. |
| `emailpreview`, `reportsbuilder`, `scheduledreports` | Independent root directories outside the workspace. No tracked deployment/workflow consumer found. Their Next 16.0.10 manifests are unchanged; their five-line pnpm files contain no resolutions. They must not be deployed without a separate dependency review. This PR does not claim to patch these standalone design applications. |

## Audits

Raw production-only JSON snapshots are retained beside this file. npm and
pnpm count findings differently; compare each tool with itself.

| Audit | Before | After |
|---|---|---|
| pnpm 9.12.3 `audit --prod --json` | 61: 4 critical, 29 high, 23 moderate, 5 low | 0 |
| npm `audit --omit=dev --package-lock-only --json` | 7 package findings: 1 critical, 6 high | 0 |

The before npm snapshot used `--omit=dev`; the after explicitly reads the
lockfile to avoid reading a pnpm-managed installation. No residual production
advisory needs a reachability waiver. This is an audit snapshot, not a claim
that future advisories cannot appear.

## Verification

Node executable: **22.22.0**, installed outside the repository. pnpm: **9.12.3**.
The system default Node 24 was not used for either production build.

- Original frozen pnpm install and original production build: PASS.
- Updated frozen pnpm install: PASS.
- Updated `next build`: PASS, including TypeScript checking and static pages.
- Web Jest: **31 suites, 698 tests passed** on Node 22.
- Root npm clean install: PASS, 892 packages installed and zero vulnerabilities;
  separate from the pnpm-managed tree using the explicit Node 22 executable.
- Backend checks: market/property templates, reachability, color lint and
  release-gate tests: **240 passed, 54 failed** locally on Windows, both
  before and after. All 54 failing test IDs are identical. Failures include
  Unix date-format directives and platform-sensitive template/lint checks.
  These are not represented as passing. Linux/PostgreSQL release CI must pass.
- No live database tests, provider sends, Stripe calls or card checkout tests.

Builds used localhost API/app URLs, not production endpoints. Self-hosted
fonts and the existing middleware remain unchanged; Next emits its existing
middleware-to-proxy deprecation warning. Migrating that convention is outside
this dependency patch.

## Visual verification limitation

Automatic approval review rejected starting the local Next.js server before
execution. It returned `blocked by policy` without a more specific reason.
No alternate launch mechanism was used. Authenticated rail, report creation,
public report and social/PDF browser smoke checks therefore remain pending;
neither a successful build nor Jest is presented as those screenshots.
Claude subsequently completed the missing checks in its independent
[review of 3140db08](https://github.com/easydeed/reportscompany/pull/297#issuecomment-6932105220):
all six requested pages at 390px and 1280px, no page errors or 5xx, zero pixel
differences, and matching self-hosted fonts. It also rebuilt both versions on
Node 22.23.4 and independently confirmed both updated audits were clean.

## CI correction after Claude's review

The npm lock refresh updated Playwright to 1.65.1. CI installed Chromium in
`chrome-linux64`, but four measurement scripts recognized only `chrome-linux`.
The first Release gate therefore had 4,313 passes and three browser-discovery
errors. All four scripts now accept both layouts without pinning Playwright.
The 16 discovery tests cover each layout, coexistence and absence across all
four scripts. Running them against the original scripts gives eight failures;
the corrected scripts pass all 16. A new exact-head Release gate and Claude's
re-review remain required.

## Rollout

One PR for Claude's cross-review. Do not merge without its recorded PASS and
the exact-head Release gate. After merge, verify the production deployment of
that commit on **reportscompany-web** and smoke-test the routes above without
sending reports or starting checkout. Roll back the whole dependency unit if
needed; do not restore one old lockfile independently.
