from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.models import Post


class PostRepository:

    def __init__(self, session):
        self.session = session

    async def get_by_id(
        self,
        post_id: int
    ):
        result = await self.session.execute(
            select(Post)
            .options(
                selectinload(Post.author)
            )
            .where(Post.id == post_id)
        )

        return result.scalars().first()

    async def get_all(
        self,
        skip: int,
        limit: int
    ):
        result = await self.session.execute(
            select(Post)
            .options(
                selectinload(Post.author)
            )
            .order_by(Post.date_posted.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()

    async def count(self):
        result = await self.session.execute(
            select(func.count())
            .select_from(Post)
        )

        return result.scalar()

    async def create(
        self,
        post: Post
    ):
        self.session.add(post)

    async def delete(
        self,
        post: Post
    ):
        await self.session.delete(post)
        
    async def count_for_user(
        self,
        user_id: int
    ):
        result = await self.session.execute(
            select(func.count())
            .select_from(Post)
            .where(Post.user_id == user_id)
        )

        return result.scalar()
    
    
    async def get_posts_for_user(
        self,
        user_id: int,
        skip: int,
        limit: int
    ):
        result = await self.session.execute(
            select(Post)
            .options(
                selectinload(Post.author)
            )
            .where(Post.user_id == user_id)
            .order_by(Post.date_posted.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()