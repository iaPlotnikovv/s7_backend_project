from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import service, security
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas import UserCreate, UserResponse, TokenResponse
from app.dependencies import get_db, get_current_user
from app.models import User

# prefix задаёт общий префикс для всех роутов в этом файле
router = APIRouter(prefix='/auth', tags=['authorization'])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, session: AsyncSession = Depends(get_db)):
    existing = await service.get_user_by_email(session, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,   # email уже занят
            detail='Bad Request',
        )
    user = await service.create_user(session, data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    user = await service.get_user_by_email(session, form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Unauthorized')
    token = security.create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
