from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app import security, service
import jwt 

# tokenUrl — путь к login endpoint, используется Swagger UI для кнопки "Authorize"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session 


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Unauthorized',
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_access_token(token)  # функция из security.py
        user_id: str = payload.get('sub')  # стандартный JWT claim — идентификатор субъекта
        if user_id is None:
            raise credentials_exception
    except (jwt.PyJWTError, ValueError):  # базовый класс исключений pyjw t
        raise credentials_exception

    user = await service.get_user_by_id(session, user_id)
    if user is None:
        raise credentials_exception
    return user
