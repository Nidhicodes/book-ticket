import logging
from app.database import SessionLocal, engine
from app.models import User, Event, Base
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    db: Session = SessionLocal()
    try:
        logger.info("Creating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created.")

        if db.query(User).first() or db.query(Event).first():
            logger.info("Data already exists. Skipping seeding.")
            return

        logger.info("Creating users...")
        user1 = User(email="testuser@example.com", username="testuser", role="user")
        admin1 = User(email="admin@example.com", username="adminuser", role="admin")
        db.add(user1)
        db.add(admin1)
        db.commit()
        logger.info("Users created.")

        logger.info("Creating events...")
        event1 = Event(name="Tech Conference 2025", venue="Convention Center", start_time="2025-10-01T09:00:00", end_time="2025-10-01T17:00:00", capacity=100, available_tickets=100)
        event2 = Event(name="Music Festival", venue="City Park", start_time="2025-11-15T12:00:00", end_time="2025-11-15T23:00:00", capacity=500, available_tickets=500)
        event3 = Event(name="Art Exhibition", venue="Downtown Gallery", start_time="2025-12-05T10:00:00", end_time="2025-12-05T18:00:00", capacity=50, available_tickets=0) 
        db.add(event1)
        db.add(event2)
        db.add(event3)
        db.commit()
        logger.info("Events created.")

        logger.info("Database has been seeded successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
