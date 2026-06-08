from auth.dependencies import get_current_user
from database.models import User
from database.unit_of_work import UnitOfWork
from fastapi import APIRouter, Depends, Query
from users.schemas import (
    UserProfileCreate,
    UserProfilePatch,
    UserProfileRead,
    UserProfileSearchResult,
    UserProfileUpdate,
)
from users.service import UserService

router = APIRouter(prefix="/user-profiles", tags=["user-profiles"])


@router.post("/", response_model=UserProfileRead)
async def create_profile(
    data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
):
    async with UnitOfWork() as uow:
        service = UserService(uow)
        profile = await service.create_profile(current_user.id, data)
        return profile


@router.get("/me", response_model=UserProfileRead)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    async with UnitOfWork() as uow:
        service = UserService(uow)
        return await service.get_profile(current_user.id)


@router.put("/me", response_model=UserProfileRead)
async def update_profile_full(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
):
    async with UnitOfWork() as uow:
        service = UserService(uow)
        return await service.update_profile_full(current_user.id, data)


@router.patch("/me", response_model=UserProfileRead)
async def update_profile_partial(
    data: UserProfilePatch,
    current_user: User = Depends(get_current_user),
):
    async with UnitOfWork() as uow:
        service = UserService(uow)
        return await service.update_profile_partial(current_user.id, data)


@router.delete("/me", status_code=204)
async def delete_profile(
    current_user: User = Depends(get_current_user),
):
    async with UnitOfWork() as uow:
        service = UserService(uow)
        await service.delete_profile(current_user.id)


@router.get("/search", response_model=list[UserProfileSearchResult])
async def search_profiles(
    query: str = Query(..., min_length=1, max_length=100),
    lang: str = Query("english", regex="^(english|russian)$"),
    current_user: User = Depends(get_current_user),
):
    async with UnitOfWork() as uow:
        service = UserService(uow)
        profiles = await service.search_users(query, lang)

        return [
            UserProfileSearchResult(user_id=p.user_id, bio=p.bio, avatar_url=p.avatar_url, email=p.user.email)
            for p in profiles
        ]
