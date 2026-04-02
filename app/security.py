from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings
from app.schemas import RoleEnum, TokenPayload


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(user_id: int, role: RoleEnum) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    # python-jose requires "sub" to be a string per JWT validation rules.
    payload = {"sub": str(user_id), "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> TokenPayload | None:
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub = data.get("sub")
        role = data.get("role")
        if sub is None or role is None:
            return None
        return TokenPayload(sub=int(sub), role=RoleEnum(role))
    except (JWTError, ValueError):
        return None
