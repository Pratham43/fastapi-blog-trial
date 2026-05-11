
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from schemas.post_schema import PostResponse
from models import models
from sqlalchemy import select
from sqlalchemy.orm import Session



from config import Settings
from db.database import get_db, engine, Base
from schemas.user_schema import UserCreate, UserResponse

user_router = APIRouter(prefix="/api/v1/users", tags=["users"])

@user_router.post(
    "/api/v1/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    result = db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    existing_username = result.scalars().first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    result = db.execute(
        select(models.User).where(models.User.email == user.email)
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    new_user = models.User(
        username=user.username,
        email=user.email
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    result = db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@user_router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> list[PostResponse]:
    result = db.execute(
        select(models.User).where(models.User.id == user_id)
    )

    user = result.scalars().first() 
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts