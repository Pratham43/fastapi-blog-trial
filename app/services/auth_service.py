from datetime import timedelta

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.config import settings
from app.models.models import User
from app.schemas.user_schema import UserCreate, Token
from app.uow.unit_of_work import UnitOfWork

from app.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:

    async def register(
        self,
        user_data: UserCreate,
    ):
        async with UnitOfWork() as uow:

            existing_username = await uow.users.get_by_username(
                user_data.username
            )

            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists",
                )

            existing_email = await uow.users.get_by_email(
                user_data.email
            )

            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists",
                )

            user = User(
                username=user_data.username,
                email=user_data.email.lower(),
                password_hash=hash_password(
                    user_data.password
                ),
            )

            await uow.users.create(user)

            await uow.commit()

            await uow.session.refresh(user)

            return user

    async def login(
        self,
        email: str,
        password: str
    ) -> Token:

        async with UnitOfWork() as uow:
            user = await uow.users.get_by_email(
                email.lower()
            )

            if (
                not user
                or
                not verify_password(
                    password,
                    user.password_hash,
                )
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                    headers={
                        "WWW-Authenticate": "Bearer"
                    },
                )

            access_token = create_access_token(
                data={
                    "sub": str(user.id)
                },
                expires_delta=timedelta(
                    minutes=settings.access_token_expire_minutes
                ),
            )

            return Token(
                access_token=access_token,
                token_type="bearer",
            )