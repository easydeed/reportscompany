"""The release check must reject missing proof, without stranding unrelated PRs."""
import itertools
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.release_gate import changed_paths, classify_paths, gate_errors

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("path,expected", [
    ("apps/api/poetry.lock", (True, False)),
    ("apps/worker/src/worker/tasks.py", (True, False)),
    ("apps/web/app/page.tsx", (True, True)),
    ("apps/web/templates/social/story.html", (True, True)),
    ("tests/test_example.py", (True, False)),
    ("db/migrations/0064_example.sql", (True, False)),
    ("scripts/render_routes.mjs", (True, False)),
    ("tools/fixture.py", (True, False)),
    ("libs/shared/src/ids.py", (True, False)),
    ("docs/DEFECT_LIST.md", (True, False)),
    ("docs/runbooks/example.md", (True, False)),
    ("README.md", (False, False)),
    ("package.json", (True, True)),
    ("package-lock.json", (True, True)),
    ("pnpm-lock.yaml", (True, True)),
    ("pnpm-workspace.yaml", (True, True)),
    (".nvmrc", (True, True)),
    (".npmrc", (True, True)),
    ("packages/api-client/src/index.ts", (True, True)),
    ("e2e/stripe.spec.ts", (False, True)),
    ("playwright.config.ts", (False, True)),
    (".github/workflows/e2e.yml", (True, True)),
    ("scripts/release_gate.py", (True, True)),
    ("tests/test_release_gate.py", (True, True)),
    ("docker-compose.yml", (True, False)),
    (".python-version", (True, False)),
    ("unclassified/config.toml", (True, True)),
])
def test_trigger_families(path, expected):
    result = classify_paths([path])
    assert (result["backend"], result["frontend"]) == expected


def test_incomplete_comparison_and_mixed_changes():
    assert classify_paths(None) == {"backend": True, "frontend": True}
    assert classify_paths(["apps/api/a.py", "apps/web/a.ts"]) == classify_paths(None)


@pytest.mark.parametrize("path", [
    "apps/web/components/mobile-report/MobileReportViewer.tsx",
    "apps/web/app/api/proxy/v1/reports/[id]/route.ts",
    "apps/web/app/app/company/people/page.tsx",
])
def test_web_contract_inputs_require_backend_even_on_web_only_prs(path):
    # API/root suites inspect these consumers. A web-only change must not
    # defer discovering a broken contract until an unrelated backend PR.
    assert classify_paths([path]) == {"backend": True, "frontend": True}


@pytest.mark.parametrize("selected,results", itertools.product(
    itertools.product(("true", "false"), repeat=2),
    itertools.product(("success", "failure", "cancelled", "skipped", None), repeat=2),
))
def test_gate_result_matrix(selected, results):
    needs = {"changes": {"result": "success", "outputs": dict(zip(
        ("backend", "frontend"), selected))}}
    needs.update({suite: {"result": result} for suite, result in zip(
        ("backend", "frontend"), results)})
    expected = all(
        result == "success" if wanted == "true" else result in ("success", "skipped")
        for wanted, result in zip(selected, results)
    )
    assert (not gate_errors(needs)) == expected


def test_invalid_classifier_output_never_passes():
    assert gate_errors({})
    assert gate_errors({"changes": {"result": "failure"}})
    assert gate_errors({"changes": {"result": "success", "outputs": {}}})


def test_real_git_comparison_includes_old_and_new_renamed_paths(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args]).decode().strip()
    git("init", "-q")
    git("config", "user.email", "ci@example.invalid")
    git("config", "user.name", "CI fixture")
    (tmp_path / "apps/api").mkdir(parents=True)
    (tmp_path / "apps/api/old.py").write_text("old\n")
    git("add", ".")
    git("commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    (tmp_path / "apps/web").mkdir()
    git("mv", "apps/api/old.py", "apps/web/new.ts")
    git("commit", "-qm", "rename")
    head = git("rev-parse", "HEAD")
    event = {"pull_request": {"base": {"sha": base}, "head": {"sha": head}}}
    paths = changed_paths(event, "pull_request", tmp_path)
    assert set(paths) == {"apps/api/old.py", "apps/web/new.ts"}
    assert classify_paths(paths) == {"backend": True, "frontend": True}
    assert changed_paths({"before": base, "after": head}, "push", tmp_path) == paths
    assert changed_paths({"merge_group": {"base_sha": base, "head_sha": head}},
                         "merge_group", tmp_path) == paths
    assert changed_paths({"before": "0" * 40, "after": head}, "push", tmp_path) is None
    assert changed_paths({}, "workflow_dispatch", tmp_path) is None


def test_no_truncated_file_list_and_invalid_history_fail_closed(tmp_path):
    assert changed_paths({"before": "bad", "after": "bad"}, "push", tmp_path) is None
    files = [f"docs/example-{i}.md" for i in range(1000)] + ["apps/web/app/page.tsx"]
    assert classify_paths(files) == {"backend": True, "frontend": True}


def test_workflow_has_one_always_running_final_gate_and_reuses_real_jobs():
    workflow = yaml.safe_load((ROOT / ".github/workflows/release-check.yml").read_text())
    triggers = workflow.get("on", workflow.get(True))
    assert set(triggers) == {"pull_request", "push", "merge_group", "workflow_dispatch"}
    assert triggers["pull_request"] is None
    assert triggers["push"] == {"branches": ["main"]}
    jobs = workflow["jobs"]
    assert jobs["changes"]["steps"][0]["with"]["fetch-depth"] == 0
    for suite in ("backend", "frontend"):
        assert jobs[suite]["uses"] == f"./.github/workflows/{suite}-tests.yml"
        assert jobs[suite]["if"] == f"needs.changes.outputs.{suite} == 'true'"
        called = yaml.safe_load((ROOT / f".github/workflows/{suite}-tests.yml").read_text())
        assert "workflow_call" in called.get("on", called.get(True))
        assert called["jobs"]["test"]["steps"]
    final = jobs["gate"]
    assert final["name"] == "Release gate"
    assert final["if"] == "${{ always() }}"
    assert set(final["needs"]) == {"changes", "backend", "frontend"}
    assert final["steps"][-1]["env"]["RELEASE_NEEDS"] == "${{ toJSON(needs) }}"
