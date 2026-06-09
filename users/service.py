from datetime import date
from uuid import UUID

from cache.leaderboard import update_user_score
from cache.locks import create_user_lock
from cache.redis_client import redis_client
from database.models import UserProfile
from database.unit_of_work import UnitOfWork
from fastapi import HTTPException, status

from users.schemas import UserProfileCreate, UserProfilePatch, UserProfileUpdate


class UserService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def search_users(self, query: str, lang: str = "english") -> list[UserProfile]:
        return await self.uow.user_profiles.get_search_by_bio(search_query=query, lang=lang)

    async def create_profile(self, user_id: UUID, data: UserProfileCreate) -> UserProfile:
        existing = await self.uow.user_profiles.get_profile_by_user_id(user_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile already exists for this user")
        return await self.uow.user_profiles.create_profile({"user_id": user_id, **data.model_dump()})

    async def get_profile(self, user_id: UUID) -> UserProfile:
        profile = await self.uow.user_profiles.get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user_updated = await self.uow.users.update_user(user, {"score": user.score + points})
        await update_user_score(user_id, user_updated.score)

        return user_updated.score

    async def claim_daily_bonus(self, user_id: UUID, bonus_points: int) -> dict:
        lock = create_user_lock(user_id=user_id, operation=f"claim_daily_bonus:{date.today().isoformat()}")
        if not await lock.acquire():
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

        try:
            claimed_key = f"bonus_claimed:{user_id}:{date.today().isoformat()}"
            if await redis_client.exists(claimed_key):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bonus already claimed")

            new_score = await self.add_points(user_id=user_id, points=bonus_points)
            await redis_client.setex(name=claimed_key, time=86400, value="1")

            return {"message": "Bonus claimed!", "new_score": new_score}
        finally:
            await lock.release()
