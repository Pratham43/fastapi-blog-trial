from fastapi import HTTPException, status

from app.models.models import User

from app.schemas.user_schema import (
    UserCreate,
    UserUpdate
)

from app.schemas.post_schema import (
    PaginatedPostsResponse
)

from app.uow.unit_of_work import UnitOfWork

from app.utils.auth import (
    hash_password
)

from app.utils.image_handler import (
    delete_profile_image
)


class UserService:

    async def register_user(
        self,
        user_data: UserCreate
    ):
        async with UnitOfWork() as uow:

            if await uow.users.exists_username(
                user_data.username
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )

            if await uow.users.exists_email(
                user_data.email
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )

            user = User(
                username=user_data.username,
                email=user_data.email.lower(),
                password_hash=hash_password(
                    user_data.password
                )
            )

            await uow.users.create(user)

            await uow.commit()

            await uow.session.refresh(user)

            return user

    async def get_user(
        self,
        user_id: int
    ):
        async with UnitOfWork() as uow:

            user = await uow.users.get_by_id(
                user_id
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            return user

    async def get_user_posts(
        self,
        user_id: int,
        skip: int,
        limit: int
    ):
        async with UnitOfWork() as uow:

            user = await uow.users.get_by_id(
                user_id
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            total = await uow.posts.count_for_user(
                user_id
            )

            posts = await uow.posts.get_posts_for_user(
                user_id,
                skip,
                limit
            )

            return PaginatedPostsResponse(
                posts=posts,
                total=total,
                skip=skip,
                limit=limit,
                has_more=(
                    skip + len(posts)
                ) < total
            )

    async def update_user(
        self,
        user_id: int,
        current_user_id: int,
        user_update: UserUpdate
    ):
        async with UnitOfWork() as uow:

            if current_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not Authorized"
                )

            user = await uow.users.get_by_id(
                user_id
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            if (
                user_update.username is not None
                and
                user_update.username.lower()
                != user.username.lower()
            ):
                if await uow.users.exists_username(
                    user_update.username
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already exists"
                    )

            if (
                user_update.email is not None
                and
                user_update.email.lower()
                != user.email.lower()
            ):
                if await uow.users.exists_email(
                    user_update.email
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists"
                    )

            for field, value in (
                user_update
                .model_dump(exclude_unset=True)
                .items()
            ):
                setattr(
                    user,
                    field,
                    value
                )

            await uow.commit()

            await uow.session.refresh(user)

            return user

    async def delete_user(
        self,
        user_id: int,
        current_user_id: int
    ):
        async with UnitOfWork() as uow:

            if current_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not Authorized"
                )

            user = await uow.users.get_by_id(
                user_id
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            old_filename = user.image_file

            await uow.users.delete(user)

            await uow.commit()

        if old_filename:
            await delete_profile_image(
                old_filename
            )