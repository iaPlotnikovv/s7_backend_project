from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.schemas import UserCreate
from app import security

import uuid


async def get_user_by_email(session: AsyncSession, email: str) -> User|None:
    
    result = await session.execute(
        select(User).where(User.email==email)  # условие фильтрации по email
    )
    return result.scalar_one_or_none()  # метод: один объект или None


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    hashed = security.hash_password(data.password)  # функция из security.py
    user = User(
        email=data.email,
        hashed_password=hashed,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)  # нужно для получения server_default полей (created_at)
    return user


async def get_user_by_id(session: AsyncSession, user_id: str) -> User|None:
    result = await session.execute(
        select(User).where(User.id==uuid.UUID(user_id))
    )
    return result.scalar_one_or_none()
