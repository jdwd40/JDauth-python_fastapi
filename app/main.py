from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Import new configuration and models
from app.config.database import get_db
from app.config.settings import settings
from app.models.user import User

# Import Pydantic schemas
from app.schemas.user import UserCreate
from app.schemas.auth import TokenResponse

# Import new routers
from app.routes.auth import router as auth_router
from app.routes.user import router as user_router, admin_router


# Security utils - now using settings from configuration
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Helper functions
# get_db is now imported from app.config.database


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user


app = FastAPI(
    title="JDauth FastAPI Application",
    description="Authentication service with JWT tokens",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)


# Legacy endpoints for backward compatibility
@app.get("/test")
def test_route():
    return {"status": "success", "message": "API server is running correctly!", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
def root():
    return {
        "message": "JDauth FastAPI Application",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/test"
    }
