from typing import Any, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Base, User, UserProfile

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

    async def _update(self, db: AsyncSession, db_obj: Type[ModelType], update_data: dict) -> Type[ModelType]:
        for field, value in update_data.items():
            if value is not None:
                setattr(db_obj, field, value)
        await db.flush()
        return db_obj

    async def _delete(self, db: AsyncSession, db_obj: Type[ModelType]) -> None:
        await db.delete(db_obj)
        await db.flush()


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(User)
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

    async def update_user(self, user: User, update_data: dict) -> User:
        return await super()._update(db=self._session, db_obj=user, update_data=update_data)


class UserProfileRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(UserProfile)
        self._session = session

    async def create_profile(self, profile_data: dict) -> UserProfile:
        return await self._create(self._session, profile_data)

    async def get_profile_by_user_id(self, user_id: UUID) -> Optional[UserProfile]:
        return await self._get_by_key(self._session, "user_id", user_id)

    async def get_profile_by_id(self, id: UUID) -> Optional[UserProfile]:
        return await self._get_by_id(self._session, id)

    async def get_all_profiles(self, offset: int = 0, limit: int = 0) -> List[UserProfile]:
        return await self._get_all(self._session, offset=offset, limit=limit)

    async def update_profile(self, profile: UserProfile, update_data: dict) -> UserProfile:
        return super()._update(db=self._session, db_obj=profile, update_data=update_data)

    async def delete_profile(self, profile: UserProfile) -> None:
        await super()._delete(db=self._session, db_obj=profile)

    async def get_search_by_bio(self, search_query: str, lang: str) -> List[UserProfile]:
        if lang not in ("english", "russian"):
            raise ValueError("Unsupported language")

        vector = func.to_tsvector(lang, UserProfile.bio)
        ts_query = func.plainto_tsquery(lang, search_query)
        stmt = select(UserProfile).options(selectinload(UserProfile.user)).where(vector.bool_op("@@")(ts_query))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
