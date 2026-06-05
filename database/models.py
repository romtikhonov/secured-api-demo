from datetime import datetime
from uuid import UUID, uuid4

from passlib.context import CryptContext
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.types import DateTime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=lambda: uuid4())


class User(Base):
    _password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, password: str):
        self._password_hash = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self._password_hash)


class UserProfile(Base):
    bio: Mapped[str] = mapped_column(String(256), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(256), nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False, unique=True
    )
    user: Mapped["User"] = relationship("User", back_populates="profile")
