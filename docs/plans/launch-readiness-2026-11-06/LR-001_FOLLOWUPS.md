# LR-001 proposed historical-backlog follow-ups

Status: deferred until after the pilot by Jerry, November 9. Owner: Codex. These groups remain an inventory, not an approved implementation expansion. Exceptions approved for the pilot are D-188/D-106/D-168 numeric repairs (Claude after LR-018) and the D-014/D-274 read-only production hierarchy/RLS check (Codex). Any newly confirmed cross-account exposure or wrong number follows the pilot stop rule. Original LR-001–LR-031 work remains in its reviewed lanes.

## Provisional estimate

| Scope | Focused hours |
| --- | ---: |
| Reviewed original LR-001–LR-031 | 164–282 |
| Proposed additional LR-032–LR-051 | 181–287 |
| All proposed repair/discovery work | 345–569 |
| With 20 percent reserve | 414–682.8 |

The original 220–270-hour working forecast remains for the original reviewed program only. It cannot be presented as the cost of repairing the entire historical backlog. This broader range is a proposal, not an approved replacement forecast. It excludes unchosen new features (new sharing, sponsorship acceptance, newsletter infrastructure or full live previews), provider waiting and pilot elapsed time. Reproduce/triage before committing to the added budget. Do not add individual row estimates on top of this consolidated estimate.

Each group needs a concrete file list, sequential atomic branch/PR slices, acceptance fixtures and the other lane's approval before implementation. No simultaneous edits of shared files or bypass of LR-001/LR-002 gates is authorized here. Lane ownership below is proposed and must preserve the reviewed lane sequences. LR-030 includes final cross-system acceptance; each estimate includes its own targeted regression proof, not a second full acceptance exercise.

## LR-032 — Plan catalog and displayed allowances

**Defects:** D-004 D-051 D-204 D-316. **Hours:** 8–12. **Gate:** PAID (proposed, affected feature only). **Owner/dependencies:** Codex; after LR-013/LR-015.

**Scope:** Reconcile supported slugs, legacy/product limits and billing-card claims against the authoritative catalog. Preserve approved overrides; never invent a fallback allowance.

**Acceptance/boundary:** Capture plan data read-only; test missing/zero limits and each displayed entitlement/price. No live price or allowance edits without the catalog decision.

## LR-033 — Verified web sessions and usable auth failures

**Defects:** D-013 D-194 D-266 D-269 D-270. **Hours:** 10–16. **Gate:** PILOT (proposed, affected feature only). **Owner/dependencies:** Codex; after LR-009, coordinate LR-027.

**Scope:** Verify server-side session/role routing; distinguish verification outage from revoked credentials; validate local login return URLs; remove redundant cookie assignment only after a browser contract test.

**Acceptance/boundary:** Unsigned/tampered claims do not authorize a shell; outage fails closed without masquerading as bad credentials; return URL cannot redirect off-site. Session duration remains an explicit decision.

## LR-034 — Company hierarchy under enforced RLS

**Defects:** D-014 D-274. **Hours:** 16–24. **Gate:** PILOT (proposed, affected feature only). **Owner/dependencies:** Codex; after LR-031; coordinate company route ownership.

**Scope:** Inspect production roles/policies read-only, then design the minimum hierarchy policy and non-bypass connection behavior. Source mismatch alone does not prove a deployed leak.

**Acceptance/boundary:** Real restricted-role tests permit the intended company hierarchy and refuse another company's data. Any migration claims the single migration slot; no production role change hidden in this estimate.

## LR-035 — Safe deployment configuration and render endpoints

**Defects:** D-027 D-028 D-030 D-034 D-355. **Hours:** 10–16. **Gate:** PUBLIC (proposed, affected feature only). **Owner/dependencies:** Codex; after LR-002/LR-003.

**Scope:** Validate production vendor/origin settings, align PDF key contracts and generated links, define narrowly scoped preview CORS and inventory obsolete adapters before deletion.

**Acceptance/boundary:** Missing production configuration fails clearly; rendered links use the chosen origin; allowed/unrelated-origin preflights tested; no UAT host accepted by accidental default. Inspect config without printing secrets.

## LR-036 — Worker child-loss recovery proof

**Defects:** D-068. **Hours:** 6–10. **Gate:** PILOT (proposed, affected feature only). **Owner/dependencies:** Claude; after LR-020/LR-023.

**Scope:** Run an isolated broker/worker experiment killing a child while its parent survives; define bounded redelivery and poison-job handling.

**Acceptance/boundary:** Persisted work reaches an honest recoverable or terminal outcome; no duplicate text or unbounded poison redelivery. Do not simply enable reject-on-worker-lost.

## LR-037 — MLS parameter contract and boundary protection

**Defects:** D-075 D-084. **Hours:** 4–6. **Gate:** PILOT (proposed, affected feature only). **Owner/dependencies:** Claude; after LR-018; bounded provider access.

**Scope:** Share one recognized-parameter contract and test semantic date boundaries. Preserve client filtering until current feed behavior is proven.

