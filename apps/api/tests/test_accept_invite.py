"""
Tests for the invite acceptance flow.

Phase T1.3: Backend tests for /v1/auth/accept-invite endpoint (Phase 29C).
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing"""
    with patch('psycopg.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        yield mock_conn, mock_cursor


class TestAcceptInviteSuccess:
    """Tests for successful invite acceptance"""
    
    def test_accept_invite_success(self, api_client, mock_db_connection):
        """Valid invite should set password, mark token used, and return auth"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Mock database responses
        future_expiry = datetime.now() + timedelta(days=7)
        mock_cursor.fetchone.side_effect = [
            # Token validation query
            ('user-123', 'account-456', future_expiry, None),
            # User lookup query
            ('user-123', 'agent@example.com', True)
        ]
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={
                "token": "valid-token-abc123",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data['ok'] is True
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'
        assert data['user']['id'] == 'user-123'
        assert data['user']['email'] == 'agent@example.com'
        assert data['user']['primary_account_id'] == 'account-456'
        
        # Verify database operations
        mock_cursor.execute.assert_any_call(
            pytest.approx("UPDATE users", abs=50),  # Flexible match
            pytest.approx(2)  # password_hash, user_id
        )
        mock_cursor.execute.assert_any_call(
            pytest.approx("UPDATE signup_tokens", abs=50),
            pytest.approx(1)  # token
        )
        mock_conn.commit.assert_called_once()
    
    def test_accept_invite_sets_cookie(self, api_client, mock_db_connection):
        """Accept invite should set mr_token HTTP-only cookie"""
        mock_conn, mock_cursor = mock_db_connection
        
        future_expiry = datetime.now() + timedelta(days=7)
        mock_cursor.fetchone.side_effect = [
            ('user-123', 'account-456', future_expiry, None),
            ('user-123', 'agent@example.com', True)
        ]
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "valid-token", "password": "SecurePass123!"}
        )
        
        # Verify cookie is set
        assert 'set-cookie' in response.headers or 'Set-Cookie' in response.headers
        # Cookie should be HTTP-only and secure
        cookie_header = response.headers.get('set-cookie', response.headers.get('Set-Cookie', ''))
        assert 'mr_token=' in cookie_header
        assert 'HttpOnly' in cookie_header or 'httponly' in cookie_header


class TestAcceptInviteInvalidToken:
    """Tests for invalid token scenarios"""
    
    def test_accept_invite_token_not_found(self, api_client, mock_db_connection):
        """Non-existent token should return 400"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Token query returns None
        mock_cursor.fetchone.return_value = None
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "nonexistent-token", "password": "SecurePass123!"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['detail']['error'] == 'invalid_token'
        assert 'invalid or expired' in data['detail']['message'].lower()
    
    def test_accept_invite_token_already_used(self, api_client, mock_db_connection):
        """Token that was already used should return 400"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Token exists but has used_at timestamp
        past_time = datetime.now() - timedelta(days=1)
        mock_cursor.fetchone.return_value = (
            'user-123',
            'account-456',
            datetime.now() + timedelta(days=7),
            past_time  # used_at is set
        )
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "used-token", "password": "SecurePass123!"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['detail']['error'] == 'invalid_token'
        assert 'invalid or expired' in data['detail']['message'].lower()
    
    def test_accept_invite_token_expired(self, api_client, mock_db_connection):
        """Expired token should return 400"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Token exists but expires_at is in the past
        past_time = datetime.now() - timedelta(days=1)
        mock_cursor.fetchone.return_value = (
            'user-123',
            'account-456',
            past_time,  # expires_at is in the past
            None  # not used yet
        )
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "expired-token", "password": "SecurePass123!"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['detail']['error'] == 'invalid_token'
        assert 'invalid or expired' in data['detail']['message'].lower()


class TestAcceptInvitePasswordValidation:
    """Tests for password validation"""
    
    def test_accept_invite_password_too_short(self, api_client, mock_db_connection):
        """Password shorter than 8 characters should be rejected"""
        mock_conn, mock_cursor = mock_db_connection
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "valid-token", "password": "short"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['detail']['error'] == 'invalid_password'
        assert '8 characters' in data['detail']['message']
    
    def test_accept_invite_password_exactly_8_chars(self, api_client, mock_db_connection):
        """Password with exactly 8 characters should be accepted"""
        mock_conn, mock_cursor = mock_db_connection
        
        future_expiry = datetime.now() + timedelta(days=7)
        mock_cursor.fetchone.side_effect = [
            ('user-123', 'account-456', future_expiry, None),
            ('user-123', 'agent@example.com', True)
        ]
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "valid-token", "password": "Pass1234"}  # Exactly 8
        )
        
        assert response.status_code == 200


