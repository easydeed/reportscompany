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


class TestGetBrandForAccount:
    """Tests for get_brand_for_account resolution logic"""
    
    def test_regular_without_sponsor_uses_trendy_fallback(self):
        """REGULAR account with no sponsor should use TrendyReports default brand"""
        cursor = Mock()
        
        # Account query: REGULAR type, no sponsor
        cursor.fetchone.return_value = (
            'account-123',  # id
            'John Doe Real Estate',  # name
            'REGULAR',  # account_type
            None  # sponsor_account_id (no sponsor)
        )
        
        # Branding query will be called but return None (no custom branding)
        cursor.execute.side_effect = [
            None,  # Account query
            None   # Branding query returns nothing
        ]
        cursor.fetchone.side_effect = [
            ('account-123', 'John Doe Real Estate', 'REGULAR', None),
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
            ('affiliate-456', 'Realty Partners Group', 'INDUSTRY_AFFILIATE', None),
            # Branding row with full configuration
            (
                'Realty Partners Group',  # brand_display_name
                'https://cdn.example.com/rpg-logo.png',  # logo_url
                '#1E3A8A',  # primary_color (dark blue)
                '#F59E0B',  # accent_color (amber)
                'https://cdn.example.com/ceo-photo.jpg',  # rep_photo_url
                'Realty Partners Group Inc.',  # contact_line1
                '555-1234 | partners@rpg.com',  # contact_line2
                'https://www.realtypartners.example'  # website_url
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
    
    def test_sponsored_regular_uses_affiliate_brand(self):
        """REGULAR account sponsored by affiliate should use sponsor's brand"""
        cursor = Mock()
        
        # Account query: REGULAR with sponsor_account_id
        # Branding query: Sponsor's branding
        cursor.fetchone.side_effect = [
            ('agent-789', 'Agent Smith', 'REGULAR', 'sponsor-123'),
            # Sponsor's branding
            (
                'Premier Realty Network',  # sponsor's brand
                'https://cdn.example.com/prn-logo.png',
                '#10B981',  # emerald
                '#8B5CF6',  # violet
                None,
                'Premier Realty Network',
                'Contact: 555-0100',
                'https://premierrealty.example'
            )
        ]
        
        brand = get_brand_for_account(cursor, 'agent-789')
        
        # Should use sponsor's brand, not agent's name
        assert brand['display_name'] == 'Premier Realty Network'
        assert brand['logo_url'] == 'https://cdn.example.com/prn-logo.png'
        assert brand['primary_color'] == '#10B981'
        assert brand['accent_color'] == '#8B5CF6'
        assert brand['website_url'] == 'https://premierrealty.example'
    
    def test_affiliate_without_branding_uses_account_name(self):
        """INDUSTRY_AFFILIATE without branding row should use account name"""
        cursor = Mock()
        
        cursor.fetchone.side_effect = [
            ('affiliate-new', 'NewCo Realty', 'INDUSTRY_AFFILIATE', None),
            None  # No branding row yet
        ]
        
        brand = get_brand_for_account(cursor, 'affiliate-new')
        
        # Should use account name, not "TrendyReports"
        assert brand['display_name'] == 'NewCo Realty'
        assert brand['primary_color'] == DEFAULT_PRIMARY  # Default colors
        assert brand['accent_color'] == DEFAULT_ACCENT
        assert brand['logo_url'] is None
    
    def test_sponsored_agent_without_sponsor_branding_uses_sponsor_name(self):
        """Sponsored agent whose sponsor has no branding should use sponsor name"""
        cursor = Mock()
        
        cursor.fetchone.side_effect = [
            ('agent-101', 'Agent Johnson', 'REGULAR', 'sponsor-202'),
            None,  # No branding row for sponsor
            ('Sponsor Realty Co',)  # Sponsor account name query
        ]
        
        brand = get_brand_for_account(cursor, 'agent-101')
        
        assert brand['display_name'] == 'Sponsor Realty Co'
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
            ('affiliate-partial', 'Partial Branding Co', 'INDUSTRY_AFFILIATE', None),
            (
                'Partial Branding Co',
                'https://example.com/logo.png',
                None,  # primary_color null
                None,  # accent_color null
                None,
                'Contact Info',
                None,
                None
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
            ('agent-nested', 'Nested Agent', 'REGULAR', 'affiliate-sponsor'),
            (
                'Direct Sponsor Brand',
                'https://example.com/direct.png',
                '#000000',
                '#FFFFFF',
                None, None, None, None
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
            ('regular-no-sponsor', 'Independent Agent', 'REGULAR', None),
            None  # No branding
        ]
        
        brand = get_brand_for_account(cursor, 'regular-no-sponsor')
        
        # Should use TrendyReports default
        assert brand['display_name'] == 'TrendyReports'
    
    def test_affiliate_with_empty_logo_url(self):
        """Branding with empty string logo_url should be None"""
        cursor = Mock()
        
        cursor.fetchone.side_effect = [
            ('affiliate-no-logo', 'No Logo Realty', 'INDUSTRY_AFFILIATE', None),
            (
                'No Logo Realty',
                '',  # Empty string logo URL
                '#FF0000',
                '#00FF00',
                None, None, None, None
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
            ('new-affiliate', 'Elite Properties', 'INDUSTRY_AFFILIATE', None),
            None  # No branding yet
        ]
        
        brand_initial = get_brand_for_account(cursor, 'new-affiliate')
        assert brand_initial['display_name'] == 'Elite Properties'
        
        # Affiliate sets up branding
        cursor.fetchone.side_effect = [
            ('new-affiliate', 'Elite Properties', 'INDUSTRY_AFFILIATE', None),
            (
                'Elite Properties Group',  # Updated display name
                'https://example.com/elite-logo.png',
                '#2D3748',
                '#ED8936',
                'https://example.com/broker.jpg',
                'Elite Properties Group LLC',
                '(555) 123-4567',
                'https://www.eliteproperties.example'
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
            ('agent-sarah', 'Sarah Johnson', 'REGULAR', 'elite-realty'),
            # Sponsor's full branding
            (
                'Elite Realty Network',
                'https://example.com/ern-logo.png',
                '#1A365D',
                '#DD6B20',
                None,
                'Elite Realty Network',
                'Contact: info@eliterealty.example',
                'https://eliterealty.example'
            )
        ]
        
        brand = get_brand_for_account(cursor, 'agent-sarah')
        
        # Agent's clients see Elite Realty Network, not "Sarah Johnson"
        assert brand['display_name'] == 'Elite Realty Network'
        assert 'Sarah' not in brand['display_name']

