from typing import Dict, Optional

from database.unit_of_work import UnitOfWork

from auth.utils import create_access_token, create_refresh_token


class AuthService:
    @classmethod
    async def authenticate_user(cls, email: str, password: str) -> Optional[Dict]:
        async with UnitOfWork() as uow:
            user = await uow.users.get_user_by_email(email=email)
            if not user:
                return None
            if not user.check_password(password=password):
                return None
            return {
                "access_token": create_access_token(user_id=user.id),
                "refresh_token": create_refresh_token(user_id=user.id),
                "user_id": str(user.id),
            }
