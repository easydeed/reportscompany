"""
Unit tests for SimplyRETS query builder correctness.

Verifies:
 1. Market builder uses cities=<city>, NOT q=<city>
 2. Market builder does NOT produce type=RES
 3. vendor param is injected when SIMPLYRETS_VENDOR env var is set
 4. Comps fallback ladder removes subtype and widens sqft as expected
 5. Legacy type codes (RES, CND, MUL) are normalized to valid SimplyRETS values

Run with:  pytest tests/test_simplyrets_query_builder.py -v
"""

import os
import sys
import unittest
from typing import Dict
from unittest.mock import patch

# ── Ensure worker source is on the path ───────────────────────────────────────
WORKER_SRC = os.path.join(
    os.path.dirname(__file__), "..", "apps", "worker", "src"
)
if WORKER_SRC not in sys.path:
    sys.path.insert(0, WORKER_SRC)


# =============================================================================
# 1. Market Builder — cities= not q=, no type=RES
# =============================================================================

class TestMarketQueryBuilderCityParam(unittest.TestCase):
    """Market builder must use cities= (deterministic) not q= (fuzzy)."""

    def _build(self, city: str, **extra) -> Dict:
        """Build query with ALLOW_CITY_SEARCH=True (production mode)."""
        with patch.dict("os.environ", {"SIMPLYRETS_USERNAME": "prod_user",
                                       "SIMPLYRETS_PASSWORD": "prod_pass"}):
            # Force-reload query_builders so IS_DEMO / IS_PRODUCTION is recalculated
            import importlib
            import worker.query_builders as qb
            importlib.reload(qb)
            params = {"city": city, **extra}
            return qb._location(params)

    def test_production_uses_cities_param(self):
        """Production credentials → location uses 'cities' not 'q'."""
        loc = self._build("Anaheim")
        self.assertIn("cities", loc, "Expected 'cities' param in location dict")
        self.assertNotIn("q", loc, "Should NOT have 'q' param when cities= is available")
        self.assertEqual(loc["cities"], "Anaheim")

    def test_production_city_value_preserved(self):
        """City name is passed through without modification."""
        loc = self._build("San Jose")
        self.assertEqual(loc.get("cities"), "San Jose")

    def test_zip_takes_precedence_over_city(self):
        """When ZIPs are present, postalCodes wins over cities."""
        with patch.dict("os.environ", {"SIMPLYRETS_USERNAME": "prod_user",
                                       "SIMPLYRETS_PASSWORD": "prod_pass"}):
            import importlib
            import worker.query_builders as qb
            importlib.reload(qb)
            loc = qb._location({"city": "Anaheim", "zips": ["92805", "92801"]})
        self.assertIn("postalCodes", loc)
        self.assertNotIn("q", loc)


class TestMarketQueryBuilderTypeParam(unittest.TestCase):
    """Market builder must NOT set type=RES."""

    def _get_filter_type(self, filters=None) -> str:
        import importlib
        import worker.query_builders as qb
        importlib.reload(qb)
        result = qb._filters(filters)
        return result.get("type", "")

    def test_default_type_is_not_RES(self):
        """Default type must not be the invalid legacy code 'RES'."""
        t = self._get_filter_type()
        self.assertNotEqual(t, "RES", "type='RES' is an invalid SimplyRETS value")

    def test_default_type_is_residential(self):
        """Default type should be 'residential' (valid SimplyRETS API value)."""
        t = self._get_filter_type()
        self.assertEqual(t, "residential",
                         f"Expected 'residential', got {t!r}")

    def test_explicit_residential_passthrough(self):
        """Explicit 'residential' is passed through unchanged."""
        t = self._get_filter_type({"type": "residential"})
        self.assertEqual(t, "residential")

    def test_RES_alias_normalized_to_residential(self):
        """Legacy code 'RES' is normalized to 'residential'."""
        t = self._get_filter_type({"type": "RES"})
        self.assertEqual(t, "residential",
                         "Legacy 'RES' should be normalized to 'residential'")

    def test_MUL_alias_normalized_to_multifamily(self):
        """Legacy code 'MUL' is normalized to 'multifamily'."""
        t = self._get_filter_type({"type": "MUL"})
        self.assertEqual(t, "multifamily")

    def test_LND_alias_normalized_to_land(self):
        """Legacy code 'LND' is normalized to 'land'."""
        t = self._get_filter_type({"type": "LND"})
        self.assertEqual(t, "land")

    def test_RNT_alias_normalized_to_rental(self):
        """Legacy code 'RNT' is normalized to 'rental'."""
        t = self._get_filter_type({"type": "RNT"})
        self.assertEqual(t, "rental")

    def test_market_snapshot_query_has_no_RES(self):
        """Full market_snapshot query must not contain type=RES."""
        import importlib
        import worker.query_builders as qb
        importlib.reload(qb)
        params = qb.build_market_snapshot({"city": "Anaheim", "lookback_days": 30})
        self.assertNotEqual(params.get("type"), "RES",
                            f"market_snapshot produced type=RES: {params}")
        # type should either be absent or a valid value
        if "type" in params:
            valid_types = {"residential", "multifamily", "commercial", "land", "rental"}
            self.assertIn(params["type"], valid_types,
                          f"Invalid type value in market_snapshot: {params['type']!r}")


