import logging
import os
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app import crud, models
from app.core.config import settings
from app.schemas.user import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """
    Initialize database with initial data.
    """
    # Create admin user if it doesn't exist
    admin_user = crud.user.get_by_username(db, username="admin")
    if not admin_user:
        logger.info("Creating admin user")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")  # For development only
        admin_user_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password=admin_password,
            full_name="Admin User",
            is_superuser=True,
            department="Administration"
        )
        crud.user.create(db, obj_in=admin_user_in)
        logger.info(f"Admin user created with password: {admin_password}")
    
    # Create regular user if it doesn't exist
    user = crud.user.get_by_username(db, username="officer")
    if not user:
        logger.info("Creating regular user")
        user_password = os.environ.get("USER_PASSWORD", "officer123")  # For development only
        user_in = UserCreate(
            username="officer",
            email="officer@example.com",
            password=user_password,
            full_name="License Officer",
            is_superuser=False,
            department="License Department"
        )
        crud.user.create(db, obj_in=user_in)
        logger.info(f"Regular user created with password: {user_password}")


def main() -> None:
    """
    Main function to run when script is executed.
    """
    logger.info("Creating initial data")
    db = SessionLocal()
    init_db(db)
    db.close()
    logger.info("Initial data created")


if __name__ == "__main__":
    main() 