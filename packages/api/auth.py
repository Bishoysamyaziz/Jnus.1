"""OneAgent OS — JWT Authentication"""
from __future__ import annotations

import os
import uuid
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users import FastAPIUsers, BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend, BearerTransport, JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users import schemas

SECRET = os.getenv("SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION")


# ── User Schema ───────────────────────────────────────────────────
class UserRead(schemas.BaseUser[uuid.UUID]):
    pass

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass


# ── JWT Strategy ──────────────────────────────────────────────────
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=604_800)  # 7 days


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=BearerTransport(tokenUrl="auth/jwt/login"),
    get_strategy=get_jwt_strategy,
)
