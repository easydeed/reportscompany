/**
 * GENERATED FILE — DO NOT EDIT.
 * Source: apps/worker/src/worker/themes.json
 * Regenerate: python3 scripts/gen_theme_registries.py
 * Checked by: tests/test_theme_registry_is_single_sourced.py
 */

export interface ThemeRegistryEntry {
  id: number
  name: string
  label: string
}

export const THEME_REGISTRY: ThemeRegistryEntry[] = [
  { id: 2, name: "modern", label: "Modern" },
  { id: 3, name: "elegant", label: "Elegant" },
  { id: 5, name: "bold", label: "Bold" },
]

/** id -> name. The two hand-written copies of this were wrong on
 *  every id (D-163): a user on theme 4 got a wizard showing
 *  `elegant` and a PDF rendered in teal. */
export const THEME_ID_TO_NAME: Record<number, string> = {
  2: "modern",
  3: "elegant",
  5: "bold",
}

export const THEME_NAME_TO_ID: Record<string, number> = {
  modern: 2,
  elegant: 3,
  bold: 5,
}

/** Retired themes. An account row or a saved schedule can still hold
 *  one of these ids, so the UI resolves it to the default rather than
 *  showing a blank selection — but the ADMIN report list still has to
 *  label historical rows, which is what the labels are for. */
export const RETIRED_THEME_REGISTRY: ThemeRegistryEntry[] = [
  { id: 1, name: "classic", label: "Classic" },
  { id: 4, name: "teal", label: "Teal" },
]

export const RETIRED_THEME_IDS: number[] = RETIRED_THEME_REGISTRY.map(
  (t) => t.id,
)

export const DEFAULT_THEME_ID = 5

/** The id to actually use for a stored value, which may be absent,
 *  retired, or something nobody has seen before. */
export function resolveThemeId(id: number | null | undefined): number {
  return id != null && THEME_ID_TO_NAME[id] ? id : DEFAULT_THEME_ID
}

export function themeName(id: number | null | undefined): string {
  return THEME_ID_TO_NAME[resolveThemeId(id)]
}
