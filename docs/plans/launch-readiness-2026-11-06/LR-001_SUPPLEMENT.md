# LR-001 supplementary read-only baseline

Observed November 6, 2026 against mr-staging-db. No migration, account edit, role/policy change, provider send or billing mutation. These observations supplement the earlier investigator rows; they do not erase their source evidence or prove live customer journeys.

## Actual plan catalog

Query: `SELECT plan_slug, monthly_report_limit, market_reports_limit, schedules_limit, property_reports_per_month FROM plans ORDER BY plan_slug;`

| plan_slug | monthly_report_limit | market_reports_limit | schedules_limit | property_reports_per_month |
| --- | ---: | ---: | ---: | ---: |
| affiliate | 5000 | 5000 | 99999 | 100 |
| free | 3 | 3 | 1 | 1 |
| pro | 99999 | 99999 | 99999 | 10 |
| solo | 500 | 25 | 3 | 5 |
| sponsored_free | 3 | 3 | 1 | 1 |
| starter | 25 | 25 | 3 | 3 |
| team | 1000 | 99999 | 99999 | 25 |
| trial | 3 | 3 | 1 | 1 |

D-004/D-051 now have deployed catalog evidence beyond the source-only investigation. Solo and Team legacy/product limits differ. Starter's property allowance is 3 and Pro's is 10, unlike migration 0051's initial 5/25. These may be intentional operator choices: do not overwrite them by replaying seeds or treating a migration literal as current commercial policy. LR-032 needs an authoritative catalog decision.

## Free account overrides

Query uses the already-authorized four override columns, counts only and no contact details:

```sql
SELECT a.plan_slug, count(*) AS accounts,
       count(*) FILTER (
         WHERE a.market_reports_limit_override IS NOT NULL
            OR a.monthly_report_limit_override IS NOT NULL
            OR a.schedules_limit_override IS NOT NULL
            OR a.property_reports_limit_override IS NOT NULL
       ) AS with_override
FROM accounts a
WHERE a.plan_slug IN ('free','sponsored_free')
GROUP BY 1 ORDER BY 1;
```

| plan_slug | accounts | with_override |
| --- | ---: | ---: |
| free | 17 | 1 |
| sponsored_free | 17 | 0 |

D-301's override still exists. Its identity/intent remains unverified; no customer allowance is changed. The original row's claim that production presence was not inspected is now supplemented by this count.

## Roles and policies

Read-only inspection connection: `mr_staging_db_user`, superuser false, bypass_rls false. This identifies the inspection connection, not independently the deployed API/worker connection identity.

| Table | Owner | RLS enabled | RLS forced |
| --- | --- | --- | --- |
| accounts | mr_staging_db_user | false | false |
| property_reports | mr_staging_db_user | true | false |
| report_generations | mr_staging_db_user | true | false |
| schedules | mr_staging_db_user | true | false |

The latter three each expose one ALL/public policy: account_id equals app.current_account_id, OR app.current_user_role equals ADMIN. No company-descendant policy appeared in this inspected set. This supports the D-014/D-274 policy inventory; it does not demonstrate an unauthorized request or justify changing production roles before restricted-role integration proof.

## Release-control identity constraint

GitHub repository permissions show admin capability for the current operator; collaborator inventory returned only `easydeed`. Both PR #273 and #274 are authored by `easydeed`, despite separate agent lanes. [GitHub disallows author self-approval](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews).

LR-002 must resolve the distinct reviewer identity before enabling a native required-approval rule. A CI-only gate with recorded cross-agent review is an explicitly weaker alternative, not equivalent independent-identity enforcement. No rule has been changed, no bypass has been used, and no reviewer access has been granted. Jerry has been asked which separate GitHub identity should supply approvals.

Backend/frontend workflows and DB fixture guards were read for preflight. Workflows currently use top-level path filters; an always-running required gate must avoid skipped-check deadlocks and classify lockfiles/runtime/shared package changes. DB CI still names postgres:16 and the shared db_session fixture can skip on missing/unreachable DB. These remain LR-002/LR-031 implementation, not fixes in this evidence PR.

## Parallel review

Codex reviewed Claude LR-019 at `6a33682a` and posted a [BLOCK](https://github.com/easydeed/reportscompany/pull/274#issuecomment-6700547374). An isolated fake-provider experiment demonstrated acceptance followed by lost response being classified retryable. The fix must honor the approved unknown-text no-auto-resend policy before merge. No real provider was invoked. The delivered-state design remains in Claude's lane; Codex made no worker edits.
