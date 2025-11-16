# Release Check Workflow

**Purpose**: One-button validation of all test suites before shipping major changes.

---

## How to Use

### GitHub UI (Recommended)
1. Go to: https://github.com/easydeed/reportscompany/actions/workflows/release-check.yml
2. Click **"Run workflow"** button
3. Select branch: `main` (or your feature branch)
4. Click **"Run workflow"** (green button)

### Wait for Results
The workflow runs 3 jobs in sequence:
1. **backend-tests** (~2-5 min): pytest for API + Worker
2. **frontend-tests** (~3-5 min): Jest + build for web app
3. **e2e-tests** (~5-10 min): Playwright E2E tests against staging

**Total time**: ~10-20 minutes

---

## What It Checks

### ✅ Backend Tests
- **API Tests**: Routes, auth, plan limits, billing, branding, schedules
- **Worker Tests**: Report builders, email formatting, template mapping
- **Total**: 95+ tests

### ✅ Frontend Tests
- **Unit Tests**: React components (AccountSwitcher, PlanPage, Affiliate)
- **Template Mapping**: Builders for all 7 report types
- **Build**: Vercel production build check
- **Total**: 70+ tests

### ✅ E2E Tests
- **Auth Flow**: Login, logout, cookie persistence
- **Plan Page**: Usage display, Stripe buttons
- **Affiliate Dashboard**: Sponsored accounts, invite flow
- **Schedules**: Create, edit, list schedules
- **Total**: 17+ tests

---

## When to Run

### Required Before:
- ✅ Merging to `main`
- ✅ Deploying to production
- ✅ Releasing a new version/tag

### Optional For:
- Large feature branches (to catch regressions early)
- After major dependency updates
- Before customer demos

---

## Interpreting Results

### All Green ✅
**Safe to ship!** All tests passed across backend, frontend, and E2E.

### One or More Red ❌
**Do NOT ship.** Click into the failed job to see:
- Which test(s) failed
- Error messages and stack traces
- For E2E failures: Playwright screenshots/videos in artifacts

Fix the failures and re-run the workflow.

---

## Secrets Required

The E2E tests need these GitHub secrets configured:

| Secret Name | Description | Recommended Value |
|-------------|-------------|-------------------|
| `E2E_BASE_URL` | Staging URL | `https://reportscompany-web.vercel.app` |
| `E2E_REGULAR_EMAIL` | Regular agent test account | `agent-pro@trendyreports-demo.com` |
| `E2E_REGULAR_PASSWORD` | Regular agent password | `DemoAgent123!` |
| `E2E_AFFILIATE_EMAIL` | Affiliate test account | `affiliate@trendyreports-demo.com` |
| `E2E_AFFILIATE_PASSWORD` | Affiliate password | `DemoAff123!` |

**Note**: These map to canonical demo accounts. See `docs/DEMO_ACCOUNTS.md` for details.

To add/update secrets:
1. Go to: https://github.com/easydeed/reportscompany/settings/secrets/actions
2. Click **"New repository secret"** or edit existing
3. Add the secret name and value
4. Click **"Add secret"**

---

## Troubleshooting

### "backend-tests failed"
- Check if API dependencies are installed correctly
- Verify pytest can find `apps/api/tests/`
- Look for import errors or missing env vars

### "frontend-tests failed"
- Check if pnpm installed all workspace dependencies
- Verify Jest config is correct in `apps/web/jest.config.ts`
- Look for TypeScript errors or missing mocks

### "e2e-tests failed"
- Check if staging/vercel deployment is healthy
- Verify E2E credentials are correct in secrets
- Download Playwright report artifact for screenshots/video

---

## Local Equivalent

To run the same checks locally (before pushing):

```bash
# Backend tests
pytest apps/api/tests
pytest apps/worker/tests

# Frontend tests
pnpm --filter web test
pnpm --filter web build

# E2E tests (optional, requires running services)
E2E_BASE_URL=http://localhost:3000 npx playwright test
```

---

## Maintenance

### Adding New Tests
- Backend: Add `test_*.py` files to `apps/api/tests/` or `apps/worker/tests/`
- Frontend: Add `*.test.tsx` files to `apps/web/__tests__/`
- E2E: Add `*.spec.ts` files to `e2e/` (root)

All new tests will automatically run in the release check workflow.

### Updating Dependencies
- If you update Python deps: Update `requirements.txt`
- If you update Node deps: Update `package.json` + run `pnpm install`
- The workflow will pick up changes automatically

---

**Last Updated**: November 15, 2025  
**Maintained By**: Development Team

