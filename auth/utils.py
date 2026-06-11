from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from core.config import settings
from core.secrets import secret_manager
from jose import ExpiredSignatureError, JWTError, jwt


class TokenValidationError(Exception):
    pass


def create_access_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.auth.access_token_expire_minutes),
        "token_type": "access",
    }
    return jwt.encode(payload, secret_manager.get_auth_secret_key(), algorithm=settings.auth.algorithm)


def create_refresh_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.auth.refresh_token_expire_days),
        "token_type": "refresh",
        "aud": "refresh",
    }
    return jwt.encode(payload, secret_manager.get_auth_secret_key(), algorithm=settings.auth.algorithm)


def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, secret_manager.get_auth_secret_key(), algorithms=[settings.auth.algorithm])
    except ExpiredSignatureError:
        raise TokenValidationError("Token has expired")
    except JWTError:
        raise TokenValidationError("Invalid token signature")


def verify_refresh_token(token: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            secret_manager.get_auth_secret_key(),
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
