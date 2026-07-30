"""
ThreatLens AI — File Upload & Analysis Tests
Tests for file upload, analysis retrieval, and listing.
"""

import io
import pytest
from httpx import AsyncClient

from app.models.file_analysis import FileAnalysis


# ─── File Upload ───────────────────────────────────────────────────

class TestFileUpload:
    """Test file upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_requires_auth(self, client: AsyncClient):
        """Test upload returns 401 without authentication."""
        files = {"file": ("test.exe", io.BytesIO(b"MZ" + b"\x00" * 100), "application/octet-stream")}
        response = await client.post("/api/v1/files/upload", files=files)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_success(self, client: AsyncClient, test_user, auth_headers):
        """Test successful file upload and analysis trigger."""
        file_content = b"MZ" + b"\x90" * 500  # Minimal PE stub
        files = {"file": ("suspicious.exe", io.BytesIO(file_content), "application/octet-stream")}
        response = await client.post("/api/v1/files/upload", files=files, headers=auth_headers)
        # Should succeed (201) or return the analysis response
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["original_name"] == "suspicious.exe"
        assert "md5_hash" in data
        assert "sha256_hash" in data

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client: AsyncClient, test_user, auth_headers):
        """Test upload rejects empty files."""
        files = {"file": ("empty.exe", io.BytesIO(b""), "application/octet-stream")}
        response = await client.post("/api/v1/files/upload", files=files, headers=auth_headers)
        # Should fail with validation error
        assert response.status_code in [400, 422]


# ─── File Analysis Retrieval ───────────────────────────────────────

class TestFileAnalysis:
    """Test file analysis retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_get_analysis_success(
        self, client: AsyncClient, test_user, auth_headers, sample_file_analysis
    ):
        """Test retrieving a specific file analysis."""
        response = await client.get(
            f"/api/v1/files/{sample_file_analysis.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_file_analysis.id
        assert data["original_name"] == "suspicious.exe"
        assert data["status"] == "completed"
        assert data["risk_score"] == 65.0

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(self, client: AsyncClient, test_user, auth_headers):
        """Test 404 for non-existent analysis."""
        response = await client.get("/api/v1/files/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_analysis_requires_auth(self, client: AsyncClient):
        """Test analysis retrieval requires authentication."""
        response = await client.get("/api/v1/files/1")
        assert response.status_code == 401


# ─── File Listing ──────────────────────────────────────────────────

class TestFileListing:
    """Test file analysis listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_analyses_empty(self, client: AsyncClient, test_user, auth_headers):
        """Test listing when no analyses exist."""
        response = await client.get("/api/v1/files/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_analyses_with_data(
        self, client: AsyncClient, test_user, auth_headers, sample_file_analysis
    ):
        """Test listing with existing analyses."""
        response = await client.get("/api/v1/files/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["files"]) >= 1

    @pytest.mark.asyncio
    async def test_list_analyses_pagination(self, client: AsyncClient, test_user, auth_headers):
        """Test pagination parameters work."""
        response = await client.get(
            "/api/v1/files/?page=1&page_size=5",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_list_analyses_requires_auth(self, client: AsyncClient):
        """Test listing requires authentication."""
        response = await client.get("/api/v1/files/")
        assert response.status_code == 401
