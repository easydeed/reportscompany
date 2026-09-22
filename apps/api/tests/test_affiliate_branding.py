"""
Tests for affiliate branding helper (get_brand_for_account).

Phase T1.4: Backend tests for white-label branding logic from Phase 30 / W1.
"""
import pytest
from unittest.mock import Mock
from api.services.branding import (
    get_brand_for_account,
    validate_brand_input,
    Brand,
    DEFAULT_PRIMARY,
    DEFAULT_ACCENT
)


from _query_rows import row_for
from api.services.branding import (
    get_brand_for_account as _brand_fn,
    _fetch_affiliate_branding_row,
)


def account_row(**columns):
    """
    One row of `get_brand_for_account`'s accounts query, built FROM that query
    (D-091).

    These tuples carried FOUR values — the fourth a `sponsor_account_id` the
    query no longer selects, since REGULAR agents stopped having a sponsor
    fallback. So every test here died inside `branding.py:60` with "too many
    values to unpack (expected 3)".

    Note the direction: `test_plans_limits` drifted because the query GAINED
    columns, this one because the query LOST one. A transcribed tuple is wrong
    either way, and the error surfaces in the production module both times,
    which is what makes these read like product bugs.
    """
    return row_for(_brand_fn, **columns)


def branding_row(**columns):
    """
    One row of the affiliate_branding query, built FROM it (D-091).

    `_fetch_affiliate_branding_row` tries three SELECTs in order — full (11
    columns), legacy (10), minimal (8) — falling back only when the previous one
    RAISES because a column does not exist. A `Mock()` cursor never raises, so
    the code always takes the FULL path, while these tuples carried the eight
    columns of the MINIMAL one. Result: `IndexError: tuple index out of range`
    at branding.py:148, on `branding_row[8]`.

    A different failure from the other two in this file, and worth naming
    precisely: not a query that changed, but a double that cannot reproduce the
    fallback the code is written around. Index 0 is the full query, which is
    what a current database serves.
    """
    return row_for(_fetch_affiliate_branding_row, index=0, **columns)



