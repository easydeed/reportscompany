"""The SiteX probe's output goes into a ticket, so it must not carry names.

`scripts/probe_sitex_sale_history.py` prints whatever key names SiteX returns
— that is its whole purpose, since the exact spelling is the thing being
discovered. Printing unknown keys and printing their values are different
risks: `PrimaryOwnerName` and `MailingAddress` are in the same PropertyProfile
this probe dumps, and D-116 is about exactly that data leaving the system.

So the redaction is tested rather than trusted, and it is tested at every
depth, because the probe recurses.
"""
import io
import importlib.util
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts/probe_sitex_sale_history.py"


@pytest.fixture(scope="module")
def probe():
    spec = importlib.util.spec_from_file_location("probe_sitex", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["probe_sitex"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("key", [
    "OwnerInformation", "PrimaryOwnerName", "Owner2FullName",
    "MailingAddress", "owner_name", "MAILING_CITY",
])
def test_identity_keys_are_redacted(key, probe):
    assert probe._redacted(key), f"{key} would be printed"


@pytest.mark.parametrize("key", [
    "LastMarketSaleInfo", "SalePrice", "APN", "AssessmentTaxInfo",
])
def test_the_keys_the_probe_exists_to_find_are_not_redacted(key, probe):
    assert not probe._redacted(key), f"{key} would be hidden from the probe's own output"


def test_a_name_nested_three_levels_deep_is_still_redacted(probe):
    payload = {"LastMarketSaleInfo": {
        "SalePrice": 512000,
        "SaleDate": "2019-07-14",
        "Seller": {"OwnerFullName": "HERNANDEZ GERARDO J"},
    }}
    out = io.StringIO()
    with redirect_stdout(out):
        probe._dump(payload)
    text = out.getvalue()
    assert "HERNANDEZ" not in text
    assert "512000" in text, "the probe redacted the thing it exists to find"
    assert "2019-07-14" in text


def test_values_are_truncated_so_a_dump_cannot_carry_a_paragraph(probe):
    out = io.StringIO()
    with redirect_stdout(out):
        probe._dump({"LegalBriefDescription": "X" * 500})
    assert "X" * 200 not in out.getvalue()
