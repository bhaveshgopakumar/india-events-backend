from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from . import models

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_pw(p: str) -> str: return pwd.hash(p)
def verify_pw(p: str, h: str) -> bool: return pwd.verify(p, h)

def make_token(uid: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(uid), "exp": exp}, settings.secret_key, algorithm="HS256")

def current_user(token: str | None = Depends(oauth2), db: Session = Depends(get_db)) -> models.User:
    if not token: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        uid = int(jwt.decode(token, settings.secret_key, algorithms=["HS256"])["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = db.get(models.User, uid)
    if not user: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user

def roles_of(db: Session, uid: int) -> list[str]:
    return [r.role for r in db.query(models.UserRole).filter_by(user_id=uid)]

def require_admin(user: models.User = Depends(current_user), db: Session = Depends(get_db)) -> models.User:
    if "admin" not in roles_of(db, user.id): raise HTTPException(status.HTTP_403_FORBIDDEN, "Admins only")
    return user
