from datetime import datetime, timedelta
from typing import Any, Optional, Union, List

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.token import TokenPayload

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 setup with token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password for storing.
    """
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def oauth2_scheme_optional(
    authorization: Optional[str] = Header(None, include_in_schema=True)
) -> Optional[str]:
    """OAuth2 scheme that does not raise an exception when no authentication is provided."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    return None

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current user from a JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if token_data.exp < datetime.utcnow().timestamp():
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == token_data.sub).first()
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user

async def get_current_active_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

# Role-based access control functions
def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control.
    """
    async def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.is_superuser or current_user.role in allowed_roles:
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}",
        )
    return check_role

async def get_current_printer_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Get the current active printer user.
    """
    if not (current_user.role == UserRole.PRINTER or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Printer access required",
        )
    return current_user

async def get_current_manager_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Get the current active manager user.
    """
    if not (current_user.role in [UserRole.MANAGER, UserRole.ADMIN] or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required",
        )
    return current_user

async def get_current_officer_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Get the current active officer user (can process applications).
    """
    if not (current_user.role in [UserRole.OFFICER, UserRole.MANAGER, UserRole.ADMIN] or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Officer access required",
        )
    return current_user

async def get_current_user_optional(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme_optional)
) -> Optional[User]:
    """
    Get current user if authenticated, return None if not.
    Use this for endpoints that allow both authenticated and unauthenticated access.
    """
    if not token:
        return None
    
    try:
        return await get_current_user(db=db, token=token)
    except HTTPException:
        return None 