**Acceptance/boundary:** Capture both boundary dates and returned close dates without customer PII; unknown local parameter rejected. Live vendor probe uses approved credentials and bounded read-only calls.

## LR-038 — Mutation refusal and error surfaces

**Defects:** D-082 D-213 D-329. **Hours:** 8–12. **Gate:** PILOT (proposed, affected feature only). **Owner/dependencies:** Codex; after Claude LR-024 and LR-015.

**Scope:** Inventory current failing mutation handlers, normalize structured errors and show property-wizard verification/quota refusals. LR-024 already pays for unified-wizard repair.

**Acceptance/boundary:** Injected validation, quota, server and network refusals leave visible actionable errors without duplicate submission. Recount current handlers rather than claiming old counts remain accurate.

## LR-039 — Brand settings persistence and fallback contract

**Defects:** D-260 D-271 D-272 D-279 D-337 D-345. **Hours:** 10–16. **Gate:** PILOT (proposed, affected feature only). **Owner/dependencies:** Codex; after LR-007; coordinate Claude report modules.

**Scope:** Repair independent-rep save/read contract and tagline/contact-field persistence. Decide intended new-account fallback colors and supported funnel settings before changing stored colors or visible layout.

**Acceptance/boundary:** Save/reload/render fixtures agree for regular, independent rep and company-owned rep. Do not recolor existing brands automatically or save an unsupported contact-email field.

## LR-040 — Schedule editing, history and delivery visibility

**Defects:** D-236 D-328 D-327 D-335 D-252 D-331 D-333. **Hours:** 18–28. **Gate:** PUBLIC (proposed, affected feature only). **Owner/dependencies:** Codex UI and Claude persistence in separate reviewed PRs; after LR-016/LR-023/LR-024.

**Scope:** Edit the identified schedule instead of creating another; populate history/resolved recipients/cadence; expose skipped suppression and truthful allowance copy. No new Run Now endpoint without product approval.

**Acceptance/boundary:** Editing leaves one row; existing settings load; mixed legacy recipients render; all-suppressed send is visibly skipped rather than falsely delivered. Separate sub-PRs share one bounded ticket budget.

## LR-041 — City handoff and onboarding disposition

**Defects:** D-230 D-268 D-254 D-326. **Hours:** 6–10. **Gate:** PUBLIC (proposed, affected feature only). **Owner/dependencies:** Codex; Jerry decides role-specific onboarding first; after LR-026 fixtures.

**Scope:** Make the landing city promise true through signup/onboarding. Explicitly remount or remove unused onboarding only after role guidance requirements are agreed.

**Acceptance/boundary:** A city survives the full flow for an approved fixture; role guidance does not disappear unintentionally. One city-handoff implementation, not separate charges for D-230/D-268.

## LR-042 — Report data absence and fixture contracts

**Defects:** D-106 D-135 D-168 D-173 D-229 D-242 D-114 D-122 D-142 D-149 D-187. **Hours:** 20–32. **Gate:** PILOT (proposed, affected feature only). **Owner/dependencies:** Claude; after LR-018; input/display decisions first.

**Scope:** Preserve missing versus real zero comp values; settle bathroom fields, preview data and orphan metrics/spec tests. Diagnose the sale-ratio outlier before changing arithmetic. Address missing/broken photos and dropped-section disclosure.

**Acceptance/boundary:** Both absent and genuine-zero fixtures produce truthful output; recorded sale/lease outliers trace to rows; shared sample data reflects supported sections. This is not authorization to invent missing producers or fill unavailable facts.

## LR-043 — Preview, report labels and remaining presentation defects

**Defects:** D-162 D-214 D-245 D-246 D-258 D-259 D-261 D-323 D-262 D-264 D-265 D-294 D-253 D-250 D-237 D-238 D-240 D-251 D-338. **Hours:** 18–28. **Gate:** PUBLIC (proposed, affected feature only). **Owner/dependencies:** Codex web/Claude render owners, separate small PRs; after LR-024/LR-025.

**Scope:** Unify display names; correct window/count/progress labels and theme fallback; repair sample timeout; inspect current preview assets before refresh; fix recipient badge, ZIP contract and schedule layout. Compare React email previews with real fixture output.

**Acceptance/boundary:** Render affected initial/selected/error states and current report kinds; injected timeout preserves intended failure; no retired generator or vendor-cost assumption. Full live template-preview replacement requires a separate decision if the labeled sketch is retained.

## LR-044 — Company and reporting data semantics

**Defects:** D-297 D-299 D-283 D-321 D-319. **Hours:** 10–16. **Gate:** PUBLIC (proposed, affected feature only). **Owner/dependencies:** Codex; after LR-031; seat deactivation policy first.

**Scope:** Agree deactivation/reactivation seat semantics, include property-only activity, represent zero-base growth honestly, use authority-aware labels and consistent UTC feeds.

**Acceptance/boundary:** Restricted fixtures cover property-only activity, zero-to-positive growth and viewers; real admin deactivation respects the approved seat policy; agent/admin timestamps have explicit UTC.

