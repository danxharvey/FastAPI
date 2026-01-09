# Import libraries
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt

from app.auth.utils import (
    create_access_token,
    decode_access_token,
    get_current_user,
    require_role,
)
from app.config import config


# Helper function for creating test tokens
def create_test_token(username: str, role: str = "user"):
    """Helper to create a test JWT token."""
    return create_access_token(data={"sub": username, "role": role})


class TestCreateAccessToken:
    """Test suite for create_access_token function."""

    def test_create_token_success(self):
        """Test successful token creation."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_expiry(self):
        """Test that token contains expiration claim."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)

        # Decode without verification to check payload
        payload = jwt.decode(token, key="", options={"verify_signature": False})
        assert "exp" in payload
        assert "sub" in payload
        assert "role" in payload

    def test_token_expiry_time(self):
        """Test that token expiry is set correctly."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)

        payload = jwt.decode(token, key="", options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + timedelta(
            minutes=config["jwt_exp_minutes"]
        )

        # Allow 5 second tolerance for test execution time
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5

    def test_token_preserves_custom_data(self):
        """Test that custom data is preserved in token."""
        data = {"sub": "testuser", "role": "admin", "custom": "value"}
        token = create_access_token(data)

        payload = jwt.decode(token, key="", options={"verify_signature": False})
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
        assert payload["custom"] == "value"


class TestDecodeAccessToken:
    """Test suite for decode_access_token function."""

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)

        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"
        assert payload["role"] == "user"
        assert "exp" in payload

    def test_decode_invalid_token_raises_exception(self):
        """Test that invalid token raises HTTPException."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(invalid_token)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in str(exc_info.value.detail)

    def test_decode_expired_token_raises_exception(self):
        """Test that expired token raises HTTPException."""
        # Create expired token manually
        expired_data = {
            "sub": "testuser",
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(
            expired_data, config["jwt_secret"], algorithm=config["jwt_algorithm"]
        )

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(expired_token)

        assert exc_info.value.status_code == 401

    def test_decode_wrong_secret_raises_exception(self):
        """Test that token with wrong secret raises exception."""
        data = {"sub": "testuser", "role": "user"}
        wrong_secret_token = jwt.encode(
            data, "wrong_secret", algorithm=config["jwt_algorithm"]
        )

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(wrong_secret_token)

        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    """Test suite for get_current_user function."""

    def test_get_current_user_success(self, mock_request):
        """Test successful user extraction from valid token."""
        token = create_test_token("testuser", "user")
        mock_request.cookies = {"access_token": token}

        user_info = get_current_user(mock_request)

        assert user_info == {"username": "testuser", "role": "user"}

    def test_get_current_user_no_token_raises_exception(self, mock_request):
        """Test that missing token raises HTTPException."""
        mock_request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_request)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in str(exc_info.value.detail)

    def test_get_current_user_invalid_token_raises_exception(self, mock_request):
        """Test that invalid token raises HTTPException."""
        mock_request.cookies = {"access_token": "invalid.token"}

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_request)

        assert exc_info.value.status_code == 401

    def test_get_current_user_missing_username_raises_exception(self, mock_request):
        """Test that token without username raises exception."""
        # Create token without 'sub' field
        invalid_data = {
            "role": "user",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        token = jwt.encode(
            invalid_data, config["jwt_secret"], algorithm=config["jwt_algorithm"]
        )
        mock_request.cookies = {"access_token": token}

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_request)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication payload" in str(exc_info.value.detail)

    def test_get_current_user_missing_role_raises_exception(self, mock_request):
        """Test that token without role raises exception."""
        # Create token without 'role' field
        invalid_data = {
            "sub": "testuser",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        token = jwt.encode(
            invalid_data, config["jwt_secret"], algorithm=config["jwt_algorithm"]
        )
        mock_request.cookies = {"access_token": token}

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_request)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication payload" in str(exc_info.value.detail)

    def test_get_current_user_with_admin_role(self, mock_request):
        """Test extraction of admin user."""
        token = create_test_token("adminuser", "admin")
        mock_request.cookies = {"access_token": token}

        user_info = get_current_user(mock_request)

        assert user_info == {"username": "adminuser", "role": "admin"}


class TestRequireRole:
    """Test suite for require_role function."""

    def test_require_role_admin_success(self, mock_request):
        """Test that admin role check passes for admin user."""
        token = create_test_token("adminuser", "admin")
        mock_request.cookies = {"access_token": token}

        role_checker = require_role("admin")
        current_user = get_current_user(mock_request)
        result = role_checker(current_user)

        assert result == current_user

    def test_require_role_admin_fails_for_user(self, mock_request):
        """Test that admin role check fails for regular user."""
        token = create_test_token("testuser", "user")
        mock_request.cookies = {"access_token": token}

        role_checker = require_role("admin")
        current_user = get_current_user(mock_request)

        with pytest.raises(HTTPException) as exc_info:
            role_checker(current_user)

        assert exc_info.value.status_code == 403
        assert "Requires admin role" in str(exc_info.value.detail)

    def test_require_role_user_success(self, mock_request):
        """Test that user role check passes for regular user."""
        token = create_test_token("testuser", "user")
        mock_request.cookies = {"access_token": token}

        role_checker = require_role("user")
        current_user = get_current_user(mock_request)
        result = role_checker(current_user)

        assert result == current_user

    def test_require_role_user_fails_for_different_role(self, mock_request):
        """Test that user role check fails for admin
        trying to access user-only endpoint.
        """
        token = create_test_token("adminuser", "admin")
        mock_request.cookies = {"access_token": token}

        role_checker = require_role("user")
        current_user = get_current_user(mock_request)

        with pytest.raises(HTTPException) as exc_info:
            role_checker(current_user)

        assert exc_info.value.status_code == 403
        assert "Requires user role" in str(exc_info.value.detail)
