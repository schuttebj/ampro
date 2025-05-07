from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.dependencies import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.audit import ActionType, ResourceType
from app.schemas.token import Token
from app.schemas.user import User

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = crud.user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not crud.user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
        
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    
    # Log login action
    crud.audit_log.create(
        db,
        obj_in={
            "user_id": user.id,
            "action_type": ActionType.LOGIN,
            "resource_type": ResourceType.USER,
            "resource_id": str(user.id),
            "description": f"User {user.username} logged in"
        }
    )
    
    return {"access_token": token, "token_type": "bearer"}


@router.post("/test-token", response_model=User)
def test_token(current_user: User = Depends(crud.user.get_current_active_user)) -> Any:
    """
    Test access token.
    """
    return current_user 