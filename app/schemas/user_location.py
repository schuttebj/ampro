from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UserLocationBase(BaseModel):
    user_id: int
    location_id: int
    is_primary: bool = False
    can_print: bool = False


class UserLocationCreate(UserLocationBase):
    pass


class UserLocationUpdate(BaseModel):
    is_primary: Optional[bool] = None
    can_print: Optional[bool] = None


class UserLocationInDBBase(UserLocationBase):
    created_at: datetime

    class Config:
        orm_mode = True


class UserLocation(UserLocationInDBBase):
    pass


class UserLocationInDB(UserLocationInDBBase):
    pass


# Extended schemas with related data
class UserLocationWithUser(UserLocationInDBBase):
    user: Optional[dict] = None  # Will be populated with User data


class UserLocationWithLocation(UserLocationInDBBase):
    location: Optional[dict] = None  # Will be populated with Location data


class UserLocationFull(UserLocationInDBBase):
    user: Optional[dict] = None
    location: Optional[dict] = None 