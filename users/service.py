from uuid import UUID

from cache.leaderboard import update_user_score
from database.models import UserProfile
from database.unit_of_work import UnitOfWork
from fastapi import HTTPException

from users.schemas import UserProfileCreate, UserProfilePatch, UserProfileUpdate


class UserService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def search_users(self, query: str, lang: str = "english") -> list[UserProfile]:
        return await self.uow.user_profiles.get_search_by_bio(search_query=query, lang=lang)

    async def create_profile(self, user_id: UUID, data: UserProfileCreate) -> UserProfile:
        existing = await self.uow.user_profiles.get_profile_by_user_id(user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Profile already exists for this user")
        return await self.uow.user_profiles.create_profile({"user_id": user_id, **data.model_dump()})

    async def get_profile(self, user_id: UUID) -> UserProfile:
        profile = await self.uow.user_profiles.get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    async def update_profile_full(self, user_id: UUID, data: UserProfileUpdate) -> UserProfile:
        return await self.uow.user_profiles.update_profile(await self.get_profile(user_id), data.model_dump())

    async def update_profile_partial(self, user_id: UUID, data: UserProfilePatch) -> UserProfile:
        return await self.uow.user_profiles.update_profile(
            await self.get_profile(user_id), data.model_dump(exclude_unset=True)
        )

    async def delete_profile(self, user_id: UUID) -> None:
        await self.uow.user_profiles.delete_profile(await self.get_profile(user_id))

    async def add_points(self, user_id: UUID, points: int) -> int:
        user = await self.uow.users.get_user_by_id(user_id)
        if not user:
            raise HTTPException(404, "User not found")

        user_updated = await self.uow.users.update_user(user, {"score": user.score + points})
        await update_user_score(user_id, user_updated.score)

        return user_updated.score
