"""The files a theme actually renders — one answer, shared by every gate.

WHY THIS EXISTS
---------------
Until 2026-10-06 a theme WAS a file: `THEME_TEMPLATES[theme]` named one
self-contained template and six structural gates read it directly. Design's
package replaces that with one shared page architecture (`_v2/report.jinja2`)
plus a per-theme entry file that sets typography and includes it. bold is the
first theme on it; elegant and modern are still self-contained.

So "the template for this theme" is now a CHAIN, and a gate that reads only
the entry file sees thirty-four lines of `{% set %}` and concludes the theme
has no cover. That is what happened: `test_theme_cover_title` failed at
COLLECTION with "expected exactly one cover title line, found 0", which took
the whole worker suite down and hid every other result until it was fixed.

RESOLVED BY PARSING, NOT BY A LIST
----------------------------------
The chain is read out of each template with Jinja's own parser — `Include`,
`Extends`, `Import` and `FromImport` nodes — rather than from a table of which
themes are on which architecture. A table would be a fourth copy of the thing
D-163 was about, and it would go stale on the day a theme moved. If `_v2/`
later includes a partial of its own, this follows it without being edited.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not resolve `property/_base/`. Nothing live includes that one and
`test_one_comp_set::test_the_live_template_set_reaches_only_the_shared_v2_file`
is what keeps that true — this module would happily follow an include into
the dead tree, so it is not the thing standing between a live template and
D-131's 5,570 lines.
"""
import sys
from pathlib import Path

from jinja2 import Environment, nodes

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.property_builder import THEME_TEMPLATES  # noqa: E402

TEMPLATES = Path(__file__).resolve().parents[1] / "src/worker/templates/property"

#: Template-reference node types, in the order Jinja names them. All four, so
#: a theme that switched from `include` to `extends` would not silently drop
#: out of every chain.
_REFS = (nodes.Include, nodes.Extends, nodes.Import, nodes.FromImport)


def _referenced(path: Path):
    """Template names this file reaches, as written."""
    tree = Environment().parse(path.read_text(encoding="utf-8"))
    out = []
    for kind in _REFS:
        for node in tree.find_all(kind):
            template = getattr(node, "template", None)
            value = getattr(template, "value", None)
            if isinstance(value, str):
                out.append(value)
            elif isinstance(value, (list, tuple)):
                out.extend(v for v in value if isinstance(v, str))
    return out


def chain(theme: str):
    """Every file rendering `theme`, entry file first, depth-first, no repeats.

    Asserts each referenced file exists, so a typo'd include is a failure here
    rather than a Jinja error inside whichever gate happened to run first.
    """
    entry = TEMPLATES / THEME_TEMPLATES[theme]
    assert entry.exists(), f"{theme}: {entry} does not exist"
    out, seen, stack = [], set(), [entry]
    while stack:
        path = stack.pop(0)
        if path in seen:
            continue
        seen.add(path)
        out.append(path)
        for name in _referenced(path):
            target = TEMPLATES / name
            assert target.exists(), (
                f"{path.relative_to(TEMPLATES)} references {name!r}, "
                f"which is not under {TEMPLATES}"
            )
            stack.append(target)
    return out


def source(theme: str) -> str:
    """The chain, concatenated. For a gate that greps rather than parses."""
    return "\n".join(p.read_text(encoding="utf-8") for p in chain(theme))


def is_shared(theme: str) -> bool:
    """Is this theme on the shared architecture?

    Derived from the chain's length, not from a list of theme names.
    """
    return len(chain(theme)) > 1


#: Themes on the shared architecture, and themes still self-contained. Both
#: are DERIVED; a gate that needs to treat them differently asks here.
SHARED_THEMES = sorted(t for t in THEME_TEMPLATES if is_shared(t))
SELF_CONTAINED_THEMES = sorted(t for t in THEME_TEMPLATES if not is_shared(t))