class TestGetBrandForAccount:
    """Tests for get_brand_for_account resolution logic"""
    
    def test_regular_without_sponsor_uses_trendy_fallback(self):
        """REGULAR account with no sponsor should use TrendyReports default brand"""
        cursor = Mock()
        
        # Account query: REGULAR type, no sponsor
        cursor.fetchone.return_value = account_row(id='account-123', name='John Doe Real Estate', account_type='REGULAR')
        
        # Branding query will be called but return None (no custom branding)
        cursor.execute.side_effect = [
            None,  # Account query
            None   # Branding query returns nothing
        ]
        cursor.fetchone.side_effect = [
            account_row(id='account-123', name='John Doe Real Estate', account_type='REGULAR'),
            None  # No branding row
        ]
        
        brand = get_brand_for_account(cursor, 'account-123')
        
        assert brand['display_name'] == 'TrendyReports'
        assert brand['primary_color'] == DEFAULT_PRIMARY
        assert brand['accent_color'] == DEFAULT_ACCENT
        assert brand['logo_url'] is None
    
    def test_affiliate_uses_own_branding(self):
        """INDUSTRY_AFFILIATE with branding configured should use own brand"""
        cursor = Mock()
        
        # First call: Account query
        # Second call: Branding query
        cursor.fetchone.side_effect = [
            account_row(id='affiliate-456', name='Realty Partners Group', account_type='INDUSTRY_AFFILIATE'),
            # Branding row with full configuration
            branding_row(
                brand_display_name='Realty Partners Group',
                logo_url='https://cdn.example.com/rpg-logo.png',
                primary_color='#1E3A8A',
                accent_color='#F59E0B',
                rep_photo_url='https://cdn.example.com/ceo-photo.jpg',
                contact_line1='Realty Partners Group Inc.',
                contact_line2='555-1234 | partners@rpg.com',
                website_url='https://www.realtypartners.example',
            )
        ]
        
        brand = get_brand_for_account(cursor, 'affiliate-456')
        
        assert brand['display_name'] == 'Realty Partners Group'
        assert brand['logo_url'] == 'https://cdn.example.com/rpg-logo.png'
        assert brand['primary_color'] == '#1E3A8A'
        assert brand['accent_color'] == '#F59E0B'
        assert brand['rep_photo_url'] == 'https://cdn.example.com/ceo-photo.jpg'
        assert brand['contact_line1'] == 'Realty Partners Group Inc.'
        assert brand['contact_line2'] == '555-1234 | partners@rpg.com'
        assert brand['website_url'] == 'https://www.realtypartners.example'
    
    def test_affiliate_without_branding_uses_account_name(self):
        """INDUSTRY_AFFILIATE without branding row should use account name"""
        cursor = Mock()

        cursor.fetchone.side_effect = [
            account_row(id='affiliate-new', name='NewCo Realty',
                        account_type='INDUSTRY_AFFILIATE'),
            None  # No branding row yet
        ]

        brand = get_brand_for_account(cursor, 'affiliate-new')

        # Should use account name, not "TrendyReports"
        assert brand['display_name'] == 'NewCo Realty'
        assert brand['primary_color'] == DEFAULT_PRIMARY  # Default colors
        assert brand['accent_color'] == DEFAULT_ACCENT
        assert brand['logo_url'] is None

    def test_a_sponsored_regular_account_uses_its_OWN_branding(self):
        """
        THE SPONSOR FALLBACK WAS REMOVED, AND THIS TEST USED TO ASSERT IT.

        It was called `test_sponsored_regular_uses_affiliate_brand` and checked
        that a REGULAR agent sponsored by an affiliate renders the SPONSOR's
        brand. `get_brand_for_account` now routes every REGULAR account —
        "sponsored or not" in its own words — to `_get_regular_user_brand`,
        which reads the accounts table and never looks at a sponsor. The
        `sponsor_account_id` column was dropped from the account query in the
        same change.

        So this is not a defect to file: it is a product decision the test
        outlived. Rewritten to assert what the code documents, rather than
        xfailed, because nothing is pending — there is no version of this that
        comes back.
        """
        cursor = Mock()
        cursor.fetchone.side_effect = [
            account_row(id='agent-789', name='Agent Smith', account_type='REGULAR'),
            # _get_regular_user_brand's own 11-column accounts+avatar query
            ('Agent Smith', None, None, None, None,
             '#123456', '#654321', 'Agent Smith Realty', '555-0100',
             'https://agentsmith.example', None),
        ]

        brand = get_brand_for_account(cursor, 'agent-789')

        assert brand['display_name'] == 'Agent Smith'
        assert brand['primary_color'] == '#123456'

    def test_a_regular_account_with_no_branding_row_falls_back_to_defaults(self):
        """
        Was `test_sponsored_agent_without_sponsor_branding_uses_sponsor_name`,
        and asserted the sponsor's NAME as the display name. Same removal as
        above: with no sponsor lookup left, an account whose branding query
        returns nothing gets the house defaults.
        """
        cursor = Mock()
        cursor.fetchone.side_effect = [
            account_row(id='agent-101', name='Agent Jones', account_type='REGULAR'),
            None,
        ]

        brand = get_brand_for_account(cursor, 'agent-101')

        assert brand['primary_color'] == DEFAULT_PRIMARY
        assert brand['accent_color'] == DEFAULT_ACCENT
    
    def test_account_not_found_returns_default(self):
        """If account doesn't exist, should return TrendyReports default"""
        cursor = Mock()
        cursor.fetchone.return_value = None
        
        brand = get_brand_for_account(cursor, 'nonexistent-account')
        
        assert brand['display_name'] == 'TrendyReports'
        assert brand['primary_color'] == DEFAULT_PRIMARY
        assert brand['accent_color'] == DEFAULT_ACCENT
    
    def test_branding_with_partial_colors(self):
        """Branding row with null colors should use defaults"""
        cursor = Mock()
        
        cursor.fetchone.side_effect = [
            account_row(id='affiliate-partial', name='Partial Branding Co', account_type='INDUSTRY_AFFILIATE'),
            branding_row(
                brand_display_name='Partial Branding Co',
                logo_url='https://example.com/logo.png',
                primary_color=None,
                accent_color=None,
                rep_photo_url=None,
                contact_line1='Contact Info',
                contact_line2=None,
                website_url=None,
            )
        ]
        
        brand = get_brand_for_account(cursor, 'affiliate-partial')
        
        assert brand['display_name'] == 'Partial Branding Co'
        # Should fall back to defaults when colors are null
        assert brand['primary_color'] == DEFAULT_PRIMARY
        assert brand['accent_color'] == DEFAULT_ACCENT


