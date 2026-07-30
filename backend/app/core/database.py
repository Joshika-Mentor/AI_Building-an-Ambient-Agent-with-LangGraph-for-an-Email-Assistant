"""
ThreatLens AI - Database Connections
PostgreSQL (SQLAlchemy async), MongoDB (Motor), Redis.
Supports SQLite (aiosqlite) for local development.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from app.core.config import settings


# ─── SQLAlchemy (PostgreSQL / SQLite) ──────────────────────────────

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = {
    "echo": settings.DEBUG,
}

if not _is_sqlite:
    # Pool settings only apply to connection-pooled backends (PostgreSQL, etc.)
    _engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db():
    """Dependency: yield a PostgreSQL async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── MongoDB (Motor) ──────────────────────────────────────────────

mongo_client: AsyncIOMotorClient = None
mongo_db = None


async def connect_mongo():
    """Initialize MongoDB connection on app startup."""
    global mongo_client, mongo_db
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongo_db = mongo_client[settings.MONGODB_DB_NAME]


async def close_mongo():
    """Close MongoDB connection on app shutdown."""
    global mongo_client
    if mongo_client:
        mongo_client.close()


async def get_mongo():
    """Dependency: return MongoDB database instance."""
    return mongo_db


# ─── Redis ─────────────────────────────────────────────────────────

redis_client: Redis = None


async def connect_redis():
    """Initialize Redis connection on app startup."""
    global redis_client
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis():
    """Close Redis connection on app shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_redis():
    """Dependency: return Redis client instance."""
    return redis_client


# ─── Init All ──────────────────────────────────────────────────────

async def init_databases():
    """Initialize all database connections."""
    await connect_mongo()
    await connect_redis()


async def close_databases():
    """Close all database connections."""
    await close_mongo()
    await close_redis()
