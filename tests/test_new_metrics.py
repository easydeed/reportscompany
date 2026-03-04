"""
Prompt 3C — Unit tests for new metric computations and template logic.

Tests cover:
- compute_price_cut_stats()   price cut rate + median cut
- compute_dom_distribution()  DOM bucket percentages
- comp_confidence()           fallback ladder level -> A/B/C/D
- parse_options_meta()        handles both flat + fields-nested OPTIONS shapes
- field presence assertions   fixtures have required fields
"""

import json
import pathlib
import pytest
from datetime import datetime, timedelta

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures"


# ─── Helpers / pure functions (no project deps) ────────────────────────────────

def compute_price_cut_stats(active_listings: list) -> dict:
    """
    Compute price cut rate and median cut size from active listings.

    Fields used:
        listing["list_price"]           (int) current price
        listing["original_list_price"]  (int) original price (may equal list_price)
    """
    cuts = [
        l for l in active_listings
        if (l.get("original_list_price") or 0) > (l.get("list_price") or 0)
    ]
    cut_amounts = [
        l["original_list_price"] - l["list_price"]
        for l in cuts
    ]
    cut_rate = len(cuts) / len(active_listings) if active_listings else 0.0
    median_cut = sorted(cut_amounts)[len(cut_amounts) // 2] if cut_amounts else 0
    return {
        "count":       len(cuts),
        "rate":        round(cut_rate, 4),
        "median_cut":  median_cut,
    }


def compute_dom_distribution(dom_values: list) -> dict:
    """
    Compute DOM distribution buckets from a list of integer DOM values.

    Returns percentages (0–100) for each bucket.
    """
    if not dom_values:
        return {}
    n = len(dom_values)
    return {
        "under_7":  round(len([d for d in dom_values if d <= 7])  / n * 100, 1),
        "under_14": round(len([d for d in dom_values if d <= 14]) / n * 100, 1),
        "under_30": round(len([d for d in dom_values if d <= 30]) / n * 100, 1),
        "over_45":  round(len([d for d in dom_values if d > 45])  / n * 100, 1),
    }


def comp_confidence(ladder_level: str) -> str:
    """
    Map SimplyRETS fallback ladder level to confidence grade.

    L0:strict             -> A   (strict match, same subtype, ±20% sqft)
    L1:no-subtype         -> B   (subtype removed)
    L2:sqft±30%           -> B   (sqft loosened)
    L3:sqft±40%,beds±1    -> C   (beds loosened)
    L4:sqft±50%,beds±2    -> C
    L5:no-sqft,no-subtype -> D   (very thin market)
    none / unknown        -> D
    """
    level = (ladder_level or "none").lower()
    if level.startswith("l0"):
        return "A"
    if level.startswith("l1") or level.startswith("l2"):
        return "B"
    if level.startswith("l3") or level.startswith("l4"):
        return "C"
    return "D"


def parse_options_meta(meta: dict) -> dict:
    """
    Parse OPTIONS response dict into {statuses, types, subtypes, cities}.
    Handles both flat and fields-nested shapes.
    """
    fields = meta.get("fields") or meta
    statuses = (fields.get("statuses") or fields.get("status") or
                meta.get("statuses") or meta.get("status") or [])
    types    = (fields.get("types") or fields.get("type") or
                meta.get("types") or meta.get("type") or [])
    subtypes = (fields.get("subtypes") or fields.get("subtype") or
                meta.get("subtypes") or meta.get("subtype") or [])
    cities   = (fields.get("cities") or meta.get("cities") or [])
    return {"statuses": statuses, "types": types, "subtypes": subtypes, "cities": cities}


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def active_listing():
    return json.loads((FIXTURE_DIR / "listing_active_minimal.json").read_text())


@pytest.fixture
def closed_listing():
    return json.loads((FIXTURE_DIR / "listing_closed_minimal.json").read_text())


@pytest.fixture
def options_nested():
    return json.loads((FIXTURE_DIR / "options_fields_nested.json").read_text())


# ─── Tests: compute_price_cut_stats ────────────────────────────────────────────

class TestPriceCutStats:
    def test_basic_cut_detected(self):
        listings = [
            {"list_price": 800000, "original_list_price": 850000},  # cut: -50k
            {"list_price": 700000, "original_list_price": 700000},  # no cut
            {"list_price": 600000, "original_list_price": 650000},  # cut: -50k
        ]
        result = compute_price_cut_stats(listings)
        assert result["count"] == 2
        assert result["rate"] == pytest.approx(2/3, rel=0.01)
        assert result["median_cut"] == 50000

    def test_no_cuts(self):
        listings = [
            {"list_price": 500000, "original_list_price": 500000},
            {"list_price": 600000, "original_list_price": 600000},
        ]
        result = compute_price_cut_stats(listings)
        assert result["count"] == 0
        assert result["rate"] == 0.0
        assert result["median_cut"] == 0

    def test_missing_original_treated_as_no_cut(self):
        listings = [
            {"list_price": 500000},  # no original_list_price
            {"list_price": 500000, "original_list_price": None},
        ]
        result = compute_price_cut_stats(listings)
        assert result["count"] == 0

    def test_empty_list(self):
        result = compute_price_cut_stats([])
        assert result["rate"] == 0.0
        assert result["count"] == 0

    def test_active_fixture_has_price_cut(self, active_listing):
        """Active fixture has originalListPrice=895000 > listPrice=869900."""
        listings = [{
            "list_price": active_listing["listPrice"],
            "original_list_price": active_listing["originalListPrice"],
        }]
        result = compute_price_cut_stats(listings)
        assert result["count"] == 1
        assert result["median_cut"] == 895000 - 869900

    def test_closed_fixture_no_price_cut(self, closed_listing):
        """Closed fixture has same list and original price."""
        listings = [{
            "list_price": closed_listing["listPrice"],
            "original_list_price": closed_listing["originalListPrice"],
        }]
        result = compute_price_cut_stats(listings)
        assert result["count"] == 0


# ─── Tests: compute_dom_distribution ───────────────────────────────────────────

class TestDomDistribution:
    def test_known_distribution(self):
        dom = [5, 8, 12, 20, 50, 60, 10, 3, 25, 90]
        # under_7:  5,3         = 2/10 = 20%
        # under_14: 5,8,12,10,3 = 5/10 = 50%
        # under_30: 5,8,12,20,10,3,25 = 7/10 = 70%
        # over_45:  50,60,90    = 3/10 = 30%
        r = compute_dom_distribution(dom)
        assert r["under_7"]  == 20.0
        assert r["under_14"] == 50.0
        assert r["under_30"] == 70.0
        assert r["over_45"]  == 30.0

    def test_all_fast(self):
        dom = [1, 2, 3, 4, 5]
        r = compute_dom_distribution(dom)
        assert r["under_7"]  == 100.0
        assert r["over_45"]  == 0.0

    def test_all_slow(self):
        dom = [60, 70, 80, 90]
        r = compute_dom_distribution(dom)
        assert r["under_7"]  == 0.0
        assert r["over_45"]  == 100.0

    def test_empty(self):
        assert compute_dom_distribution([]) == {}

    def test_closed_fixture_dom(self, closed_listing):
        dom = [closed_listing["mls"]["daysOnMarket"]]  # 16 days
        r = compute_dom_distribution(dom)
        assert r["under_14"] == 0.0   # 16 > 14
        assert r["under_30"] == 100.0  # 16 <= 30
        assert r["over_45"]  == 0.0


# ─── Tests: comp_confidence ────────────────────────────────────────────────────

class TestCompConfidence:
    @pytest.mark.parametrize("level,expected", [
        ("L0:strict",            "A"),
        ("L0:STRICT",            "A"),   # case insensitive
        ("L1:no-subtype",        "B"),
        ("L2:sqft+-30%",         "B"),
        ("L3:sqft+-40%,beds+-1", "C"),
        ("L4:sqft+-50%,beds+-2", "C"),
        ("L5:no-sqft,no-subtype","D"),
        ("none",                 "D"),
        ("",                     "D"),
        (None,                   "D"),
    ])
    def test_all_levels(self, level, expected):
        assert comp_confidence(level) == expected

    def test_a_means_strict_match(self):
        assert comp_confidence("L0:strict") == "A"

    def test_b_means_relaxed(self):
        assert comp_confidence("L1:no-subtype") == "B"

    def test_d_means_thin_market(self):
        assert comp_confidence("L5:no-sqft,no-subtype") == "D"


# ─── Tests: parse_options_meta ─────────────────────────────────────────────────

class TestOptionsMetaParser:
    def test_fields_nested_shape(self, options_nested):
        result = parse_options_meta(options_nested)
        assert "Active" in result["statuses"]
        assert "Closed" in result["statuses"]
        assert len(result["statuses"]) >= 3
        assert "Residential" in result["types"]
        assert "SingleFamilyResidence" in result["subtypes"]
        assert "Downey" in result["cities"]

    def test_flat_shape(self):
        flat_meta = {
            "status":  ["Active", "Closed"],
            "type":    ["Residential"],
            "cities":  ["Houston", "Anaheim"],
        }
        result = parse_options_meta(flat_meta)
        assert "Active" in result["statuses"]
        assert "Residential" in result["types"]
        assert "Houston" in result["cities"]
        assert result["subtypes"] == []

    def test_empty_response(self):
        result = parse_options_meta({})
        assert result["statuses"] == []
        assert result["types"] == []
        assert result["subtypes"] == []
        assert result["cities"] == []

    def test_counts_match_fixture(self, options_nested):
        result = parse_options_meta(options_nested)
        assert len(result["statuses"]) == 5
        assert len(result["types"]) == 8
        assert len(result["cities"]) == 7


# ─── Tests: fixture field presence ─────────────────────────────────────────────

class TestFixtureFields:
    def test_active_required_fields_present(self, active_listing):
        assert active_listing.get("listPrice") is not None
        assert active_listing.get("originalListPrice") is not None
        assert active_listing.get("listDate") is not None
        assert active_listing.get("property", {}).get("area") is not None
        assert active_listing.get("property", {}).get("lotSizeArea") is not None
        assert active_listing.get("mls", {}).get("daysOnMarket") is not None
        assert active_listing.get("association") is not None
        assert "fee" in active_listing["association"]
        assert active_listing.get("school", {}).get("district") is not None

    def test_closed_sales_dates_present(self, closed_listing):
        sales = closed_listing.get("sales") or {}
        assert sales.get("closeDate") is not None, "closeDate required"
        assert sales.get("contractDate") is not None, "contractDate required for timeline calc"
        assert sales.get("closePrice") is not None, "closePrice required"

    def test_tax_annual_amount_is_null(self, active_listing, closed_listing):
        """Both fixtures confirm taxAnnualAmount is NULL in this feed."""
        assert active_listing.get("tax", {}).get("taxAnnualAmount") is None
        assert closed_listing.get("tax", {}).get("taxAnnualAmount") is None

    def test_school_district_present(self, active_listing, closed_listing):
        assert active_listing["school"]["district"] == "Downey Unified"
        assert closed_listing["school"]["district"] == "Bonita Unified"

    def test_hoa_fee_present_and_zero_for_sfr(self, active_listing, closed_listing):
        assert active_listing["association"]["fee"] == 0
        assert closed_listing["association"]["fee"] == 0

    def test_photo_count_inferrable(self, active_listing, closed_listing):
        assert len(active_listing["photos"]) == 3
        assert len(closed_listing["photos"]) == 5

    def test_lot_size_present(self, active_listing, closed_listing):
        assert active_listing["property"]["lotSizeArea"] == 5183
        assert closed_listing["property"]["lotSizeArea"] == 7460

    def test_contract_to_close_calculable(self, closed_listing):
        from datetime import datetime
        sales = closed_listing["sales"]
        close    = datetime.fromisoformat(sales["closeDate"].replace("Z", ""))
        contract = datetime.fromisoformat(sales["contractDate"].replace("Z", ""))
        list_dt  = datetime.fromisoformat(closed_listing["listDate"].replace("Z", ""))
        escrow_days    = (close - contract).days
        marketing_days = (contract - list_dt).days
        assert escrow_days > 0,    "escrow_days must be positive"
        assert marketing_days > 0, "marketing_days must be positive"
        # NOTE: SimplyRETS daysOnMarket = days from listing to contract only (list→contract).
        # It does NOT equal escrow_days + marketing_days (which spans list→close).
        # We verify the timeline components are individually positive and computable.
        dom = closed_listing["mls"]["daysOnMarket"]
        assert marketing_days == dom, (
            f"marketing_days ({marketing_days}) should match SimplyRETS daysOnMarket ({dom}) "
            f"because DOM = listDate -> contractDate in this feed"
        )