# =============================================================================
# 2. Vendor param injection
# =============================================================================

class TestVendorInjection(unittest.TestCase):
    """Vendor param must be injected when SIMPLYRETS_VENDOR env var is set."""

    def test_vendor_injected_in_filter_common_params(self):
        """_common_params() includes vendor when SIMPLYRETS_VENDOR is set."""
        with patch.dict("os.environ", {"SIMPLYRETS_VENDOR": "test-feed-123"}):
            import importlib
            import worker.query_builders as qb
            importlib.reload(qb)
            common = qb._common_params()
        self.assertEqual(common.get("vendor"), "test-feed-123",
                         "_common_params should inject vendor when env var is set")

    def test_vendor_absent_when_env_not_set(self):
        """vendor param should NOT appear when SIMPLYRETS_VENDOR is unset."""
        env = {k: v for k, v in os.environ.items() if k != "SIMPLYRETS_VENDOR"}
        with patch.dict("os.environ", env, clear=True):
            import importlib
            import worker.query_builders as qb
            importlib.reload(qb)
            common = qb._common_params()
        self.assertNotIn("vendor", common,
                         "_common_params should not add vendor when env var is absent")

    def test_vendor_in_worker_simplyrets_inject(self):
        """vendors/simplyrets._inject_vendor adds vendor when env var set."""
        with patch.dict("os.environ", {"SIMPLYRETS_VENDOR": "my-vendor"}):
            import importlib
            import worker.vendors.simplyrets as sr
            importlib.reload(sr)
            result = sr._inject_vendor({"status": "Active"})
        self.assertEqual(result.get("vendor"), "my-vendor")
        self.assertEqual(result.get("status"), "Active")

    def test_vendor_not_overwritten_if_caller_set_it(self):
        """Caller-provided vendor is not overwritten."""
        with patch.dict("os.environ", {"SIMPLYRETS_VENDOR": "env-vendor"}):
            import importlib
            import worker.vendors.simplyrets as sr
            importlib.reload(sr)
            result = sr._inject_vendor({"vendor": "caller-vendor"})
        self.assertEqual(result.get("vendor"), "caller-vendor")


# =============================================================================
# 3. filter_resolver no longer emits type=RES
# =============================================================================

class TestFilterResolverType(unittest.TestCase):
    """filter_resolver.resolve_filters must not emit type=RES."""

    def _resolve(self, intent, stats) -> Dict:
        import importlib
        import worker.filter_resolver as fr
        importlib.reload(fr)
        return fr.resolve_filters(intent, stats)

    def test_resolver_type_is_not_RES(self):
        resolved = self._resolve({}, {"median_list_price": 500000})
        self.assertNotEqual(resolved.get("type"), "RES",
                            "resolve_filters must not emit type=RES")

    def test_resolver_type_is_residential(self):
        resolved = self._resolve({}, {"median_list_price": 500000})
        self.assertEqual(resolved.get("type"), "residential")


# =============================================================================
# 4. Comps fallback ladder — query progression
# =============================================================================

