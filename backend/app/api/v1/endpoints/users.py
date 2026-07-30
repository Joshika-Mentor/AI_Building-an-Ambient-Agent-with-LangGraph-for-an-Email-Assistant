"""
ThreatLens AI - User Endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, role_required, UserRole
from app.schemas.user import UserResponse, UserUpdate, UserRoleUpdate, UserListResponse
from app.services.user_service import (
    get_user_profile, update_user_profile, list_users, update_user_role, deactivate_user,
)
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile."""
    return await update_user_profile(current_user.id, update_data, db)


@router.get("/", response_model=UserListResponse)
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(role_required([UserRole.ADMINISTRATOR])),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    return await list_users(db, page, page_size)


@router.put("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: User = Depends(role_required([UserRole.ADMINISTRATOR])),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role (admin only)."""
    return await update_user_role(user_id, role_data.role, db)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(role_required([UserRole.ADMINISTRATOR])),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user account (admin only)."""
    return await deactivate_user(user_id, db)
