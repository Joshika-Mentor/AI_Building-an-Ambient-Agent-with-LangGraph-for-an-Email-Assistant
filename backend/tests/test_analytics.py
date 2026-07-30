"""
ThreatLens AI — Analytics Tests
Tests for analytics endpoints: overview, distribution, trends, risk.
"""

import pytest
from httpx import AsyncClient


# ─── Analytics Overview ────────────────────────────────────────────

class TestAnalyticsOverview:
    """Test the analytics overview endpoint."""

    @pytest.mark.asyncio
    async def test_overview_requires_auth(self, client: AsyncClient):
        """Test overview returns 401 without authentication."""
        response = await client.get("/api/v1/analytics/overview")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_overview_empty(self, client: AsyncClient, test_user, auth_headers):
        """Test overview with no data returns zeroed stats."""
        response = await client.get("/api/v1/analytics/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_scans" in data
        assert "threats_detected" in data
        assert "average_risk_score" in data
        assert "active_alerts" in data
        assert "scans_today" in data
        assert "critical_alerts" in data
        assert data["total_scans"] == 0

    @pytest.mark.asyncio
    async def test_overview_with_data(
        self, client: AsyncClient, test_user, auth_headers, sample_file_analysis
    ):
        """Test overview reflects existing data."""
        response = await client.get("/api/v1/analytics/overview", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] >= 1


# ─── Malware Distribution ─────────────────────────────────────────

class TestMalwareDistribution:
    """Test malware distribution endpoint."""

    @pytest.mark.asyncio
    async def test_distribution_requires_auth(self, client: AsyncClient):
        """Test distribution endpoint requires auth."""
        response = await client.get("/api/v1/analytics/malware-distribution")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_distribution_empty(self, client: AsyncClient, test_user, auth_headers):
        """Test distribution with no classifications."""
        response = await client.get("/api/v1/analytics/malware-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "distribution" in data
        assert "total" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_distribution_with_data(
        self, client: AsyncClient, test_user, auth_headers, sample_classification
    ):
        """Test distribution reflects classification data."""
        response = await client.get("/api/v1/analytics/malware-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert "Trojan" in data["distribution"]


# ─── Threat Trends ─────────────────────────────────────────────────

class TestThreatTrends:
    """Test threat trends endpoint."""

    @pytest.mark.asyncio
    async def test_trends_requires_auth(self, client: AsyncClient):
        """Test trends endpoint requires auth."""
        response = await client.get("/api/v1/analytics/trends")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_trends_default_period(self, client: AsyncClient, test_user, auth_headers):
        """Test trends with default 30d period."""
        response = await client.get("/api/v1/analytics/trends", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert "period" in data
        assert data["period"] == "30d"

    @pytest.mark.asyncio
    async def test_trends_custom_period(self, client: AsyncClient, test_user, auth_headers):
        """Test trends with 7d period."""
        response = await client.get("/api/v1/analytics/trends?period=7d", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "7d"

    @pytest.mark.asyncio
    async def test_trends_with_data(
        self, client: AsyncClient, test_user, auth_headers, sample_file_analysis
    ):
        """Test trends include analysis data."""
        response = await client.get("/api/v1/analytics/trends?period=90d", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should have at least one data point from the sample
        assert isinstance(data["trends"], list)


# ─── Risk Distribution ────────────────────────────────────────────

class TestRiskDistribution:
    """Test risk score distribution endpoint."""

    @pytest.mark.asyncio
    async def test_risk_distribution_requires_auth(self, client: AsyncClient):
        """Test risk distribution requires auth."""
        response = await client.get("/api/v1/analytics/risk-distribution")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_risk_distribution_empty(self, client: AsyncClient, test_user, auth_headers):
        """Test risk distribution with no data."""
        response = await client.get("/api/v1/analytics/risk-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "clean" in data
        assert "low" in data
        assert "medium" in data
        assert "high" in data
        assert "critical" in data

    @pytest.mark.asyncio
    async def test_risk_distribution_with_data(
        self, client: AsyncClient, test_user, auth_headers, sample_file_analysis
    ):
        """Test risk distribution reflects file analysis data."""
        response = await client.get("/api/v1/analytics/risk-distribution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Sample has risk_score=65 → "high" bucket
        total = data["clean"] + data["low"] + data["medium"] + data["high"] + data["critical"]
        assert total >= 1


# ─── Health Check ──────────────────────────────────────────────────

class TestHealthCheck:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_root_health(self, client: AsyncClient):
        """Test root health check endpoint (no auth required)."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["name"] == "ThreatLens AI"

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test detailed health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
