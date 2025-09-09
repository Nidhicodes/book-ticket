import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import services, schemas

def test_list_all_events(client: TestClient, db: Session):
    services.create_event(db, schemas.EventCreate(
        name="Event for Listing", venue="Venue",
        start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00",
        total_seats=5
    ))
    response = client.get("/events")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert "seats" in response.json()[0]

def test_successful_booking(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(
        name="Bookable Event", venue="Venue",
        start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00",
        total_seats=2
    ))

    response = client.post(
        "/bookings",
        json={"user_id": 1, "event_id": event.id}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == 1
    assert "seat_id" in data

def test_booking_full_event_goes_to_waitlist(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(
        name="Single Seat Event", venue="Venue",
        start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00",
        total_seats=1
    ))
    client.post("/bookings", json={"user_id": 1, "event_id": event.id})

    response = client.post("/bookings", json={"user_id": 2, "event_id": event.id})

    assert response.status_code == 202
    assert "added to the waitlist" in response.json()["detail"]

def test_list_my_bookings(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(
        name="My Booking Event", venue="Venue",
        start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00",
        total_seats=1
    ))
    client.post("/bookings", json={"user_id": 1, "event_id": event.id})

    response = client.get("/users/me/bookings", headers={"X-User-ID": "1"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "seat" in data[0]
    assert data[0]["seat"]["seat_number"] == "Seat-1"

def test_cancel_booking_and_another_can_book(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(
        name="Cancellable Event", venue="Venue",
        start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00",
        total_seats=1
    ))
    booking_response = client.post("/bookings", json={"user_id": 1, "event_id": event.id})
    booking_id = booking_response.json()["id"]

    client.delete(f"/bookings/{booking_id}", headers={"X-User-ID": "1"})

    response = client.post(
        "/bookings",
        json={"user_id": 2, "event_id": event.id}
    )
    assert response.status_code == 201
