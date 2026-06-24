from fastapi import HTTPException, status

from app.models.models import Post

from app.schemas.post_schema import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PaginatedPostsResponse
)

from app.uow.unit_of_work import UnitOfWork


class PostService:

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
        user_id: int
    ):
        async with UnitOfWork() as uow:

            post = Post(
                title=post_data.title,
                content=post_data.content,
                user_id=user_id
            )

            await uow.posts.create(post)

            await uow.commit()

            await uow.session.refresh(post)

            return post

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

            await uow.posts.delete(post)

            await uow.commit()