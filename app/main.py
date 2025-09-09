from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from . import services, models, schemas
from .database import get_db
from .routers import admin, waitlist
from .dependencies import get_current_user

app = FastAPI(
    title="Evently API",
    description="Backend system for an event ticketing platform.",
    version="1.0.0"
)

app.include_router(admin.router)
app.include_router(waitlist.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Evently API"}

@app.get("/events", response_model=List[schemas.Event])
def list_events(db: Session = Depends(get_db)):
    """
    Get a list of all available events.
    """
    return services.get_events(db=db)

@app.get("/users/me/bookings", response_model=List[schemas.BookingDetails])
def list_my_bookings(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    """
    Get the booking history for the current user.
    """
    return services.get_user_bookings(db=db, user_id=current_user_id)

@app.post("/bookings", response_model=schemas.Booking, status_code=status.HTTP_201_CREATED)
def book_ticket(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    """
    Book a ticket for an event. The user ID in the request body
    is used to create the booking.
    """
    return services.create_booking(db=db, booking=booking)

@app.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    """
    Cancel a booking. A user can only cancel their own bookings.
    """
    services.cancel_booking(db=db, booking_id=booking_id, user_id=current_user_id)
    return None

@app.get("/users/me/notifications", response_model=List[schemas.Notification])
def list_my_notifications(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    """
    Get all notifications for the current user.
    """
    return services.get_user_notifications(db=db, user_id=current_user_id)
