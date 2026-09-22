"""
Tests for plan resolution and usage limit enforcement.

Phase T1.2: Backend tests for plan & usage logic from Phase 29B.
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, MagicMock
from api.services.usage import (
    get_monthly_usage,
    resolve_plan_for_account,
    evaluate_report_limit,
    LimitDecision
)


from _query_rows import row_for
from api.services.usage import resolve_plan_for_account as _resolve_plan_fn


def plan_row(**columns):
    """
    One row of `resolve_plan_for_account`'s account+plan query, built FROM that
    query (D-091).

    The tuples this replaces were transcribed by hand and listed 7 columns. The
    query selects 15 — it gained `plan_downgrade_at/to` and the six per-product
    limit and override columns — so every test in this file died inside
    `usage.py:90` with "not enough values to unpack (expected 15, got 7)",
    which reads like a product bug and is not.

    Naming the columns rather than ordering them means the next column added to
    that SELECT widens these rows automatically, and a column REMOVED from it
    fails here, on the name, instead of at the unpack.
    """
    return row_for(_resolve_plan_fn, **columns)


# D-093 IS A NUMBER SOMEBODY HAS TO CHOOSE, NOT A BUG I CAN FIX.
#
# An account with no `plan_slug` falls through to `plan_slug = "free"` with no
# plan row, so `effective_limit` lands on the hard-coded `default=100`. This
# test asserts 50. Both are defensible and the repository does not settle it:
# `0012_seed_plans.sql` seeds `solo` (25) and `affiliate` (5000) and no `free`
# row at all, so there is nothing to read the free allowance off.
#
# §0.2: a business decision — a price, a limit, a claim about customers — is
# [JERRY]'s, and the rule is to stop and ask rather than guess or placeholder.
# Changing the product to 50 to make a test pass would be picking a number for
# the business out of deference to a test written in 2025.
#
# strict=True, so whichever way it is decided, this fails until the marker goes.
_D093_GATED = pytest.mark.xfail(
    strict=True,
    reason="D-093: the default report limit for an account with no plan is a "
           "business decision (code says 100, this test says 50) and is "
           "[JERRY]'s to make.",
)


class TestResolvePlan:
    """Tests for resolve_plan_for_account"""
    
    def test_resolve_plan_free_default_limit(self):
        """Free plan should return correct default limit"""
        cursor = Mock()
        cursor.fetchone.return_value = plan_row(plan_slug='free', monthly_report_limit_override=None, account_type='REGULAR', plan_name='Free', plan_limit=50, allow_overage=False, overage_price_cents=0)
        
        result = resolve_plan_for_account(cursor, 'test-account-id')
        
        assert result['plan_slug'] == 'free'
        assert result['plan_name'] == 'Free'
        assert result['monthly_report_limit'] == 50
        assert result['allow_overage'] is False
        assert result['has_override'] is False
    
    def test_resolve_plan_with_override(self):
        """Plan with override should use override value"""
        cursor = Mock()
        cursor.fetchone.return_value = plan_row(plan_slug='pro', monthly_report_limit_override=250, account_type='REGULAR', plan_name='Pro', plan_limit=300, allow_overage=True, overage_price_cents=200)
        
        result = resolve_plan_for_account(cursor, 'test-account-id')
        
        assert result['plan_slug'] == 'pro'
        assert result['monthly_report_limit'] == 250  # Override wins
        assert result['allow_overage'] is True
        assert result['has_override'] is True
        assert result['overage_price_cents'] == 200
    
    @_D093_GATED
    def test_resolve_plan_no_plan_slug_defaults_to_free(self):
        """Account with no plan_slug should default to free"""
        cursor = Mock()
        # First call: main query returns no plan_slug
        # Second call: fallback free plan query
        cursor.fetchone.side_effect = [
            plan_row(plan_slug=None, monthly_report_limit_override=None, account_type='REGULAR', plan_name=None, plan_limit=None, allow_overage=None, overage_price_cents=None),  # Account row
            ('Free', 50, False, 0)  # Free plan fallback
        ]
        
        result = resolve_plan_for_account(cursor, 'test-account-id')
        
        assert result['plan_slug'] == 'free'
        assert result['monthly_report_limit'] == 50
    
    def test_resolve_plan_account_not_found(self):
        """Should raise ValueError if account doesn't exist"""
        cursor = Mock()
        cursor.fetchone.return_value = None
        
        with pytest.raises(ValueError, match="Account .* not found"):
            resolve_plan_for_account(cursor, 'nonexistent-account')


