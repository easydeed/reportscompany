#!/usr/bin/env python3
"""Generate the API and web theme registries from the canonical JSON.

THE SHAPE, AND WHY IT IS NOT "EVERYONE IMPORTS ONE MODULE"
`apps/worker/src/worker/themes.json` is canonical and the worker reads it at
runtime. A FastAPI process and a React component cannot: the API and the
worker are separate services whose runtimes are not guaranteed to contain
each other's packages (the one place the API does reach into the worker,
`branding_tools._load_market_report_builder`, caches the ImportError and
carries on without it), and a browser bundle cannot read a Python package's
data file at all.

So each of those two gets ONE generated file, and
`tests/test_theme_registry_is_single_sourced.py` regenerates both in memory
and fails if what is on disk differs. Three statements of the pairing, two of
them machine-checked, replacing seventeen hand-written ones (D-163).

Run after editing themes.json:

    python3 scripts/gen_theme_registries.py          # write
    python3 scripts/gen_theme_registries.py --check  # exit 1 if stale
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps/worker/src/worker/themes.json"
API_OUT = ROOT / "apps/api/src/api/theme_registry.py"
WEB_OUT = ROOT / "apps/web/lib/themes.generated.ts"

BANNER = (
    "GENERATED FILE — DO NOT EDIT.\n"
    "Source: apps/worker/src/worker/themes.json\n"
    "Regenerate: python3 scripts/gen_theme_registries.py\n"
    "Checked by: tests/test_theme_registry_is_single_sourced.py"
)


def load():
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    themes = sorted(raw["themes"], key=lambda t: t["id"])
    retired = sorted(raw["retired"], key=lambda t: t["id"])
    default = int(raw["default_id"])
    assert default in {int(t["id"]) for t in themes}, "default_id is not live"
    return themes, retired, default


def render_api(themes, retired, default) -> str:
    lines = [f'"""{BANNER}\n\n']
    lines.append(
        "The API needs two facts about themes and nothing else: what a person\n"
        "is allowed to set as their account default, and what id to store when\n"
        "they have not set one. Both were literals — `ge=1, le=5` in\n"
        "`routes/account.py` and the string `\"1\"` in `routes/reports.py` —\n"
        "and `\"1\"` disagreed with every other default in the codebase.\n"
        '"""\n'
    )
    lines.append("from typing import Dict, List\n\n")
    lines.append("#: id -> name, live themes only.\n")
    lines.append("THEME_NUMBER_MAP: Dict[int, str] = {\n")
    for t in themes:
        lines.append(f'    {t["id"]}: "{t["name"]}",\n')
    lines.append("}\n\n")
    lines.append("#: Retired ids. Still held by historical rows; not selectable.\n")
    lines.append("RETIRED_NUMBER_MAP: Dict[int, str] = {\n")
    for t in retired:
        lines.append(f'    {t["id"]}: "{t["name"]}",\n')
    lines.append("}\n\n")
    lines.append(f"DEFAULT_THEME_ID: int = {default}\n\n")
    lines.append(
        "#: The ids an account may be set to, for the request validator.\n"
        "#: A plain `ge`/`le` range cannot express the gaps the cut left.\n"
    )
    lines.append("SELECTABLE_THEME_IDS: List[int] = sorted(THEME_NUMBER_MAP)\n")
    return "".join(lines)


def render_web(themes, retired, default) -> str:
    lines = [f"/**\n * {BANNER.replace(chr(10), chr(10) + ' * ')}\n */\n\n"]
    lines.append("export interface ThemeRegistryEntry {\n")
    lines.append("  id: number\n  name: string\n  label: string\n}\n\n")
    lines.append("export const THEME_REGISTRY: ThemeRegistryEntry[] = [\n")
    for t in themes:
        lines.append(
            f'  {{ id: {t["id"]}, name: "{t["name"]}", label: "{t["label"]}" }},\n'
        )
    lines.append("]\n\n")
    lines.append(
        "/** id -> name. The two hand-written copies of this were wrong on\n"
        " *  every id (D-163): a user on theme 4 got a wizard showing\n"
        " *  `elegant` and a PDF rendered in teal. */\n"
    )
    lines.append("export const THEME_ID_TO_NAME: Record<number, string> = {\n")
    for t in themes:
        lines.append(f'  {t["id"]}: "{t["name"]}",\n')
    lines.append("}\n\n")
    lines.append("export const THEME_NAME_TO_ID: Record<string, number> = {\n")
    for t in themes:
        lines.append(f'  {t["name"]}: {t["id"]},\n')
    lines.append("}\n\n")
    lines.append(
        "/** Retired themes. An account row or a saved schedule can still hold\n"
        " *  one of these ids, so the UI resolves it to the default rather than\n"
        " *  showing a blank selection — but the ADMIN report list still has to\n"
        " *  label historical rows, which is what the labels are for. */\n"
    )
    lines.append("export const RETIRED_THEME_REGISTRY: ThemeRegistryEntry[] = [\n")
    for t in retired:
        lines.append(
            f'  {{ id: {t["id"]}, name: "{t["name"]}", label: "{t["label"]}" }},\n'
        )
    lines.append("]\n\n")
    lines.append("export const RETIRED_THEME_IDS: number[] = RETIRED_THEME_REGISTRY.map(\n")
    lines.append("  (t) => t.id,\n)\n\n")
    lines.append(f"export const DEFAULT_THEME_ID = {default}\n\n")
    lines.append(
        "/** The id to actually use for a stored value, which may be absent,\n"
        " *  retired, or something nobody has seen before. */\n"
        "export function resolveThemeId(id: number | null | undefined): number {\n"
        "  return id != null && THEME_ID_TO_NAME[id] ? id : DEFAULT_THEME_ID\n"
        "}\n\n"
        "export function themeName(id: number | null | undefined): string {\n"
        "  return THEME_ID_TO_NAME[resolveThemeId(id)]\n"
        "}\n"
    )
    return "".join(lines)


def main() -> int:
    themes, retired, default = load()
    wanted = {API_OUT: render_api(themes, retired, default),
              WEB_OUT: render_web(themes, retired, default)}
    check = "--check" in sys.argv
    stale = []
    for path, text in wanted.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == text:
            continue
        stale.append(path.relative_to(ROOT))
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if check:
        if stale:
            print("STALE: " + ", ".join(map(str, stale)), file=sys.stderr)
            print("Run: python3 scripts/gen_theme_registries.py", file=sys.stderr)
            return 1
        print("theme registries are current")
        return 0
    print("wrote" if stale else "already current", *map(str, stale) or ["(nothing)"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
