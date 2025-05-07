from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations on a SQLAlchemy model.
    """
    def __init__(self, model: Type[ModelType]):
        """
        Initialize with SQLAlchemy model class.
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a record by ID.
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        Remove a record by ID.
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
        
    def get_by_field(self, db: Session, field_name: str, value: Any) -> Optional[ModelType]:
        """
        Get a record by a specific field value.
        """
        return db.query(self.model).filter(getattr(self.model, field_name) == value).first()
        
    def get_multi_by_field(
        self, db: Session, field_name: str, value: Any, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records by a specific field value with pagination.
        """
        return db.query(self.model).filter(
            getattr(self.model, field_name) == value
        ).offset(skip).limit(limit).all()
        
    def soft_delete(self, db: Session, *, id: int) -> ModelType:
        """
        Soft delete a record by setting is_active to False.
        """
        obj = db.query(self.model).get(id)
        obj.is_active = False
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj 