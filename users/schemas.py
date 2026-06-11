from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserProfileBase(BaseModel):
    """Base schema for user profile."""

    bio: str = Field(min_length=1, max_length=256, description="Short biography of the user")
    avatar_url: str = Field(description="URL to the user's avatar image")


class UserProfileCreate(UserProfileBase):
    """Schema for creating a new user profile."""

    pass


class UserProfilePatch(BaseModel):
    """Schema for partially updating an existing user profile."""

    bio: str | None = Field(min_length=1, max_length=256)
    avatar_url: str | None


class UserProfileUpdate(UserProfileBase):
    """Schema for updating an existing user profile."""

    pass


class UserProfileRead(UserProfileBase):
    """Schema for reading a user profile from the API."""

    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True


class UserProfileSearchResult(UserProfileBase):
    user_id: UUID
    email: EmailStr


class LeaderboardEntry(BaseModel):
    user_id: UUID
    score: int


class BonusClaimRequest(BaseModel):
    points: int = Field(..., gt=0, le=100)


class BonusClaimResponse(BaseModel):
    new_score: int


class UniqueVisitorsResponse(BaseModel):
    date: str
    unique_visitors: int
