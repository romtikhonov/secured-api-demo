from database.models import User
from database.repositories import UserRepository
from database.session import SessionLocal


class UnitOfWork:
    def __init__(self):
        self._session = None

    @property
    def users(self) -> UserRepository:
        return self._users

    async def __aenter__(self):
        self._session = SessionLocal()
        self._users = UserRepository(User, session=self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            await self._session.close()
