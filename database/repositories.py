from typing import Any, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Base, User

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository:
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def _create(self, db: AsyncSession, obj_in: dict) -> Type[ModelType]:
        if not isinstance(obj_in, dict):
            raise ValueError(f"obj_in is not dict ({type(obj_in)})")
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise ValueError("Database constraint violation: unique constraint failed")
        except Exception as e:
            raise Exception(f"DB Error: {e}")
        return db_obj

    async def _get_by_id(self, db: AsyncSession, id: UUID) -> Optional[Type[ModelType]]:
        if not isinstance(id, UUID):
            raise ValueError(f"id is not UUID ({type(id)})")
        return (await db.scalars(select(self.model).where(self.model.id == id))).first()

    async def _get_by_key(self, db: AsyncSession, key: Any, value: Any) -> Optional[Type[ModelType]]:
        if not hasattr(self.model, key):
            raise ValueError(f"{key} is not in ({self.model})")
        return (await db.scalars(select(self.model).where(getattr(self.model, key) == value))).first()

    async def _get_all(self, db: AsyncSession, offset: int = 0, limit: int = 0) -> List[Type[ModelType]]:
        query = select(self.model).offset(offset)
        if limit > 0:
            query = query.limit(limit)
        return (await db.scalars(query)).all()


class UserRepository(BaseRepository):
    def __init__(self, model: Type[User], session: Optional[AsyncSession] = None):
        super().__init__(model)
        self._session = session

    async def create_user(self, user_data: dict) -> User:
        password = user_data.pop("password")
        user = User(**user_data)
        user.set_password(password)
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_user_by_id(self, id: UUID) -> Optional[User]:
        return await super()._get_by_id(db=self._session, id=id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        return await super()._get_by_key(db=self._session, key="username", value=username)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await super()._get_by_key(db=self._session, key="email", value=email)

    async def get_all_users(self, offset: int = 0, limit: int = 0) -> List[User]:
        return await super()._get_all(db=self._session, offset=offset, limit=limit)
