from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.citizen import Citizen
from app.schemas.citizen import CitizenCreate, CitizenUpdate


class CRUDCitizen(CRUDBase[Citizen, CitizenCreate, CitizenUpdate]):
    """
    CRUD operations for Citizen model.
    """
    def get_by_id_number(self, db: Session, *, id_number: str) -> Optional[Citizen]:
        """
        Get a citizen by ID number.
        """
        return db.query(Citizen).filter(Citizen.id_number == id_number).first()

    def search_by_name(
        self, db: Session, *, first_name: str = None, last_name: str = None, skip: int = 0, limit: int = 100
    ) -> List[Citizen]:
        """
        Search citizens by first name and/or last name.
        """
        query = db.query(Citizen)
        if first_name:
            query = query.filter(Citizen.first_name.ilike(f"%{first_name}%"))
        if last_name:
            query = query.filter(Citizen.last_name.ilike(f"%{last_name}%"))
        return query.offset(skip).limit(limit).all()
    
    def get_with_licenses(self, db: Session, *, id: int) -> Optional[Citizen]:
        """
        Get a citizen with their licenses.
        """
        return db.query(Citizen).filter(Citizen.id == id).first()


citizen = CRUDCitizen(Citizen) 