class TestBrandResolutionEdgeCases:
    """Edge cases and complex scenarios"""
    
    def test_nested_sponsorship_uses_direct_sponsor(self):
        """If sponsor relationships are nested, use immediate sponsor"""
        cursor = Mock()
        
        # Agent is sponsored by affiliate (simple case, not double-nested)
        cursor.fetchone.side_effect = [
            account_row(id='agent-nested', name='Nested Agent', account_type='REGULAR'),
            branding_row(
                brand_display_name='Direct Sponsor Brand',
                logo_url='https://example.com/direct.png',
                primary_color='#000000',
                accent_color='#FFFFFF',
                rep_photo_url=None,
                contact_line1=None,
                contact_line2=None,
                website_url=None,
            )
        ]
        
        brand = get_brand_for_account(cursor, 'agent-nested')
        
        # Should use direct sponsor's brand
        assert brand['display_name'] == 'Direct Sponsor Brand'
        assert brand['logo_url'] == 'https://example.com/direct.png'
    
    def test_regular_account_with_null_sponsor_id(self):
        """REGULAR account with sponsor_account_id explicitly null"""
        cursor = Mock()
        
        cursor.fetchone.side_effect = [
            account_row(id='regular-no-sponsor', name='Independent Agent', account_type='REGULAR'),
            None  # No branding
        ]
        
        brand = get_brand_for_account(cursor, 'regular-no-sponsor')
        
        # Should use TrendyReports default
        assert brand['display_name'] == 'TrendyReports'
    
    def test_affiliate_with_empty_logo_url(self):
        """Branding with empty string logo_url should be None"""
        cursor = Mock()
        
        cursor.fetchone.side_effect = [
            account_row(id='affiliate-no-logo', name='No Logo Realty', account_type='INDUSTRY_AFFILIATE'),
            branding_row(
                brand_display_name='No Logo Realty',
                logo_url='',
                primary_color='#FF0000',
                accent_color='#00FF00',
                rep_photo_url=None,
                contact_line1=None,
                contact_line2=None,
                website_url=None,
            )
        ]
        
        brand = get_brand_for_account(cursor, 'affiliate-no-logo')
        
        # Empty string should be treated as None/null
        assert brand['logo_url'] == ''  # Or could normalize to None


