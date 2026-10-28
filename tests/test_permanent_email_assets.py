"""Any asset an email has ever loaded is permanent.

THE RULE (board, "Standing rules", R1). A sent email keeps its HTML in every
inbox it reached and loads its images by URL each time it is opened. Delete or
rename one of those files and the image breaks in every past email — emails
nobody can change any more. #235 deleted `white.png`, which every account
email since April loads its logo from; caught in review, restored.

THE CHECK, in three parts:
  1. every file in `permanent_email_assets.txt` exists under apps/web/public;
  2. every public file the email code references is in that list, so a new
     reference is recorded the day it is added;
  3. the list holds at least FLOOR, so an entry cannot be dropped together
     with its file in one quiet change.
`apps/api/tests/test_transactional_shell.py` adds the rendered half: every
image an account email actually loads from the app is on the list.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "apps/web/public"
MANIFEST = Path(__file__).with_name("permanent_email_assets.txt")

#: What the list held when the rule was written. It may only grow.
FLOOR = {
    "white.png",
    "logo-white.png",
    "email/trendy-lockup-light@3x.png",
    "email/trendy-lockup-dark@3x.png",
}

#: Everything that builds an email's HTML.
EMAIL_SOURCES = [
    ROOT / "apps/api/src/api/services/email.py",
    ROOT / "apps/worker/src/worker/tasks.py",
    *(ROOT / "apps/worker/src/worker/email").rglob("*.py"),
    *(ROOT / "apps/worker/src/worker/templates/email").rglob("*.jinja2"),
]

_EXT = r"(?:png|jpe?g|gif|svg|webp|ico)"
#: Our own hosts, written out.
ABSOLUTE = re.compile(
    rf"https?://(?:www\.)?(?:trendyreports\.io|reportscompany-web\.vercel\.app)/([A-Za-z0-9_./@%-]+\.{_EXT})")
#: The app base, interpolated: `{_e(app)}/email/x.png`, `{base}/white.png`.
TEMPLATED = re.compile(rf"\}}/([A-Za-z0-9_./@%-]+\.{_EXT})")


def manifest():
    out = set()
    for line in MANIFEST.read_text().splitlines():
        path = line.split("#", 1)[0].strip()
        if path:
            out.add(path)
    return out


def referenced():
    refs = {}
    for f in EMAIL_SOURCES:
        text = f.read_text(encoding="utf-8")
        for rx in (ABSOLUTE, TEMPLATED):
            for m in rx.finditer(text):
                refs.setdefault(m.group(1), f"{f.relative_to(ROOT)}:{text[:m.start()].count(chr(10)) + 1}")
    return refs


def test_every_permanent_asset_still_exists():
    missing = sorted(p for p in manifest() if not (PUBLIC / p).is_file()
                     or (PUBLIC / p).stat().st_size == 0)
    assert not missing, (
        f"{missing} — sent emails load these from inboxes. Deleting or renaming "
        f"one breaks every past email that used it. Restore the file.")


def test_every_asset_an_email_references_is_on_the_list():
    unlisted = {p: where for p, where in referenced().items() if p not in manifest()}
    assert not unlisted, (
        "email code references public file(s) not in tests/permanent_email_assets.txt:\n  "
        + "\n  ".join(f"{p}  ({w})" for p, w in sorted(unlisted.items()))
        + "\nAdd them: once an email has been sent with a URL, that file is permanent.")


def test_the_list_only_grows():
    dropped = sorted(FLOOR - manifest())
    assert not dropped, f"{dropped} left the permanent list. Nothing leaves it."


def test_the_scan_sees_what_it_should():
    """POSITIVE CONTROL: the scanner finds both shapes of reference, in the
    real source. If it stops finding the shell's logo, it has stopped looking."""
    refs = referenced()
    assert "email/trendy-lockup-light@3x.png" in refs, "the templated form is not being found"
    sample = 'x = "https://www.trendyreports.io/brand/a.png" and f"{base}/b/c.jpg"'
    assert [m.group(1) for m in ABSOLUTE.finditer(sample)] == ["brand/a.png"]
    assert [m.group(1) for m in TEMPLATED.finditer(sample)] == ["b/c.jpg"]