## LR-045 — Lead identity, attribution and notification contracts

**Defects:** D-325 D-336 D-340 D-341 D-344 D-322. **Hours:** 10–16. **Gate:** PILOT (proposed, affected feature only). **Owner/dependencies:** Codex web/API; Claude notification edges; after LR-021/LR-025; product decisions first.

**Scope:** Persist signup identity, guard nullable leads, distinguish QR/direct attribution and repair test-email links. Decide new every-lead email and SMS signature requirements before adding a channel.

**Acceptance/boundary:** Nullable and CMA-source leads render; signup signature uses entered identity; no owner-name fallback. New channel tests are isolated and consent-aware; no production test send is implicit.

## LR-046 — Company-read access audit

**Defects:** D-012. **Hours:** 6–10. **Gate:** PUBLIC (proposed, affected feature only). **Owner/dependencies:** Codex; after LR-034; retention/access policy first.

**Scope:** Define bounded reader identity, accessed account/resource and authorized audit access for company report/schedule reads.

**Acceptance/boundary:** Cross-company reads are refused and authorized reads have auditable scope; no property/contact payload in audit events. Schema work uses the single migration slot.

## LR-047 — Substantiated marketing and sponsor-brand promises

**Defects:** D-221 D-231 D-232 D-233 D-234 D-275 D-278. **Hours:** 4–8. **Gate:** PUBLIC (proposed, affected feature only). **Owner/dependencies:** Codex; Jerry chooses removal/substantiation; after LR-025.

**Scope:** Resolve unsupported newsletter, city/coverage and adjacent-logo/cascade claims against the existing product. Default proposed scope is truthful copy/removal, not new MLS integrations, newsletter platform or cobranding feature.

**Acceptance/boundary:** Every surviving factual claim has an evidence pointer; current sponsored output and advertised branding agree. Any new product capability is separately estimated.

## LR-048 — Proven-unreachable code and shared UI cleanup

**Defects:** D-197 D-198 D-295 D-298 D-176. **Hours:** 8–12. **Gate:** PUBLIC (proposed, affected feature only). **Owner/dependencies:** Codex web/Claude worker owners, separate PRs; after LR-003.

**Scope:** Inventory imports/routes/string/dynamic references before deleting legacy modules; consolidate the remaining UsageBars; remove unused title-size context while preserving active contrast math.

**Acceptance/boundary:** Reference evidence precedes deletion; redirects and verified auth survive; typecheck/source tests pass. Naming convention may be accepted instead of building structural enforcement.

## LR-049 — Render-harness determinism

**Defects:** D-235 D-286. **Hours:** 3–5. **Gate:** PUBLIC (proposed, affected feature only). **Owner/dependencies:** Codex; after LR-026 safe harness.

**Scope:** Repeat controlled same-SHA route renders under load and validate sentinel/write synchronization. D-286 is already a source-closure candidate, not a proven current race.

**Acceptance/boundary:** Repeated healthy fixture runs are stable; deliberately unhealthy route fails. No arbitrary sleep increase substitutes for a measured readiness condition.

## LR-050 — Historical tenancy and override inventory

**Defects:** D-023 D-301. **Hours:** 2–4. **Gate:** PROCESS (proposed, affected feature only). **Owner/dependencies:** Codex read-only; Jerry confirms assignment/override intent.

**Scope:** Identify affected promotion/Free-override rows with bounded non-contact queries and check intent.

**Acceptance/boundary:** Record approved exceptions versus defects; change no allowances, account types or customer data. Data correction would require its own reviewed procedure.

## LR-051 — Unresolved product-boundary decisions

**Defects:** D-239 D-244 D-248 D-249 D-307 D-346. **Hours:** 4–6. **Gate:** PROCESS (proposed, affected feature only). **Owner/dependencies:** Jerry decisions; Codex records contracts; coordinate Claude LR-018.

**Scope:** Decide route-locked modes, active-comps default, property audience/sharing, sponsored branding access, multi-user report identity and existing-agent sponsorship acceptance.

**Acceptance/boundary:** Record decision, impact and owner for each; no new sharing/sponsorship feature is priced here. Subsequent feature builds require separate scoped estimates.

## Existing-ticket and closure disposition

D-036/D-096/D-339/D-347 remain within LR-027/LR-029/LR-006/LR-016. D-330 and the unified portion of D-329 remain LR-024; property refusal UX is LR-038. D-332 is LR-015/LR-023 and must match the existing-schedules policy. D-343's PDF/expiry promises must be explicitly included in LR-025. D-191 has fresh hosted-CI baseline evidence in the reconciliation; mandatory checks remain LR-002.

After Claude's corrections there are 15 superseded-source candidates and three partial rows. D-047 remains current: its paid-tier AI promise survives on the billing page. D-188 is a current numeric pilot blocker; D-267 is a current AuthFrame inconsistency deferred beyond the pilot. D-097's legacy-print path, D-122's inaccessible avatar and D-123's empty map/street frames are explicit residuals. D-286 still needs loaded repeatability proof. No candidate is closed automatically by this document.
