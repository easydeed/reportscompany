"""A regular account's own postal address reaches the footer of its mail (D-079).

REGULAR accounts build their email brand from `accounts` and `users`
(`tasks._build_regular_brand`), and that brand had no `postal_address` at all,
so a regular agent's emails could only ever carry the platform address. The
address lives on `affiliate_branding` — the row `PUT /v1/account/postal-address`
creates — and the builder now reads it. No row, or a NULL, is the platform
address, attributed to TrendyReports.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")

from worker import tasks  # noqa: E402
from worker.email.template import PLATFORM_POSTAL_ADDRESS, schedule_email_html  # noqa: E402

ACCOUNT_ROW = ("https://x.test/p.jpg", "Dana", "Ortiz", "Broker", "6265550134", "dana@example.test",
               "https://ridge.example.test", "Ridge Realty", None, None, "#0d9488", None, None, None)


class Cursor:
    def __init__(self, address_row):
        self.address_row = address_row
        self.sql = ""

    def execute(self, sql, params=None):
        self.sql = sql

    def fetchone(self):
        if "FROM affiliate_branding" in self.sql:
            return self.address_row
        return ACCOUNT_ROW


def _footer(brand):
    return schedule_email_html(
        account_name="Ridge Realty", report_type="market_snapshot", city="Anytown", zip_codes=None,
        lookback_days=30, metrics={"total_active": 4}, pdf_url="https://x.test/r.pdf",
        unsubscribe_url="https://x.test/u?t=" + "a" * 64, brand=brand, sender_type="REGULAR")


def test_the_regular_brand_carries_the_accounts_address():
    brand = tasks._build_regular_brand(Cursor(("12 Oak Ave, Anytown, CA 90000",)), "acct")
    assert brand["postal_address"] == "12 Oak Ave, Anytown, CA 90000"
    html = _footer(brand)
    assert "Ridge Realty · 12 Oak Ave, Anytown, CA 90000" in html
    assert PLATFORM_POSTAL_ADDRESS not in html


def test_no_row_or_no_address_is_the_platform_address():
    for row in (None, (None,)):
        brand = tasks._build_regular_brand(Cursor(row), "acct")
        assert brand["postal_address"] is None
        html = _footer(brand)
        assert f"TrendyReports · {PLATFORM_POSTAL_ADDRESS} · on behalf of" in html
