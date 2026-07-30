"""
ThreatLens AI — Auth Tests
Tests for registration, login, token refresh, and RBAC.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password


# ─── Registration ──────────────────────────────────────────────────

class TestRegistration:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@threatlens.ai",
            "username": "newuser",
            "password": "SecurePass123!",
            "full_name": "New User",
            "role": "security_analyst",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@threatlens.ai"
        assert data["user"]["username"] == "newuser"
        assert data["user"]["role"] == "security_analyst"
        assert data["user"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration fails with duplicate email."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "testuser@threatlens.ai",  # Already exists
            "username": "differentuser",
            "password": "SecurePass123!",
            "full_name": "Another User",
            "role": "security_analyst",
        })
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Test registration fails with duplicate username."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "different@threatlens.ai",
            "username": "testuser",  # Already exists
            "password": "SecurePass123!",
            "full_name": "Another User",
            "role": "security_analyst",
        })
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration fails with invalid email format."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "username": "baduser",
            "password": "SecurePass123!",
            "full_name": "Bad User",
            "role": "security_analyst",
        })
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration fails with password too short."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@threatlens.ai",
            "username": "newuser",
            "password": "short",  # Less than 8 chars
            "full_name": "New User",
            "role": "security_analyst",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_role(self, client: AsyncClient):
        """Test registration fails with invalid role."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@threatlens.ai",
            "username": "newuser",
            "password": "SecurePass123!",
            "full_name": "New User",
            "role": "superadmin",  # Invalid role
        })
        assert response.status_code == 422


# ─── Login ─────────────────────────────────────────────────────────

class TestLogin:
    """Test user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login with valid credentials."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "testuser@threatlens.ai",
            "password": "TestPass123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "testuser@threatlens.ai"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login fails with wrong password."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "testuser@threatlens.ai",
            "password": "WrongPassword!",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login fails with unknown email."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nobody@threatlens.ai",
            "password": "SomePass123!",
        })
        assert response.status_code == 401


# ─── Token Refresh ─────────────────────────────────────────────────

class TestTokenRefresh:
    """Test token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, client: AsyncClient, test_user):
        """Test successful token refresh."""
        refresh_token = create_refresh_token({"sub": str(test_user.id), "role": test_user.role})
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, client: AsyncClient, test_user):
        """Test refresh fails when an access token is used instead of refresh."""
        access_token = create_access_token({"sub": str(test_user.id), "role": test_user.role})
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": access_token,
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh fails with garbage token."""
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })
        assert response.status_code == 401


# ─── RBAC ──────────────────────────────────────────────────────────

class TestRBAC:
    """Test role-based access control."""

    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, client: AsyncClient):
        """Test endpoints return 401 without a token."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_access_granted(self, client: AsyncClient, test_user, auth_headers):
        """Test authenticated user can access protected endpoint."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@threatlens.ai"

    @pytest.mark.asyncio
    async def test_expired_token_denied(self, client: AsyncClient, test_user):
        """Test expired token returns 401."""
        from datetime import timedelta
        token = create_access_token(
            {"sub": str(test_user.id), "role": test_user.role},
            expires_delta=timedelta(seconds=-10),  # Already expired
        )
        response = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


# ─── JWT Utility Tests ─────────────────────────────────────────────

class TestJWTUtils:
    """Test JWT utility functions (unit tests)."""

    def test_create_and_decode_access_token(self):
        """Test token creation and decoding roundtrip."""
        data = {"sub": "42", "role": "administrator"}
        token = create_access_token(data)
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["role"] == "administrator"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        """Test refresh token creation and decoding."""
        data = {"sub": "42", "role": "researcher"}
        token = create_refresh_token(data)
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "refresh"

    def test_hash_and_verify_password(self):
        """Test password hashing and verification."""
        from app.core.security import verify_password
        hashed = hash_password("MySecretPassword!")
        assert verify_password("MySecretPassword!", hashed) is True
        assert verify_password("WrongPassword!", hashed) is False
