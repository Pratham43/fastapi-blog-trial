
from datetime import timedelta, UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, status, Query, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from PIL import UnidentifiedImageError

from app.schemas.user_schema import UserCreate, UserPublic, UserPrivate, UserUpdate, Token, ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.post_schema import PostResponse, PaginatedPostsResponse
from app.models import models
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from sqlalchemy import delete as sql_delete

from fastapi.security import OAuth2PasswordRequestForm

from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.utils.auth import (
    CurrentUser,
    create_access_token,
    hash_password,
    verify_password,
    generate_reset_token,
    hash_reset_token
)

from botocore.exceptions import ClientError

from app.utils.email_handler import send_password_reset_email


from app.config import settings
from app.db.database import get_db, engine, Base
from app.dependencies.services import get_user_service
from app.dependencies.services import get_auth_service


user_router = APIRouter(prefix="/api/v1/user", tags=["users"])

@user_router.post(
    "/register",
    response_model=UserPrivate,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user: UserCreate,
    service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
):
    return await service.register(
        user
    )


@user_router.post(
    "/token",
    response_model=Token,
)
async def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    service: Annotated[
        AuthService,
        Depends(get_auth_service),
    ],
):
    return await service.login(
        email=form_data.username,
        password=form_data.password,
    )

@user_router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
): 
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == request_data.email.lower(),
        )
    )
    
    user = result.scalars().first()
    
    if user:
        await db.execute(
            sql_delete(models.PasswordResetToken).where(
                models.PasswordResetToken.user_id == user.id,
            ),
        )
        token = generate_reset_token()
        token_hash = hash_reset_token(token)
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.reset_token_expire_minutes
        )
        
        reset_token = models.PasswordResetToken(
            user_id = user.id,
            token_hash = token_hash,
            expires_at = expires_at,
        )
        
        db.add(reset_token)
        await db.commit()
        
        background_tasks.add_task(
            send_password_reset_email,
            to_email=user.email,
            username=user.username,
            token=token
        )
        
        return {
            "message" : "If an account exists with this email, you will recieve the instructions over email for resetting the password."
        }

@user_router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    token_hash = hash_reset_token(request_data.token)
    
    result = await db.execute(
        select(models.PasswordResetToken).where(
            models.PasswordResetToken.token_hash == token_hash,
        ),
    )
    
    reset_token = result.scalars().first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )

    if reset_token.expires_at < datetime.now(UTC):
        await db.delete(reset_token)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )
        
    result = await db.execute(
        select(models.User).where(
            models.User.id == reset_token.user_id
        )
    )
    
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )
        
    user.password_hash = hash_password(request_data.new_passowrd)
    
    await db.execute(
        sql_delete(models.PasswordResetToken).where(
            models.PasswordResetToken.user_id == user.id,
        ),
    )
    
    await db.commit()
    
    return {
        "message" : "Password reset successfully. You can now login with you new password."
    }
    

@user_router.patch("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = hash_password(password_data.new_password)

    await db.execute(
        sql_delete(models.PasswordResetToken).where(
            models.PasswordResetToken.user_id == current_user.id,
        ),
    )

    await db.commit()
    return {"message": "Password changed successfully"} 



@user_router.get("/me", response_model=UserPrivate)
async def get_current_user(
    current_user: CurrentUser
) -> UserPrivate:
    """To Get Currently Authenticated User"""
    return current_user

@user_router.get(
    "/{user_id}",
    response_model=UserPublic
)
async def get_user(
    user_id: int,
    service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    return await service.get_user(
        user_id
    )

@user_router.get(
    "/{user_id}/posts",
    response_model=PaginatedPostsResponse
)
async def get_user_posts(
    user_id: int,
    service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return await service.get_user_posts(
        user_id,
        skip,
        limit
    )


@user_router.patch(
    "/{user_id}",
    response_model=UserPrivate
)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: CurrentUser,
    service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    return await service.update_user(
        user_id,
        current_user.id,
        user_update
    )

@user_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
    user_id: int,
    current_user: CurrentUser,
    service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    await service.delete_user(
        user_id,
        current_user.id
    )


@user_router.patch(
    "/{user_id}/picture",
    response_model=UserPrivate,
)
async def upload_profile_picture(
    user_id: int,
    file: UploadFile,
    current_user: CurrentUser,
    service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
):
    return await service.upload_profile_picture(
        user_id=user_id,
        current_user=current_user,
        file=file,
    )

@user_router.delete(
    "/{user_id}/picture",
    response_model=UserPrivate,
)
async def delete_user_picture(
    user_id: int,
    current_user: CurrentUser,
    service: Annotated[
        UserService,
        Depends(get_user_service),
    ],
):
    return await service.delete_profile_picture(
        user_id=user_id,
        current_user=current_user,
    )