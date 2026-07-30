"""
ThreatLens AI — Test Fixtures & Configuration
Shared fixtures for pytest: in-memory SQLite database, test client, auth helpers.
"""

import os
import sys
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override database URL BEFORE importing the app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "test-secret-key-for-jwt"
os.environ["DEBUG"] = "false"

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.file_analysis import FileAnalysis
from app.models.classification import ClassificationResult
from app.models.threat import ThreatIncident
from app.models.alert import Alert


# ─── Test Database ─────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override the app's get_db dependency with test database."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Fixtures ──────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create tables, yield a session, then tear down."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Create an async test client with DB override."""
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        email="testuser@threatlens.ai",
        username="testuser",
        hashed_password=hash_password("TestPass123!"),
        full_name="Test User",
        role="security_analyst",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user in the database."""
    user = User(
        email="admin@threatlens.ai",
        username="adminuser",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin User",
        role="administrator",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generate auth headers for the test user."""
    token = create_access_token({"sub": str(test_user.id), "role": test_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """Generate auth headers for the admin user."""
    token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def sample_file_analysis(db_session: AsyncSession, test_user: User) -> FileAnalysis:
    """Create a sample file analysis record."""
    analysis = FileAnalysis(
        filename="test_sample.exe",
        original_name="suspicious.exe",
        file_size=102400,
        file_type="PE32 executable",
        mime_type="application/x-dosexec",
        md5_hash="d41d8cd98f00b204e9800998ecf8427e",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        status="completed",
        risk_score=65.0,
        risk_level="High",
        storage_path="/uploads/test_sample.exe",
        uploaded_by=test_user.id,
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    return analysis


@pytest_asyncio.fixture(scope="function")
async def sample_classification(
    db_session: AsyncSession, sample_file_analysis: FileAnalysis
) -> ClassificationResult:
    """Create a sample classification result."""
    classification = ClassificationResult(
        file_analysis_id=sample_file_analysis.id,
        malware_class="Trojan",
        malware_family="GenericTrojan",
        confidence_score=0.87,
        risk_score=72.5,
        model_version="v1_test",
        class_probabilities='{"Clean": 0.03, "Trojan": 0.87, "Ransomware": 0.05, "Adware": 0.02, "Worm": 0.01, "Spyware": 0.01, "Backdoor": 0.01}',
    )
    db_session.add(classification)
    await db_session.commit()
    await db_session.refresh(classification)
    return classification


@pytest_asyncio.fixture(scope="function")
async def sample_alert(db_session: AsyncSession) -> Alert:
    """Create a sample alert."""
    alert = Alert(
        title="High-risk file detected",
        description="File suspicious.exe classified as Trojan with 87% confidence",
        severity="High",
        status="new",
        source="ml_classification",
        alert_type="malware_detection",
        is_read=False,
    )
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)
    return alert
