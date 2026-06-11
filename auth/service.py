from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from uuid import UUID

from core.config import settings
from core.secrets import SecretProvider
from database.unit_of_work import UnitOfWork
from jose import ExpiredSignatureError, JWTError, jwt


class TokenValidationError(Exception):
    pass


class AuthService:
    def __init__(self, secret_provider: SecretProvider):
        self._secret_key = secret_provider.get_auth_secret_key()

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        async with UnitOfWork() as uow:
            user = await uow.users.get_user_by_email(email=email)
            if not user:
                return None
            if not user.check_password(password=password):
                return None
            return {
                "access_token": self._create_access_token(user_id=user.id),
                "refresh_token": self._create_refresh_token(user_id=user.id),
                "user_id": str(user.id),
            }

    def refresh_access_token(self, refresh_token) -> dict:
        user_id = self._verify_refresh_token(refresh_token)
        return {
            "access_token": self._create_access_token(user_id=user_id),
            "refresh_token": self._create_refresh_token(user_id=user_id),
        }

    def _create_access_token(self, user_id: UUID) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.auth.access_token_expire_minutes),
            "token_type": "access",
        }
        return jwt.encode(payload, self._secret_key, algorithm=settings.auth.algorithm)

    def _create_refresh_token(self, user_id: UUID) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(days=settings.auth.refresh_token_expire_days),
            "token_type": "refresh",
            "aud": "refresh",
        }
        return jwt.encode(payload, self._secret_key, algorithm=settings.auth.algorithm)

    def _verify_access_token(self, token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, self._secret_key, algorithms=[settings.auth.algorithm])
        except ExpiredSignatureError:
            raise TokenValidationError("Token has expired")
        except JWTError:
            raise TokenValidationError("Invalid token signature")

    def _verify_refresh_token(self, token: str) -> UUID:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[settings.auth.algorithm],
                audience="refresh",
            )
            if payload.get("token_type") != "refresh":
                raise TokenValidationError("Invalid token type")
            user_id = payload.get("sub")
            if not user_id:
                raise TokenValidationError("User ID missing")
            return UUID(user_id)
        except JWTError as e:
            raise TokenValidationError(f"Invalid refresh token: {e}")

    def validate_authentication(self, token: str) -> UUID:
        payload = self._verify_access_token(token)
        if payload.get("token_type") != "access":
            raise TokenValidationError("Invalid token type")
        user_id = payload.get("sub", None)
        if not user_id:
            raise TokenValidationError("User ID not found in token")
        return UUID(user_id)