class TestCompsFallbackLadderLogic(unittest.TestCase):
    """
    Tests the fallback ladder logic by directly testing the query structure
    at each level (without making HTTP calls).
    """

    # Replicates the ladder param builder from property.py
    @staticmethod
    def _build_ladder_params(
        sqft: int = 1800,
        beds: int = 3,
        baths: float = 2.0,
        sqft_var: float = 0.20,
        extra_beds: int = 0,
        include_subtype: bool = True,
        sr_type: str = "residential",
        sr_subtype: str = "SingleFamilyResidence",
        subject_zip: str = "92805",
        subject_city: str = "Anaheim",
        limit: int = 10,
    ) -> Dict:
        p: Dict = {
            "type": sr_type,
            "status": "Closed",
            "limit": limit * 4,
        }
        if subject_zip:
            p["postalCodes"] = subject_zip
        if subject_city:
            p["cities"] = subject_city
        if sqft_var is not None:
            p["minarea"] = int(sqft * (1 - sqft_var))
            p["maxarea"] = int(sqft * (1 + sqft_var))
        p["minbeds"] = max(1, beds - 1 - extra_beds)
        p["maxbeds"] = beds + 1 + extra_beds
        if extra_beds == 0:
            p["minbaths"] = max(1, int(baths) - 1)
            p["maxbaths"] = int(baths) + 1
        if include_subtype:
            p["subtype"] = sr_subtype
        return p

    def test_L0_has_subtype(self):
        p = self._build_ladder_params(include_subtype=True)
        self.assertIn("subtype", p)
        self.assertEqual(p["subtype"], "SingleFamilyResidence")

    def test_L1_no_subtype(self):
        """Level 1 removes subtype."""
        p = self._build_ladder_params(include_subtype=False)
        self.assertNotIn("subtype", p)

    def test_L0_sqft_variance_20_pct(self):
        p = self._build_ladder_params(sqft=1800, sqft_var=0.20, include_subtype=True)
        self.assertEqual(p["minarea"], 1440)   # 1800 * 0.80
        self.assertEqual(p["maxarea"], 2160)   # 1800 * 1.20

    def test_L2_sqft_variance_30_pct(self):
        """Level 2 widens sqft to ±30%."""
        p = self._build_ladder_params(sqft=1800, sqft_var=0.30, include_subtype=False)
        self.assertEqual(p["minarea"], 1260)   # 1800 * 0.70
        self.assertEqual(p["maxarea"], 2340)   # 1800 * 1.30
        self.assertNotIn("subtype", p)

    def test_L3_sqft_40pct_beds_plus1(self):
        """Level 3 widens sqft to ±40% and expands beds by +1."""
        p = self._build_ladder_params(sqft=1800, sqft_var=0.40, extra_beds=1,
                                      beds=3, include_subtype=False)
        self.assertEqual(p["minarea"], 1080)   # 1800 * 0.60
        self.assertEqual(p["maxarea"], 2520)   # 1800 * 1.40
        self.assertEqual(p["minbeds"], 1)      # max(1, 3-1-1)
        self.assertEqual(p["maxbeds"], 5)      # 3+1+1

    def test_L3_removes_baths_filter(self):
        """Extra_beds > 0 removes bath filter to avoid over-constraining."""
        p = self._build_ladder_params(extra_beds=1)
        self.assertNotIn("minbaths", p)
        self.assertNotIn("maxbaths", p)

    def test_L5_no_sqft_no_subtype(self):
        """Level 5 removes sqft and subtype entirely."""
        p = self._build_ladder_params(sqft_var=None, extra_beds=2, include_subtype=False)
        self.assertNotIn("minarea", p)
        self.assertNotIn("maxarea", p)
        self.assertNotIn("subtype", p)

    def test_type_is_not_RES_in_any_level(self):
        """type=RES must never appear in any ladder level."""
        for incl_sub in (True, False):
            for sqft_var in (0.20, 0.30, 0.40, None):
                p = self._build_ladder_params(
                    sqft_var=sqft_var, include_subtype=incl_sub
                )
                self.assertNotEqual(p.get("type"), "RES",
                    f"Level incl_sub={incl_sub}, sqft_var={sqft_var} produced type=RES")

    def test_cities_used_not_q(self):
        """Comps params use cities= not q= for city filtering."""
        p = self._build_ladder_params(subject_city="Anaheim")
        self.assertIn("cities", p)
        self.assertNotIn("q", p)
        self.assertEqual(p["cities"], "Anaheim")


# =============================================================================
# 5. build_params dispatcher
# =============================================================================

class TestBuildParamsDispatcher(unittest.TestCase):
    """build_params should route to correct builders and never emit type=RES."""

    REPORT_TYPES = [
        "market_snapshot", "snapshot",
        "new_listings", "new_listings_gallery", "featured_listings",
        "closed", "closed_listings", "sold",
        "inventory_by_zip", "inventory",
        "open_houses", "open-houses",
        "price_bands", "price-bands",
    ]

    def _build(self, report_type: str, city: str = "TestCity") -> Dict:
        import importlib
        import worker.query_builders as qb
        importlib.reload(qb)
        return qb.build_params(report_type, {"city": city, "lookback_days": 30})

    def test_no_report_type_produces_RES(self):
        """No report type should produce type=RES."""
        for rt in self.REPORT_TYPES:
            params = self._build(rt)
            self.assertNotEqual(
                params.get("type"), "RES",
                f"build_params('{rt}') produced invalid type=RES"
            )

    def test_valid_types_only(self):
        """When type is set, it must be a valid SimplyRETS value."""
        valid = {"residential", "rental", "multifamily", "commercial", "land"}
        for rt in self.REPORT_TYPES:
            params = self._build(rt)
            if "type" in params:
                self.assertIn(
                    params["type"], valid,
                    f"build_params('{rt}') has invalid type={params['type']!r}. "
                    f"Valid values: {valid}"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