class TestValidateBrandInput:
    """Tests for brand input validation"""
    
    def test_valid_brand_input(self):
        """Complete valid brand data should pass validation"""
        data = {
            'brand_display_name': 'Test Realty',
            'logo_url': 'https://example.com/logo.png',
            'primary_color': '#7C3AED',
            'accent_color': '#F26B2B',
            'rep_photo_url': 'https://example.com/rep.jpg',
            'contact_line1': 'Test Realty Inc.',
            'contact_line2': '555-1234',
            'website_url': 'https://example.com'
        }
        
        is_valid, error = validate_brand_input(data)
        
        assert is_valid is True
        assert error is None
    
    def test_missing_brand_display_name(self):
        """Brand without display_name should fail validation"""
        data = {
            'primary_color': '#7C3AED'
        }
        
        is_valid, error = validate_brand_input(data)
        
        assert is_valid is False
        assert 'brand_display_name' in error
        assert 'required' in error.lower()
    
    def test_empty_brand_display_name(self):
        """Empty brand_display_name should fail validation"""
        data = {
            'brand_display_name': '   ',  # Whitespace only
            'primary_color': '#7C3AED'
        }
        
        is_valid, error = validate_brand_input(data)
        
        assert is_valid is False
        assert 'brand_display_name' in error
    
    def test_invalid_hex_color_no_hash(self):
        """Hex color without # should fail validation"""
        data = {
            'brand_display_name': 'Test',
            'primary_color': '7C3AED'  # Missing #
        }
        
        is_valid, error = validate_brand_input(data)
        
        assert is_valid is False
        assert 'primary_color' in error
        assert 'hex' in error.lower()
    
    def test_invalid_hex_color_invalid_chars(self):
        """Hex color with invalid characters should fail"""
        data = {
            'brand_display_name': 'Test',
            'accent_color': '#GGGGGG'  # G is not hex
        }
        
        is_valid, error = validate_brand_input(data)
        
        assert is_valid is False
        assert 'accent_color' in error
    
    def test_invalid_hex_color_wrong_length(self):
        """Hex color with wrong length should fail"""
        data = {
            'brand_display_name': 'Test',
            'primary_color': '#7C3'  # 3 chars is OK (short form)
        }
        
        is_valid, error = validate_brand_input(data)
        
        # 3-char hex is valid (#RGB)
        assert is_valid is True
    
    def test_short_hex_color_valid(self):
        """3-character hex colors (#RGB) should be valid"""
        data = {
            'brand_display_name': 'Test',
            'primary_color': '#F0A',
            'accent_color': '#123'
        }
        
        is_valid, error = validate_brand_input(data)
        
        assert is_valid is True
    
    def test_null_optional_fields_valid(self):
        """Only brand_display_name is required, others can be null"""
        data = {
            'brand_display_name': 'Minimal Brand'
        }
        
        is_valid, error = validate_brand_input(data)
        
        assert is_valid is True
    
    def test_empty_color_strings_valid(self):
        """Empty string colors should be treated as null (valid)"""
        data = {
            'brand_display_name': 'Test',
            'primary_color': '',
            'accent_color': ''
        }
        
        is_valid, error = validate_brand_input(data)
        
        # Empty strings should be valid (treated as "not provided")
        assert is_valid is True


class TestBrandIntegration:
    """Integration tests for brand resolution"""
    
    def test_full_affiliate_workflow(self):
        """Test complete affiliate branding workflow"""
        cursor = Mock()
        
        # Affiliate creates account → uses default name
        cursor.fetchone.side_effect = [
            account_row(id='new-affiliate', name='Elite Properties', account_type='INDUSTRY_AFFILIATE'),
            None  # No branding yet
        ]
        
        brand_initial = get_brand_for_account(cursor, 'new-affiliate')
        assert brand_initial['display_name'] == 'Elite Properties'
        
        # Affiliate sets up branding
        cursor.fetchone.side_effect = [
            account_row(id='new-affiliate', name='Elite Properties', account_type='INDUSTRY_AFFILIATE'),
            branding_row(
                brand_display_name='Elite Properties Group',
                logo_url='https://example.com/elite-logo.png',
                primary_color='#2D3748',
                accent_color='#ED8936',
                rep_photo_url='https://example.com/broker.jpg',
                contact_line1='Elite Properties Group LLC',
                contact_line2='(555) 123-4567',
                website_url='https://www.eliteproperties.example',
            )
        ]
        
        brand_updated = get_brand_for_account(cursor, 'new-affiliate')
        assert brand_updated['display_name'] == 'Elite Properties Group'
        assert brand_updated['logo_url'] is not None
    
    def test_agent_sees_sponsor_brand_in_reports(self):
        """Sponsored agent's reports should show sponsor brand"""
        cursor = Mock()
        
        # Agent account (sponsored)
        cursor.fetchone.side_effect = [
            account_row(id='agent-sarah', name='Sarah Johnson', account_type='REGULAR'),
            # Sponsor's full branding
            branding_row(
                brand_display_name='Elite Realty Network',
                logo_url='https://example.com/ern-logo.png',
                primary_color='#1A365D',
                accent_color='#DD6B20',
                rep_photo_url=None,
                contact_line1='Elite Realty Network',
                contact_line2='Contact: info@eliterealty.example',
                website_url='https://eliterealty.example',
            )
        ]
        
        brand = get_brand_for_account(cursor, 'agent-sarah')
        
        # Agent's clients see Elite Realty Network, not "Sarah Johnson"
        assert brand['display_name'] == 'Elite Realty Network'
        assert 'Sarah' not in brand['display_name']

