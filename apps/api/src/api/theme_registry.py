"""GENERATED FILE — DO NOT EDIT.
Source: apps/worker/src/worker/themes.json
Regenerate: python3 scripts/gen_theme_registries.py
Checked by: tests/test_theme_registry_is_single_sourced.py

The API needs two facts about themes and nothing else: what a person
is allowed to set as their account default, and what id to store when
they have not set one. Both were literals — `ge=1, le=5` in
`routes/account.py` and the string `"1"` in `routes/reports.py` —
and `"1"` disagreed with every other default in the codebase.
"""
from typing import Dict, List

#: id -> name, live themes only.
THEME_NUMBER_MAP: Dict[int, str] = {
    2: "modern",
    3: "elegant",
    5: "bold",
}

#: Retired ids. Still held by historical rows; not selectable.
RETIRED_NUMBER_MAP: Dict[int, str] = {
    1: "classic",
    4: "teal",
}

DEFAULT_THEME_ID: int = 5

#: The ids an account may be set to, for the request validator.
#: A plain `ge`/`le` range cannot express the gaps the cut left.
SELECTABLE_THEME_IDS: List[int] = sorted(THEME_NUMBER_MAP)
