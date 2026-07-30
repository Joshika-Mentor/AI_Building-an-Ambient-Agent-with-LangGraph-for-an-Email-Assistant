"""
ThreatLens AI - Security Module
JWT authentication, password hashing, and Role-Based Access Control.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import get_db
import enum


# ─── Password Hashing ─────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Token Management ─────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── Role Definitions ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    SECURITY_ANALYST = "security_analyst"
    SOC_MEMBER = "soc_member"
    ADMINISTRATOR = "administrator"
    RESEARCHER = "researcher"


# Permission matrix: maps each role to its allowed permissions
ROLE_PERMISSIONS = {
    UserRole.SECURITY_ANALYST: [
        "upload_files", "run_analysis", "view_reports", "access_dashboards",
        "monitor_logs", "review_alerts", "generate_reports",
    ],
    UserRole.SOC_MEMBER: [
        "monitor_logs", "view_reports", "access_dashboards",
        "track_incidents", "review_alerts", "generate_reports",
    ],
    UserRole.ADMINISTRATOR: [
        "upload_files", "run_analysis", "view_reports", "access_dashboards",
        "monitor_logs", "review_alerts", "generate_reports",
        "manage_users", "manage_roles", "configure_platform",
        "manage_integrations", "manage_policies", "export_reports",
    ],
    UserRole.RESEARCHER: [
        "upload_files", "run_analysis", "view_reports", "access_dashboards",
        "access_datasets", "analyze_families", "export_reports",
        "access_history",
    ],
}


# ─── Auth Dependencies ─────────────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Dependency: decode JWT and return the current user from the database."""
    from app.models.user import User

    payload = decode_token(token)
    user_id: str = payload.get("sub")
    token_type: str = payload.get("type")

    if user_id is None or token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


def role_required(allowed_roles: List[UserRole]):
    """
    Dependency factory: restrict endpoint access to specific roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(role_required([UserRole.ADMINISTRATOR]))])
    """
    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return role_checker


def permission_required(permission: str):
    """
    Dependency factory: restrict endpoint access by permission.

    Usage:
        @router.post("/upload", dependencies=[Depends(permission_required("upload_files"))])
    """
    async def permission_checker(current_user=Depends(get_current_user)):
        user_role = UserRole(current_user.role)
        if permission not in ROLE_PERMISSIONS.get(user_role, []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have the '{permission}' permission",
            )
        return current_user
    return permission_checker
