# Release review PASS checklist

- Identify the exact reviewed PR head and scope; confirm no stray files or unreviewed changes.
- Inspect changes to .github/workflows/** and scripts/release_gate.py explicitly. A PR can edit the gate it is judged by because those files execute from its own merge tree; a green gate cannot prove its own integrity.
- For a gate change, the independent PASS comment must explicitly state that the reviewer checked gate logic, selection, fail-closed results, permissions and evidence. Do not accept green checks alone.
- Check applicable tests, negative proof and unchanged cross-boundary contracts, including backend tests that read web sources.
- Confirm the current-head Release gate passes and the branch satisfies main protection. A cancelled older run or an old-head PASS is not a replacement.
- Record cross-agent PASS as a PR comment before ordinary merge. Native GitHub approval count is zero by Jerry's decision; never imply GitHub enforces comment-based independence.
- Jerry alone handles an emergency; record the reason, exact SHA and method, obtain independent review within 24 hours, and restore any temporary rule change.
