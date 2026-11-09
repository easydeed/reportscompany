"""Classify complete Git diffs and fail closed when a required suite did not pass."""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

# Shared JS/runtime inputs also affect backend Chromium measurements.
SHARED_FILES = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "pnpm-workspace.yaml",
    ".nvmrc", ".npmrc", ".node-version",
    "scripts/release_gate.py", "tests/test_release_gate.py",
}
BACKEND_FILES = {"pytest.ini", ".python-version", "docker-compose.yml"}
BACKEND_PREFIXES = (
    "apps/api/", "apps/worker/", "tests/", "db/", "scripts/", "tools/",
    "libs/shared/", "apps/web/templates/", "docs/",
)
FRONTEND_PREFIXES = ("apps/web/", "e2e/")
FRONTEND_FILES = {"playwright.config.ts"}
SHARED_PREFIXES = (".github/workflows/", "packages/")
SHA = re.compile(r"[0-9a-f]{40}")


def classify_paths(paths):
    """None means an incomplete comparison: run both rather than assume no change."""
    selected = {"backend": False, "frontend": False}
    if paths is None:
        return dict.fromkeys(selected, True)
    for path in paths:
        if path in SHARED_FILES or path.startswith(SHARED_PREFIXES):
            selected = dict.fromkeys(selected, True)
        elif path in BACKEND_FILES or path.startswith(BACKEND_PREFIXES):
            selected["backend"] = True
            if path.startswith(FRONTEND_PREFIXES):
                selected["frontend"] = True
        elif path in FRONTEND_FILES or path.startswith(FRONTEND_PREFIXES):
            selected["frontend"] = True
        elif not path.lower().endswith(".md"):
            # Unknown executable/configuration families cannot silently bypass CI.
            selected = dict.fromkeys(selected, True)
    return selected


def changed_paths(event, event_name, repo="."):
    """No API pagination or 300-file filter limit; include deleted/renamed paths."""
    if event_name == "pull_request":
        pr = event.get("pull_request", {})
        base, head = pr.get("base", {}).get("sha"), pr.get("head", {}).get("sha")
    elif event_name == "merge_group":
        group = event.get("merge_group", {})
        base, head = group.get("base_sha"), group.get("head_sha")
    elif event_name == "push":
        base, head = event.get("before"), event.get("after")
    else:
        return None
    if not all(isinstance(s, str) and SHA.fullmatch(s) and set(s) != {"0"}
               for s in (base, head)):
        return None
    try:
        if event_name == "pull_request":
            base = subprocess.check_output(
                ["git", "-C", str(repo), "merge-base", base, head]
            ).decode().strip()
        diff = subprocess.check_output([
            "git", "-C", str(repo), "diff", "--name-only", "--no-renames", "-z",
            base, head, "--",
        ])
    except (OSError, subprocess.CalledProcessError):
        return None
    return [p.decode("utf-8", errors="surrogateescape")
            for p in diff.split(b"\0") if p]


def gate_errors(needs):
    """A selected suite must succeed; missing, failed and cancelled are never green."""
    changes = needs.get("changes", {})
    if changes.get("result") != "success":
        return ["change classification did not succeed"]
    required = changes.get("outputs", {})
    errors = []
    for suite in ("backend", "frontend"):
        selection = required.get(suite)
        result = needs.get(suite, {}).get("result")
        if selection not in ("true", "false"):
            errors.append(f"{suite}: invalid or missing selection")
        elif selection == "true" and result != "success":
            errors.append(f"{suite}: required suite returned {result!r}")
        elif selection == "false" and result not in ("success", "skipped"):
            errors.append(f"{suite}: unselected suite returned {result!r}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()
    if args.gate:
        errors = gate_errors(json.loads(os.environ["RELEASE_NEEDS"]))
        for error in errors:
            print(error)
        if not errors:
            print("Release gate passed: every selected suite succeeded.")
        return int(bool(errors))
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    selected = classify_paths(changed_paths(event, os.environ["GITHUB_EVENT_NAME"]))
    print(json.dumps(selected, sort_keys=True))
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        for suite, required in selected.items():
            output.write(f"{suite}={str(required).lower()}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
