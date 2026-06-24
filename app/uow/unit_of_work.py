from app.db.database import AsyncSessionLocal

from app.repositories.user_repository import UserRepository
from app.repositories.post_repository import PostRepository


class UnitOfWork:

    async def __aenter__(self):

        self.session = AsyncSessionLocal()

        self.users = UserRepository(
            self.session
        )

        self.posts = PostRepository(
            self.session
        )

        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        tb
    ):
        if exc:
            await self.session.rollback()

        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()