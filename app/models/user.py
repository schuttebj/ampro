from sqlalchemy import Boolean, Column, String

from app.models.base import BaseModel


class User(BaseModel):
    """
    User model for authentication and authorization.
    """
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False)
    department = Column(String, nullable=True) 