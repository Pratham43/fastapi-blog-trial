from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User


class UserRepository:

    def __init__(
        self,
        session: AsyncSession
    ):
        self.session = session

    async def get_by_id(
        self,
        user_id: int
    ):
        return await self.session.get(
            User,
            user_id
        )

    async def get_by_email(
        self,
        email: str
    ):
        result = await self.session.execute(
            select(User)
            .where(
                func.lower(User.email)
                == email.lower()
            )
        )

        return result.scalars().first()

    async def get_by_username(
        self,
        username: str
    ):
        result = await self.session.execute(
            select(User)
            .where(
                func.lower(User.username)
                == username.lower()
            )
        )

        return result.scalars().first()

    async def exists_email(
        self,
        email: str
    ):
        return (
            await self.get_by_email(email)
        ) is not None

    async def exists_username(
        self,
        username: str
    ):
        return (
            await self.get_by_username(username)
        ) is not None

    async def create(
        self,
        user: User
    ):
        self.session.add(user)

    async def delete(
        self,
        user: User
    ):
        await self.session.delete(user)