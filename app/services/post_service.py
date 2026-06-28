from fastapi import HTTPException, status

from app.models.models import Post

from app.schemas.post_schema import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PaginatedPostsResponse
)

from app.uow.unit_of_work import UnitOfWork

from fastapi import UploadFile
from PIL import UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from botocore.exceptions import ClientError

from app.config import settings
from app.providers.storage.base import StorageProvider
from app.providers.storage.factory import get_storage
from app.providers.storage.keys import StorageKeys
from app.utils.image_handler import process_profile_image
from app.core.logger import logger


class PostService:
    
    def __init__(
        self,
        storage: StorageProvider | None = None,
    ) -> None:
        self.storage = storage or get_storage()
        
        
    async def get_posts(
        self,
        skip: int,
        limit: int
    ):
        async with UnitOfWork() as uow:

            total = await uow.posts.count()

            posts = await uow.posts.get_all(
                skip=skip,
                limit=limit
            )

            has_more = (
                skip + len(posts)
            ) < total

            return PaginatedPostsResponse(
                posts=[
                    PostResponse.model_validate(post)
                    for post in posts
                ],
                total=total,
                skip=skip,
                limit=limit,
                has_more=has_more
            )

    async def get_post(
        self,
        post_id: int
    ):
        async with UnitOfWork() as uow:

            post = await uow.posts.get_by_id(
                post_id
            )

            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            return post

    async def create_post(
        self,
        post_data: PostCreate,
        user_id: int,
    ):
        async with UnitOfWork() as uow:
            
            logger.info("Post created with the title {}, by user with id {} ", post_data.title, user_id)
            
            post = Post(
                title=post_data.title,
                content=post_data.content,
                user_id=user_id,
            )

            await uow.posts.create(post)
            await uow.commit()
            await uow.session.refresh(post)

            return await uow.posts.get_by_id(
                post.id
            )

    async def update_post(
        self,
        post_id: int,
        post_data: PostCreate,
        user_id: int
    ):
        async with UnitOfWork() as uow:

            post = await uow.posts.get_by_id(
                post_id
            )

            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            if post.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not Authorized"
                )

            post.title = post_data.title
            post.content = post_data.content

            await uow.commit()
            await uow.session.refresh(post)
            
            return post

    async def patch_post(
        self,
        post_id: int,
        post_data: PostUpdate,
        user_id: int
    ):
        async with UnitOfWork() as uow:

            post = await uow.posts.get_by_id(
                post_id
            )

            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            if post.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not Authorized"
                )

            update_data = post_data.model_dump(
                exclude_unset=True
            )

            for field, value in update_data.items():
                setattr(post, field, value)

            await uow.commit()
            await uow.session.refresh(post)
            
            return post

    async def delete_post(
        self,
        post_id: int,
        user_id: int
    ):
        async with UnitOfWork() as uow:

            post = await uow.posts.get_by_id(
                post_id
            )

            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            if post.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not Authorized"
                )
                
            image_file = post.image_file
            
            if image_file:
                await self.storage.delete(
                    StorageKeys.post_image(image_file)
                )

            await uow.posts.delete(post)
            await uow.commit()
            
            
    async def upload_post_picture(
        self,
        post_id: int,
        user_id: int,
        file: UploadFile,
    ):
        async with UnitOfWork() as uow:

            post = await uow.posts.get_by_id(
                post_id
            )

            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post not found"
                )

            if post.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not Authorized"
                )

            content = await file.read()

            if len(content) > settings.max_upload_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File too large.",
                )

            try:
                processed_bytes, image_filename = await run_in_threadpool(
                    process_profile_image,
                    content,
                )
            except UnidentifiedImageError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid image.",
                )

            old_filename = post.image_file

            uploaded = await self.storage.upload(
                file_bytes=processed_bytes,
                key=StorageKeys.post_image(image_filename),
                content_type="image/jpeg",
            )

            post.image_file = uploaded.key

            await uow.commit()
            await uow.session.refresh(post)

        if old_filename:
            await self.storage.delete(
                StorageKeys.post_image(old_filename)
            )

        return post