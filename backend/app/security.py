from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd_ctx.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd_ctx.verify(p, h)

def create_access_token(sub: str, role: str, name: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": sub, "role": role, "name": name, "exp": exp},
                      settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
