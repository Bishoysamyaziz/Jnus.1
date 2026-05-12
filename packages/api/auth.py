"""OneAgent OS — JWT Authentication with Real User Model"""
from __future__ import annotations

import os
import uuid
from typing import AsyncGenerator

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, schemas
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, func

SECRET = os.getenv("SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION")
DATABASE_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql+asyncpg://oneagent:oneagent_pass@localhost:5432/oneagent",
)


# ── SQLAlchemy Setup ────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class UserTable(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# ── User Schemas ────────────────────────────────────────────────────

class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


# ── User Manager ────────────────────────────────────────────────────

class UserManager(UUIDIDMixin, BaseUserManager[UserTable, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: UserTable, request: Request | None = None):
        print(f"User {user.id} registered.")

    async def on_after_forgot_password(
        self, user: UserTable, token: str, request: Request | None = None
    ):
        print(f"User {user.id} forgot password. Token: {token}")

    async def on_after_request_verify(
        self, user: UserTable, token: str, request: Request | None = None
    ):
        print(f"Verification requested for user {user.id}. Token: {token}")


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, UserTable)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


# ── JWT Strategy ────────────────────────────────────────────────────

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=604_800)  # 7 days


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=BearerTransport(tokenUrl="auth/jwt/login"),
    get_strategy=get_jwt_strategy,
)
