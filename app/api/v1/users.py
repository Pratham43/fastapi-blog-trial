
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, status, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from PIL import UnidentifiedImageError

from schemas.user_schema import UserCreate, UserPublic, UserPrivate, UserUpdate, Token
from schemas.post_schema import PostResponse, PaginatedPostsResponse
from models import models
from sqlalchemy import func, select, selectinload
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from fastapi.security import OAuth2PasswordRequestForm

from utils.auth import (
    CurrentUser,
    create_access_token,
    hash_password,
    verify_password,
)

from utils.image_handler import (
    delete_profile_image,
    process_profile_image
)


from config import Settings
from db.database import get_db, engine, Base


user_router = APIRouter(prefix="/api/v1/users", tags=["users"])

@user_router.post(
    "/api/v1/users",
    response_model=UserPrivate,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserPrivate:
    result = await db.execute(
        select(models.User).where(func.lower(models.User.username) == user.username.lower())
    )
    existing_username = result.scalars().first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    result = db.execute(
        select(models.User).where(func.lower(models.User.email) == user.email.lower())
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        password_hash = hash_password(user.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user



@user_router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower()
        )
    )
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@user_router.get("/me", response_model=UserPrivate)
async def get_current_user(
    current_user: CurrentUser
) -> UserPrivate:
    """To Get Currently Authenticated User"""
    return current_user

@user_router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserPublic:
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@user_router.get("/{user_id}/posts", response_model=PaginatedPostsResponse)
async def get_user_posts(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10
) -> list[PostResponse]:
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )

    user = result.scalars().first() 
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    count_result = await db.execute(
        select(func.count())
        .select_from(models.Post)
        .where(models.Post.user_id == user_id)
    )
    
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()
    has_more = (len(posts) + skip) < total
    result = await db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return PaginatedPostsResponse(
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more
    )


@user_router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to update this user"
        )
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="User Not Found"
        )
    
    if user_update.username is not None and user_update.username.lower() != user.username.lower():
        result = await db.execute(
            select(models.User).where(func.lower(models.User.username) == user_update.username.lower())
        )

        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail="Username aleady exists"
            )
        
    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        result = db.execute(
            select(models.User).where(func.lower(models.User.email) == user_update.email.lower())
        )

        existing_email = result.scalars().first()

        if existing_email:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail="Email aleady exists"
            )

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data:
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user

@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to delete this user"
        )
    result = await db.execute(select(models.User).where(models.User.user_id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Not Found"
        )
    
    old_filename = user.image_file

    
    await db.delete(user)
    await db.commit()

    if old_filename:
        delete_profile_image(old_filename)


@user_router.patch("/{user_id}/picture", response_model=UserPrivate)
async def upload_profile_picture(
    user_id: int,
    file: UploadFile,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to delete this user's picture"
        )
    
    content = await file.read()

    if len(content) > Settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {Settings.max_upload_size_bytes// (1024*1024)}MB"
        )
    
    try:
        new_filename = await run_in_threadpool(process_profile_image, content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid Image (JPEG, PNG, GIF, WebP)."
        ) from err
    
    old_filename = current_user.image_file

    current_user.image_file = new_filename
    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_image(old_filename)

    return current_user


@user_router.delete("/{user_id}/picture", response_model=UserPrivate)
async def delete_user_picture(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to delete this user's picture"
        )
    
    old_filename = current_user.image_file

    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture to delete"
        )
    
    

    current_user.image_file = None 
    await db.commit()
    await db.refresh(current_user)

    delete_profile_image(old_filename)

    return current_user