class TestGetMonthlyUsage:
    """Tests for get_monthly_usage"""
    
    def test_get_monthly_usage_returns_correct_structure(self):
        """Should return usage dict with correct structure"""
        cursor = Mock()
        # Mock report count query
        cursor.fetchone.side_effect = [
            (15,),  # report_count
            (8,)    # schedule_run_count
        ]
        
        now = datetime(2025, 11, 15, 10, 30, 0)
        result = get_monthly_usage(cursor, 'test-account-id', now=now)
        
        assert result['report_count'] == 15
        assert result['schedule_run_count'] == 8
        assert result['period_start'] == '2025-11-01'
        assert result['period_end'] == '2025-11-30'
    
    def test_get_monthly_usage_handles_zero_usage(self):
        """Should handle accounts with no usage"""
        cursor = Mock()
        cursor.fetchone.side_effect = [
            (0,),  # No reports
            (0,)   # No schedule runs
        ]
        
        result = get_monthly_usage(cursor, 'test-account-id')
        
        assert result['report_count'] == 0
        assert result['schedule_run_count'] == 0
    
    def test_get_monthly_usage_handles_missing_schedule_runs_table(self):
        """Should gracefully handle if schedule_runs table doesn't exist"""
        cursor = Mock()
        # First query succeeds, second raises exception (table doesn't exist)
        cursor.fetchone.return_value = (10,)
        cursor.execute.side_effect = [
            None,  # First query (reports) succeeds
            Exception("relation 'schedule_runs' does not exist")  # Second fails
        ]
        
        result = get_monthly_usage(cursor, 'test-account-id')
        
        # Should still return report_count, with schedule_run_count = 0
        assert result['report_count'] == 10
        assert result['schedule_run_count'] == 0


class TestEvaluateReportLimit:
    """Tests for evaluate_report_limit - the core limit enforcement logic"""
    
    def test_evaluate_limit_allow_under_80_percent(self):
        """Usage < 80% should ALLOW with no warning"""
        cursor = Mock()
        # Setup: 30/50 reports (60%)
        cursor.fetchone.side_effect = [
            (30,),  # usage
            (0,),   # schedule runs
            plan_row(plan_slug='free', monthly_report_limit_override=None, account_type='REGULAR', plan_name='Free', plan_limit=50, allow_overage=False, overage_price_cents=0)  # plan
        ]
        
        decision, info = evaluate_report_limit(cursor, 'test-account-id')
        
        assert decision == LimitDecision.ALLOW
        assert info['can_proceed'] is True
        assert info['ratio'] == 0.6
        assert '30/50' in info['message']
    
    def test_evaluate_limit_warn_between_80_and_100_percent(self):
        """Usage 80-100% should ALLOW_WITH_WARNING"""
        cursor = Mock()
        # Setup: 45/50 reports (90%)
        cursor.fetchone.side_effect = [
            (45,),  # usage
            (0,),
            plan_row(plan_slug='free', monthly_report_limit_override=None, account_type='REGULAR', plan_name='Free', plan_limit=50, allow_overage=False, overage_price_cents=0)
        ]
        
        decision, info = evaluate_report_limit(cursor, 'test-account-id')
        
        assert decision == LimitDecision.ALLOW_WITH_WARNING
        assert info['can_proceed'] is True
        assert info['ratio'] == 0.9
        assert 'Approaching limit' in info['message']
    
    def test_evaluate_limit_warn_between_100_and_110_percent(self):
        """Usage 100-110% should ALLOW_WITH_WARNING"""
        cursor = Mock()
        # Setup: 52/50 reports (104%) - no overage allowed
        cursor.fetchone.side_effect = [
            (52,),  # usage
            (0,),
            plan_row(plan_slug='free', monthly_report_limit_override=None, account_type='REGULAR', plan_name='Free', plan_limit=50, allow_overage=False, overage_price_cents=0)
        ]
        
        decision, info = evaluate_report_limit(cursor, 'test-account-id')
        
        assert decision == LimitDecision.ALLOW_WITH_WARNING
        assert info['can_proceed'] is True
        assert 1.0 <= info['ratio'] <= 1.1
        assert 'Consider upgrading' in info['message']
    
    def test_evaluate_limit_block_over_110_percent_no_overage(self):
        """Usage > 110% without overage allowed should BLOCK"""
        cursor = Mock()
        # Setup: 60/50 reports (120%) - no overage
        cursor.fetchone.side_effect = [
            (60,),  # usage
            (0,),
            plan_row(plan_slug='free', monthly_report_limit_override=None, account_type='REGULAR', plan_name='Free', plan_limit=50, allow_overage=False, overage_price_cents=0)
        ]
        
        decision, info = evaluate_report_limit(cursor, 'test-account-id')
        
        assert decision == LimitDecision.BLOCK
        assert info['can_proceed'] is False
        assert info['ratio'] == 1.2
        assert 'limit reached' in info['message'].lower()
        assert 'Upgrade' in info['message']
    
    def test_evaluate_limit_allow_over_110_percent_with_overage(self):
        """Usage > 110% with overage allowed should ALLOW_WITH_WARNING + billing info"""
        cursor = Mock()
        # Setup: 350/300 reports (116.7%) - overage allowed
        cursor.fetchone.side_effect = [
            (350,),  # usage
            (0,),
            plan_row(plan_slug='pro', monthly_report_limit_override=None, account_type='REGULAR', plan_name='Pro', plan_limit=300, allow_overage=True, overage_price_cents=200)  # $2/report overage
        ]
        
        decision, info = evaluate_report_limit(cursor, 'test-account-id')
        
        assert decision == LimitDecision.ALLOW_WITH_WARNING
        assert info['can_proceed'] is True
        assert info['ratio'] > 1.1
        assert info['overage_count'] == 50
        assert 'Overage' in info['message']
        # Should mention billing amount (50 reports * $2 = $100)
    
    def test_evaluate_limit_unlimited_plan(self):
        """Plans with limit <= 0 should always ALLOW"""
        cursor = Mock()
        # Setup: Unlimited plan (limit = 0)
        cursor.fetchone.side_effect = [
            (500,),  # High usage
            (0,),
            plan_row(plan_slug='enterprise', monthly_report_limit_override=None, account_type='REGULAR', plan_name='Enterprise', plan_limit=0, allow_overage=False, overage_price_cents=0)
        ]
        
        decision, info = evaluate_report_limit(cursor, 'test-account-id')
        
        assert decision == LimitDecision.ALLOW
        assert info['can_proceed'] is True
        assert info['ratio'] == 0.0
        assert 'Unlimited' in info['message']
    
    def test_evaluate_limit_very_high_limit_treated_as_unlimited(self):
        """Plans with limit >= 10000 should be treated as unlimited"""
        cursor = Mock()
        # Setup: Very high limit
        cursor.fetchone.side_effect = [
            (500,),
            (0,),
            plan_row(plan_slug='enterprise', monthly_report_limit_override=None, account_type='REGULAR', plan_name='Enterprise', plan_limit=50000, allow_overage=False, overage_price_cents=0)
        ]
        
        decision, info = evaluate_report_limit(cursor, 'test-account-id')
        
        assert decision == LimitDecision.ALLOW
        assert info['can_proceed'] is True
        assert 'Unlimited' in info['message']


class TestPlanLimitIntegration:
    """Integration tests combining multiple functions"""
    
    def test_sponsored_account_uses_override_limit(self):
        """Sponsored accounts should respect their custom limits"""
        cursor = Mock()
        # Sponsored account with custom limit of 75 (between free 50 and pro 300)
        cursor.fetchone.side_effect = [
            (40,),  # usage
            (0,),
            plan_row(plan_slug='sponsored_free', monthly_report_limit_override=75, account_type='REGULAR', plan_name='Sponsored Free', plan_limit=50, allow_overage=False, overage_price_cents=0)
        ]
        
        decision, info = evaluate_report_limit(cursor, 'sponsored-account')
        
        # 40/75 = 53% - should allow
        assert decision == LimitDecision.ALLOW
        assert info['plan']['monthly_report_limit'] == 75
        assert info['plan']['has_override'] is True
    
    def test_team_plan_high_limit(self):
        """Team plan with high limit should allow more reports"""
        cursor = Mock()
        # Team plan: 150/200 reports (75%)
        cursor.fetchone.side_effect = [
            (150,),
            (0,),
            plan_row(plan_slug='team', monthly_report_limit_override=None, account_type='REGULAR', plan_name='Team', plan_limit=200, allow_overage=True, overage_price_cents=150)
        ]
        
        decision, info = evaluate_report_limit(cursor, 'team-account')
        
        assert decision == LimitDecision.ALLOW
        assert info['plan']['monthly_report_limit'] == 200
        assert info['ratio'] == 0.75

