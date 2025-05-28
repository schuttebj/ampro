import logging
import os
import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from app.db.session import SessionLocal, engine
from app import crud
from app.models.base import Base
from app.core.config import settings
from app.schemas.user import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables_if_not_exist():
    """
    Create tables if they don't exist
    """
    try:
        inspector = inspect(engine)
        if not inspector.has_table("user"):
            logger.info("Tables don't exist. Creating tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Tables created")
            return True
    except Exception as e:
        logger.error(f"Error checking/creating tables: {str(e)}")
    return False


def init_db(db: Session) -> None:
    """
    Initialize database with initial data.
    """
    try:
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
    except LookupError as e:
        # This happens when there's an enum value mismatch (e.g., 'admin' vs 'ADMIN')
        logger.warning(f"Enum value mismatch detected: {str(e)}")
        logger.warning("This usually means migrations need to run first: alembic upgrade head")
        logger.warning("Skipping database initialization - migrations will handle data migration")
        return
    except sqlalchemy.exc.ProgrammingError as e:
        # If tables don't exist yet, just log a warning and return
        logger.warning(f"Could not initialize database: {str(e)}")
        logger.warning("Make sure to run migrations first: alembic upgrade head")
        return


def main() -> None:
    """
    Main function to run when script is executed.
    """
    logger.info("Creating initial data")
    
    # Check if tables exist, create them if they don't
    tables_created = create_tables_if_not_exist()
    if tables_created:
        logger.info("Tables created, continuing with initialization")
    
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    logger.info("Initial data created")


if __name__ == "__main__":
    main() 