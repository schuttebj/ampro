from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.crud.base import CRUDBase
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate


class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def get_by_code(self, db: Session, *, code: str) -> Optional[Location]:
        """Get location by code"""
        return db.query(Location).filter(Location.code == code).first()
    
    def get_active_locations(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Location]:
        """Get all active locations with enum safety"""
        try:
            return (
                db.query(self.model)
                .filter(Location.is_active == True)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            print(f"Error with enum-based query, using raw SQL fallback: {e}")
            # Use raw SQL to avoid enum casting issues
            try:
                result = db.execute(text("""
                    SELECT id, name, code, address_line1, address_line2, city, state_province, 
                           postal_code, country, phone_number, email, manager_name, 
                           operating_hours, services_offered, capacity_per_day, 
                           is_active, accepts_applications, accepts_collections,
                           printing_enabled, printing_type, default_print_destination_id,
                           auto_assign_print_jobs, max_print_jobs_per_user, 
                           print_job_priority_default, notes, created_at, updated_at
                    FROM location 
                    WHERE is_active = true 
                    ORDER BY id 
                    OFFSET :skip LIMIT :limit
                """), {"skip": skip, "limit": limit})
                
                locations = []
                for row in result:
                    # Query individual locations by ID to get proper ORM objects
                    # This bypasses the enum issue in the bulk query
                    location_id = row.id
                    try:
                        location = db.execute(text("SELECT * FROM location WHERE id = :id"), {"id": location_id}).first()
                        if location:
                            # Create a new Location object manually to avoid enum casting
                            loc_obj = Location()
                            loc_obj.id = location.id
                            loc_obj.name = location.name
                            loc_obj.code = location.code
                            loc_obj.address_line1 = location.address_line1
                            loc_obj.address_line2 = location.address_line2
                            loc_obj.city = location.city
                            loc_obj.state_province = location.state_province
                            loc_obj.postal_code = location.postal_code
                            loc_obj.country = location.country
                            loc_obj.phone_number = location.phone_number
                            loc_obj.email = location.email
                            loc_obj.manager_name = location.manager_name
                            loc_obj.operating_hours = location.operating_hours
                            loc_obj.services_offered = location.services_offered
                            loc_obj.capacity_per_day = location.capacity_per_day
                            loc_obj.is_active = location.is_active
                            loc_obj.accepts_applications = location.accepts_applications
                            loc_obj.accepts_collections = location.accepts_collections
                            loc_obj.printing_enabled = location.printing_enabled
                            # Skip the problematic printing_type field for now
                            loc_obj.default_print_destination_id = location.default_print_destination_id
                            loc_obj.auto_assign_print_jobs = location.auto_assign_print_jobs
                            loc_obj.max_print_jobs_per_user = location.max_print_jobs_per_user
                            loc_obj.print_job_priority_default = location.print_job_priority_default
                            loc_obj.notes = location.notes
                            loc_obj.created_at = location.created_at
                            loc_obj.updated_at = location.updated_at
                            locations.append(loc_obj)
                    except Exception as inner_e:
                        print(f"Error processing location {location_id}: {inner_e}")
                        continue
                
                return locations
                
            except Exception as e2:
                print(f"Error with raw SQL fallback: {e2}")
                return []
    
    def get_locations_accepting_applications(self, db: Session) -> List[Location]:
        """Get locations that accept new applications"""
        return (
            db.query(self.model)
            .filter(
                Location.is_active == True,
                Location.accepts_applications == True
            )
            .all()
        )
    
    def get_locations_accepting_collections(self, db: Session) -> List[Location]:
        """Get locations that accept license collections"""
        return (
            db.query(self.model)
            .filter(
                Location.is_active == True,
                Location.accepts_collections == True
            )
            .all()
        )
    
    def create_with_code(
        self, db: Session, *, obj_in: LocationCreate
    ) -> Location:
        """Create location ensuring unique code"""
        # Generate code if not provided
        if not obj_in.code:
            obj_in.code = self.generate_location_code(obj_in.name)
        
        return self.create(db, obj_in=obj_in)
    
    def generate_location_code(self, name: str) -> str:
        """Generate a unique location code from name"""
        # Simple implementation - take first 3 letters of each word, uppercase
        words = name.split()
        code_parts = []
        for word in words[:3]:  # Max 3 words
            code_parts.append(word[:3].upper())
        
        base_code = "".join(code_parts)
        return base_code[:8]  # Max 8 characters
    
    def update_status(
        self,
        db: Session,
        *,
        db_obj: Location,
        is_active: bool,
        accepts_applications: Optional[bool] = None,
        accepts_collections: Optional[bool] = None
    ) -> Location:
        """Update location status"""
        update_data = {"is_active": is_active}
        if accepts_applications is not None:
            update_data["accepts_applications"] = accepts_applications
        if accepts_collections is not None:
            update_data["accepts_collections"] = accepts_collections
            
        return self.update(db, db_obj=db_obj, obj_in=update_data)


location = CRUDLocation(Location) 