class TestAcceptInviteUserValidation:
    """Tests for user account validation"""
    
    def test_accept_invite_user_not_found(self, api_client, mock_db_connection):
        """If user doesn't exist, should return 400"""
        mock_conn, mock_cursor = mock_db_connection
        
        future_expiry = datetime.now() + timedelta(days=7)
        mock_cursor.fetchone.side_effect = [
            # Token query succeeds
            ('nonexistent-user', 'account-456', future_expiry, None),
            # User query returns None
            None
        ]
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "orphaned-token", "password": "SecurePass123!"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['detail']['error'] == 'user_not_found'
    
    def test_accept_invite_user_inactive(self, api_client, mock_db_connection):
        """Inactive user should not be able to accept invite"""
        mock_conn, mock_cursor = mock_db_connection
        
        future_expiry = datetime.now() + timedelta(days=7)
        mock_cursor.fetchone.side_effect = [
            ('user-123', 'account-456', future_expiry, None),
            # User exists but is_active = False
            ('user-123', 'deactivated@example.com', False)
        ]
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "valid-token", "password": "SecurePass123!"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['detail']['error'] == 'account_inactive'


class TestAcceptInviteTransactionality:
    """Tests for database transaction handling"""
    
    def test_accept_invite_rolls_back_on_error(self, api_client, mock_db_connection):
        """If an error occurs, transaction should rollback"""
        mock_conn, mock_cursor = mock_db_connection
        
        future_expiry = datetime.now() + timedelta(days=7)
        mock_cursor.fetchone.side_effect = [
            ('user-123', 'account-456', future_expiry, None),
            ('user-123', 'agent@example.com', True)
        ]
        
        # Simulate error during UPDATE
        mock_cursor.execute.side_effect = [
            None,  # Token query
            None,  # User query
            Exception("Database error")  # UPDATE fails
        ]
        
        with pytest.raises(Exception):
            api_client.post(
                "/v1/auth/accept-invite",
                json={"token": "valid-token", "password": "SecurePass123!"}
            )
        
        # Commit should not have been called if error occurred
        assert mock_conn.commit.call_count == 0
    
    def test_accept_invite_commits_all_changes(self, api_client, mock_db_connection):
        """Successful invite should commit password update and token marking"""
        mock_conn, mock_cursor = mock_db_connection
        
        future_expiry = datetime.now() + timedelta(days=7)
        mock_cursor.fetchone.side_effect = [
            ('user-123', 'account-456', future_expiry, None),
            ('user-123', 'agent@example.com', True)
        ]
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "valid-token", "password": "SecurePass123!"}
        )
        
        assert response.status_code == 200
        
        # Verify both UPDATEs were called
        update_calls = [
            call for call in mock_cursor.execute.call_args_list
            if 'UPDATE' in str(call[0][0]).upper()
        ]
        assert len(update_calls) >= 2  # UPDATE users, UPDATE signup_tokens
        
        # Verify commit was called exactly once
        mock_conn.commit.assert_called_once()


class TestAcceptInviteIntegration:
    """Integration tests combining multiple scenarios"""
    
    def test_accept_invite_full_flow(self, api_client, mock_db_connection):
        """Test complete invite flow from start to finish"""
        mock_conn, mock_cursor = mock_db_connection
        
        # Setup: Valid token for a sponsored agent
        token = "affiliate-invite-abc123"
        password = "Agent2025!Secure"
        email = "new.agent@realestate.com"
        
        future_expiry = datetime.now() + timedelta(days=30)
        mock_cursor.fetchone.side_effect = [
            ('agent-user-id', 'sponsor-account-id', future_expiry, None),
            ('agent-user-id', email, True)
        ]
        
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": token, "password": password}
        )
        
        # Verify successful response
        assert response.status_code == 200
        data = response.json()
        assert data['ok'] is True
        assert data['user']['email'] == email
        assert data['user']['primary_account_id'] == 'sponsor-account-id'
        
        # Verify JWT token structure (should contain user_id and account_id)
        assert len(data['access_token']) > 20  # JWT should be reasonably long
    
    def test_accept_invite_whitespace_in_token(self, api_client, mock_db_connection):
        """Token with leading/trailing whitespace should be handled"""
        mock_conn, mock_cursor = mock_db_connection
        
        future_expiry = datetime.now() + timedelta(days=7)
        mock_cursor.fetchone.side_effect = [
            ('user-123', 'account-456', future_expiry, None),
            ('user-123', 'agent@example.com', True)
        ]
        
        # Token with whitespace
        response = api_client.post(
            "/v1/auth/accept-invite",
            json={"token": "  valid-token-with-spaces  ", "password": "SecurePass123!"}
        )
        
        # Should succeed - whitespace is stripped
        assert response.status_code == 200

