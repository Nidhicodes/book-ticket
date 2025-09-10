import logging
import datetime as dt
from app.database import SessionLocal, engine
from app.models import User, Event, Base
from app import services, schemas
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    db: Session = SessionLocal()
    try:
        # Create tables
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created.")

        # Check if data already exists
        if db.query(User).first() or db.query(Event).first():
            logger.info("Data already exists. Skipping seeding.")
            return

        # Create Users
        logger.info("Creating users...")
        user1 = User(email="testuser@example.com", username="testuser", role="user")
        admin1 = User(email="admin@example.com", username="adminuser", role="admin")
        db.add(user1)
        db.add(admin1)
        db.commit()
        logger.info("Users created.")

        # Create Events
        logger.info("Creating events...")
        event_schema1 = schemas.EventCreate(name="Tech Conference 2025", venue="Convention Center", start_time=dt.datetime(2025, 10, 1, 9, 0), end_time=dt.datetime(2025, 10, 1, 17, 0), total_seats=100)
        event_schema2 = schemas.EventCreate(name="Music Festival", venue="City Park", start_time=dt.datetime(2025, 11, 15, 12, 0), end_time=dt.datetime(2025, 11, 15, 23, 0), total_seats=500)
        event_schema3 = schemas.EventCreate(name="Art Exhibition", venue="Downtown Gallery", start_time=dt.datetime(2025, 12, 5, 10, 0), end_time=dt.datetime(2025, 12, 5, 18, 0), total_seats=50)
        
        services.create_event(db, event_schema1)
        services.create_event(db, event_schema2)
        services.create_event(db, event_schema3)
        
        logger.info("Events created.")

        logger.info("Database has been seeded successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
