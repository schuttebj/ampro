from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer
from sqlalchemy.ext.declarative import declared_attr

from app.db.session import Base


class BaseModel(Base):
    """
    Base model with common fields for all models.
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True)

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate __tablename__ automatically based on class name.
        """
        return cls.__name__.lower() 