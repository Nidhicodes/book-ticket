from sqlalchemy.orm import Session, joinedload, subqueryload
from sqlalchemy import func, cast, Date
from . import models, schemas
from fastapi import HTTPException, status

def get_events(db: Session):
    """
    Retrieves a list of all events, including their seats.
    """
    return db.query(models.Event).options(subqueryload(models.Event.seats)).all()

def create_event(db: Session, event: schemas.EventCreate):
    """
    Creates a new event and generates its seats.
    """
    db_event = models.Event(
        name=event.name,
        venue=event.venue,
        start_time=event.start_time,
        end_time=event.end_time
    )
    db.add(db_event)
    db.flush()

    seats = [models.Seat(event_id=db_event.id, seat_number=f"Seat-{i+1}") for i in range(event.total_seats)]
    db.add_all(seats)

    db.commit()
    db.refresh(db_event)
    return db_event

def create_booking(db: Session, booking: schemas.BookingCreate):
    """
    Creates a booking for a user for an event. If a seat_number is provided,
    it books that specific seat. If not, it attempts to find any available seat.
    If the event is full, it adds the user to the waitlist.
    """
    seat_to_book = None
    if booking.seat_number:
        query = db.query(models.Seat).filter(
            models.Seat.event_id == booking.event_id,
            models.Seat.seat_number == booking.seat_number
        )
        if db.bind.dialect.name == 'postgresql':
            query = query.with_for_update()
        seat_to_book = query.first()

        if not seat_to_book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found for this event")
    else:
        all_seats = db.query(models.Seat).filter(models.Seat.event_id == booking.event_id).all()
        if not all_seats:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No seats found for this event")

        booked_seat_ids = db.query(models.Booking.seat_id).filter(
            models.Booking.event_id == booking.event_id,
            models.Booking.status == 'active'
        ).all()
        booked_seat_ids = {seat_id for (seat_id,) in booked_seat_ids}

        seat_to_book = next((seat for seat in all_seats if seat.id not in booked_seat_ids), None)

    if not seat_to_book:
        waitlist_entry = db.query(models.WaitlistEntry).filter(
            models.WaitlistEntry.user_id == booking.user_id,
            models.WaitlistEntry.event_id == booking.event_id
        ).first()

        if waitlist_entry:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already on the waitlist for this event.")

        new_waitlist_entry = models.WaitlistEntry(user_id=booking.user_id, event_id=booking.event_id)
        db.add(new_waitlist_entry)
        db.commit()
        db.refresh(new_waitlist_entry)
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail="Event is full. You have been added to the waitlist.")

    existing_booking = db.query(models.Booking).filter(
        models.Booking.seat_id == seat_to_book.id,
        models.Booking.status == 'active'
    ).first()

    if existing_booking:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat is already booked")

    db_booking = models.Booking(
        user_id=booking.user_id,
        event_id=booking.event_id,
        seat_id=seat_to_book.id
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def cancel_booking(db: Session, booking_id: int, user_id: int):
    """
    Cancels a booking by marking its status as 'cancelled'. This frees the seat implicitly.
    """
    db_booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id,
        models.Booking.user_id == user_id,
        models.Booking.status == 'active'
    ).first()

    if not db_booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active booking not found for this user")

    db_booking.status = 'cancelled'
    db.commit()
    return {"detail": "Booking canceled successfully"}

def get_user_bookings(db: Session, user_id: int):
    """
    Retrieves all active bookings for a specific user, including event and seat details.
    """
    bookings = db.query(models.Booking).options(
        joinedload(models.Booking.event),
        joinedload(models.Booking.seat)
    ).filter(
        models.Booking.user_id == user_id,
        models.Booking.status == 'active'
    ).all()
    return bookings

def get_user_notifications(db: Session, user_id: int):
    """
    Retrieves all notifications for a specific user.
    """
    return db.query(models.Notification).filter(models.Notification.user_id == user_id).all()

def get_user_waitlist_entries(db: Session, user_id: int):
    """
    Retrieves all waitlist entries for a specific user.
    """
    return db.query(models.WaitlistEntry).filter(models.WaitlistEntry.user_id == user_id).all()

def remove_from_waitlist(db: Session, waitlist_entry_id: int, user_id: int):
    """
    Removes a user's entry from the waitlist.
    """
    waitlist_entry = db.query(models.WaitlistEntry).filter(
        models.WaitlistEntry.id == waitlist_entry_id,
        models.WaitlistEntry.user_id == user_id
    ).first()

    if not waitlist_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waitlist entry not found for this user")

    db.delete(waitlist_entry)
    db.commit()
    return {"detail": "Successfully removed from waitlist"}

def update_event(db: Session, event_id: int, event_update: schemas.EventCreate):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    update_data = event_update.model_dump(exclude={"total_seats"}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return db_event

def delete_event(db: Session, event_id: int):
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    has_bookings = db.query(models.Booking).filter(
        models.Booking.event_id == event_id,
        models.Booking.status == 'active'
    ).first()

    if has_bookings:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete event with active bookings")

    db.query(models.Booking).filter(models.Booking.event_id == event_id).delete(synchronize_session=False)
    db.query(models.Seat).filter(models.Seat.event_id == event_id).delete(synchronize_session=False)
    db.delete(db_event)
    db.commit()
    return {"detail": "Event deleted successfully"}

def get_analytics(db: Session):
    total_bookings = db.query(models.Booking).count()
    cancelled_bookings = db.query(models.Booking).filter(models.Booking.status == 'cancelled').count()
    cancellation_rate = (cancelled_bookings / total_bookings) if total_bookings > 0 else 0

    if db.bind.dialect.name == 'sqlite':
        date_col = func.strftime('%Y-%m-%d', models.Booking.created_at).label('date')
    else:
        date_col = cast(models.Booking.created_at, Date).label('date')

    daily_bookings = db.query(date_col, func.count(models.Booking.id).label('count')).group_by(date_col).order_by(date_col).all()

    events = db.query(models.Event).options(subqueryload(models.Event.seats)).all()
    capacity_utilization = []
    for event in events:
        total_seats = len(event.seats)
        active_bookings = db.query(models.Booking).filter(models.Booking.event_id == event.id, models.Booking.status == 'active').count()
        utilization = (active_bookings / total_seats) if total_seats > 0 else 0

        capacity_utilization.append({
            "event_id": event.id,
            "event_name": event.name,
            "utilization": utilization,
            "total_seats": total_seats,
            "booked_seats": active_bookings
        })

    most_popular_events = sorted(capacity_utilization, key=lambda x: x["booked_seats"], reverse=True)

    return {
        "total_bookings_all_time": total_bookings,
        "total_cancelled_bookings": cancelled_bookings,
        "cancellation_rate": cancellation_rate,
        "daily_booking_stats": [{"date": str(d.date), "bookings": d.count} for d in daily_bookings],
        "capacity_utilization_per_event": capacity_utilization,
        "most_popular_events": most_popular_events
    }
