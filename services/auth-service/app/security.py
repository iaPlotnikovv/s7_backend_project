from datetime import datetime, timedelta, timezone
import bcrypt
import jwt 
from app.config import settings


def hash_password(plain_password: str) -> str:
    """Хеширует пароль с помощью bcrypt и возвращает строку для хранения в БД."""
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(
        password=plain_password.encode('utf-8'),
        salt=salt,
    )
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, что plain_password соответствует ранее сохранённому хешу."""
    return bcrypt.checkpw(
        password=plain_password.encode('utf-8'),
        hashed_password=hashed_password.encode('utf-8'),
    )

def create_access_token(subject: str) -> str:
    """Создаёт JWT для пользователя с указанным subject (обычно user.id)."""
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(
        payload=payload,
        key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token


def decode_access_token(token: str) -> dict:
    """Валидирует JWT и возвращает payload. Бросает исключение при неудаче."""
    payload = jwt.decode(
        jwt=token,
        key=settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    return payload