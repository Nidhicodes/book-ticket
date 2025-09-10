from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import services, schemas

def test_list_events_with_seats(client: TestClient, db: Session):
    services.create_event(db, schemas.EventCreate(name="Event 1", venue="Venue 1", start_time="2025-01-01T10:00:00", end_time="2025-01-01T12:00:00", total_seats=50))
    services.create_event(db, schemas.EventCreate(name="Event 2", venue="Venue 2", start_time="2025-02-01T10:00:00", end_time="2025-02-01T12:00:00", total_seats=100))
    
    response = client.get("/events")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "seats" in data[0]
    assert len(data[0]["seats"]) == 50

def test_successful_seat_booking(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(name="Bookable Event", venue="Venue", start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00", total_seats=2))
    response = client.post(
        "/bookings",
        headers={"X-User-ID": "1"},
        json={"user_id": 1, "event_id": event.id, "seat_number": "Seat-1"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == 1
    assert data["event_id"] == event.id
    assert "seat_id" in data

def test_booking_already_booked_seat(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(name="Bookable Event", venue="Venue", start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00", total_seats=2))
    services.create_booking(db, schemas.BookingCreate(user_id=1, event_id=event.id, seat_number="Seat-2"))

    response = client.post(
        "/bookings",
        headers={"X-User-ID": "2"},
        json={"user_id": 2, "event_id": event.id, "seat_number": "Seat-2"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Seat is already booked"

def test_booking_nonexistent_seat(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(name="Bookable Event", venue="Venue", start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00", total_seats=2))
    response = client.post(
        "/bookings",
        headers={"X-User-ID": "1"},
        json={"user_id": 1, "event_id": event.id, "seat_number": "Seat-99"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Seat not found for this event"

def test_list_my_bookings_with_seat_info(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(name="My Booking Event", venue="Venue", start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00", total_seats=5))
    services.create_booking(db, schemas.BookingCreate(user_id=1, event_id=event.id, seat_number="Seat-3"))
    
    response = client.get("/users/me/bookings", headers={"X-User-ID": "1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "seat" in data[0]
    assert data[0]["seat"]["seat_number"] == "Seat-3"

def test_cancel_booking_and_seat_becomes_available(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(name="Cancellable Event", venue="Venue", start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00", total_seats=1))
    booking = services.create_booking(db, schemas.BookingCreate(user_id=1, event_id=event.id, seat_number="Seat-1"))

    client.delete(f"/bookings/{booking.id}", headers={"X-User-ID": "1"})

    # Verify the booking is no longer active
    response = client.get("/users/me/bookings", headers={"X-User-ID": "1"})
    assert len(response.json()) == 0

    # Verify the seat can be booked again
    response = client.post("/bookings", headers={"X-User-ID": "2"}, json={"user_id": 2, "event_id": event.id, "seat_number": "Seat-1"})
    assert response.status_code == 201
