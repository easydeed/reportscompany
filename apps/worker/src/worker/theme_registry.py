"""The one place the theme id <-> name pairing is stated (D-163).

Loaded from `themes.json`, which sits beside this module for the same reason
`templates/` does: `property_builder` already reads templates at
`Path(__file__).parent / "templates"` at runtime, so a data file in the
package directory is known to ship. A path to the repository root is not.

WHAT D-163 WAS
Five copies of the pairing existed. `property_builder.THEME_NUMBER_MAP` said
{1: classic, 2: modern, 3: elegant, 4: teal, 5: bold}; the wizard and the
onboarding flow both said {1: teal, 2: bold, 3: classic, 4: elegant,
5: modern} — wrong on every id, not shifted by one. An account whose default
was 4 got a wizard pre-selecting `elegant` and a PDF rendered in teal.
Nothing compared the copies, so nothing failed.

The copies are not gone — a React component cannot import a Python module —
but there is now one source and `tests/test_theme_registry_is_single_sourced.py`
parses every remaining site and asserts it agrees with this file.

IDS ARE NOT RENUMBERED
The cut to three themes left the ids at 2, 3 and 5. `property_reports.theme`
and `property_report_stats.theme_<name>` hold values written before the cut;
renumbering would relabel history. See `themes.json` for the long version.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

REGISTRY_PATH = Path(__file__).parent / "themes.json"

_RAW = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

#: Live themes, in id order.
THEMES: List[Dict[str, object]] = sorted(_RAW["themes"], key=lambda t: t["id"])

#: Retired ids kept for history. A retired theme has no template; asking for
#: one falls back to the default rather than raising, because the value can
#: arrive from a row written years ago.
RETIRED: List[Dict[str, object]] = sorted(_RAW["retired"], key=lambda t: t["id"])

#: The id a report gets when nothing chose one. Jerry, 2026-10-05: bold.
DEFAULT_THEME_ID: int = int(_RAW["default_id"])

#: name -> template path, relative to `templates/property/`.
THEME_TEMPLATES: Dict[str, str] = {str(t["name"]): str(t["template"]) for t in THEMES}

#: id -> name, live themes only.
THEME_NUMBER_MAP: Dict[int, str] = {int(t["id"]): str(t["name"]) for t in THEMES}

#: name -> id, the inverse. Built here rather than inverted at each call site;
#: `property_builder` used to rebuild it inline on every construction.
THEME_NAME_MAP: Dict[str, int] = {v: k for k, v in THEME_NUMBER_MAP.items()}

#: id -> the label shown to a person. The wizard, the branding page and the
#: admin report list each had their own capitalisation of these.
THEME_LABELS: Dict[int, str] = {int(t["id"]): str(t["label"]) for t in THEMES}

#: Retired id -> name. `property_stats` still reports counts under these, and
#: a row written before the cut still carries one.
RETIRED_NUMBER_MAP: Dict[int, str] = {int(t["id"]): str(t["name"]) for t in RETIRED}

DEFAULT_THEME_NAME: str = THEME_NUMBER_MAP[DEFAULT_THEME_ID]

# Asserted at import, not in a test, because every one of these being true is
# what lets the rest of the codebase stop restating the mapping. A registry
# that disagrees with itself should fail the process that loaded it.
assert DEFAULT_THEME_ID in THEME_NUMBER_MAP, (
    f"default_id {DEFAULT_THEME_ID} is not a live theme: {sorted(THEME_NUMBER_MAP)}"
)
assert not set(THEME_NUMBER_MAP) & set(RETIRED_NUMBER_MAP), (
    "an id is both live and retired; ids are never reused"
)
assert len(THEME_TEMPLATES) == len(THEMES), "two themes share a name"


def resolve(theme_input: object) -> tuple[str, int]:
    """(name, id) for whatever a caller has — a name, an id, or junk.

    Accepts `"5"` as well as `5`. `report_generations.theme_id` is
    VARCHAR(20) and `reports.py` writes `str(default_theme_id)` into it, so
    the string form reaches a builder on the market path; before this it fell
    through both `isinstance` arms and silently defaulted (D-164).

    A retired id resolves to the default rather than raising: it can arrive
    from an `accounts` row or a schedule written before the cut, and a report
    that renders in the current default is better than one that does not
    render.
    """
    if isinstance(theme_input, str):
        if theme_input in THEME_TEMPLATES:
            return theme_input, THEME_NAME_MAP[theme_input]
        if theme_input.strip().lstrip("-").isdigit():
            theme_input = int(theme_input)
    if isinstance(theme_input, bool):
        # `True == 1` in Python, and 1 is a retired id. Rejected explicitly so
        # a stray flag does not read as "classic".
        theme_input = None
    if isinstance(theme_input, int) and theme_input in THEME_NUMBER_MAP:
        return THEME_NUMBER_MAP[theme_input], theme_input
    return DEFAULT_THEME_NAME, DEFAULT_THEME_ID
