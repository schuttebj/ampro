from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class UserLocation(BaseModel):
    __tablename__ = "user_locations"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("location.id", ondelete="CASCADE"), primary_key=True, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    can_print = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="user_locations")
    location = relationship("Location", back_populates="user_locations") 