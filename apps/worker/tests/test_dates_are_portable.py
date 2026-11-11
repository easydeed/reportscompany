"""Dates print the same on Windows as on Linux.

A dash or hash flag in a strftime pattern raises ValueError on Windows.
On main that pattern was in three product files and nowhere else under apps/
outside tests: the property report label, the market email, and the
home-value email. This file fails if one comes back.
"""
import os
import re
import sys
from datetime import date
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from email_fixtures import render  # noqa: E402
from test_property_production_render import report_data  # noqa: E402
from worker.email.home_value import home_value_email_html  # noqa: E402
from worker.property_builder import PropertyReportBuilder  # noqa: E402

APPS = REPO / "apps"
# A strftime flag, not a Jinja trim marker: the flag sits against the directive.
_FLAG = re.compile("%" + r"[-#][A-Za-z]")
_SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".woff", ".woff2",
}


def _date_format_flags():
    hits = []
    for path in APPS.rglob("*"):
        if not path.is_file() or "tests" in path.parts or path.suffix.lower() in _SKIP_SUFFIXES:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(lines, 1):
            if _FLAG.search(line):
                hits.append(f"{path.relative_to(REPO).as_posix()}:{number}")
    return hits


def test_no_strftime_flag_anywhere_in_apps():
    assert _date_format_flags() == []


def test_the_fifth_is_unpadded_on_the_report_and_both_emails(monkeypatch):
    frozen = date(2026, 11, 5)
    monkeypatch.setattr("worker.property_builder._report_today", lambda: frozen)
    monkeypatch.setattr("worker.email.template._today", lambda: frozen)
    monkeypatch.setattr("worker.email.home_value._today", lambda: frozen)

    report = PropertyReportBuilder(report_data("harbor")).render_html()
    assert "Nov 5, 2026" in report
    assert "Nov 05, 2026" not in report

    market = render("market_snapshot", "#0D9488")
    home = home_value_email_html(
        report_url="https://www.trendyreports.io/r/abc",
        address="14 Sandpiper Ln",
        city="Irvine",
        requester_first_name="Tom",
        agent_name="Dana Ortiz",
        agent_title="Broker Associate",
        company_name="Marisol Ridge Realty",
        agent_phone="(626) 555-0134",
        agent_email="dana@example.test",
        primary_color="#1B365D",
    )
    for html in (market, home):
        assert "November 5, 2026" in html
        assert "November 05, 2026" not in html
