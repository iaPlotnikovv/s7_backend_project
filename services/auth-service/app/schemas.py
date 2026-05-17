import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # подсказка: ConfigDict(from_attributes=<ЧТО_СЮДА?>)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # стандартное значение по RFC 6750 (строчными)
