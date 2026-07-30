"""
ThreatLens AI - User Service
User profile management and admin operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserListResponse


async def get_user_profile(user_id: int, db: AsyncSession) -> UserResponse:
    """Get a user's profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


async def update_user_profile(user_id: int, update_data: UserUpdate, db: AsyncSession) -> UserResponse:
    """Update a user's profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.email is not None:
        # Check email uniqueness
        existing = await db.execute(
            select(User).where(User.email == update_data.email, User.id != user_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already in use")
        user.email = update_data.email

    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


async def list_users(
    db: AsyncSession, page: int = 1, page_size: int = 20
) -> UserListResponse:
    """List all users (admin only)."""
    offset = (page - 1) * page_size

    # Count total
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar()

    # Fetch page
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_user_role(user_id: int, new_role: str, db: AsyncSession) -> UserResponse:
    """Change a user's role (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = new_role
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


async def deactivate_user(user_id: int, db: AsyncSession) -> dict:
    """Deactivate a user account (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await db.flush()
    return {"message": f"User {user.username} has been deactivated"}
