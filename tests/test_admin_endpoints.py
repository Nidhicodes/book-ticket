from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import services, schemas

def test_admin_access_denied(client: TestClient):
    response = client.get("/admin/analytics", headers={"X-User-Role": "user"})
    assert response.status_code == 403

def test_create_event_by_admin_generates_seats(client: TestClient, db: Session):
    response = client.post(
        "/admin/events",
        headers={"X-User-Role": "admin"},
        json={
            "name": "Admin Created Event",
            "venue": "Admin Venue",
            "start_time": "2026-01-01T10:00:00",
            "end_time": "2026-01-01T12:00:00",
            "total_seats": 100
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Admin Created Event"
    assert "seats" in data
    assert len(data["seats"]) == 100

def test_update_event_details_by_admin(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(name="Event to Update", venue="Venue", start_time="2025-01-01T10:00:00", end_time="2025-01-01T12:00:00", total_seats=5))

    response = client.put(
        f"/admin/events/{event.id}",
        headers={"X-User-Role": "admin"},
        json={
            "name": "Updated Name",
            "venue": "Updated Venue",
            "start_time": "2025-01-01T10:00:00",
            "end_time": "2025-01-01T12:00:00",
            "total_seats": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert len(data["seats"]) == 5

def test_delete_event_with_no_bookings(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(name="To Be Deleted", venue="Nowhere", start_time="2026-01-01T10:00:00", end_time="2026-01-01T12:00:00", total_seats=1))

    response = client.delete(
        f"/admin/events/{event.id}",
        headers={"X-User-Role": "admin"}
    )
    assert response.status_code == 204

def test_cannot_delete_event_with_active_bookings(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(name="Event with Booking", venue="Venue", start_time="2025-01-01T10:00:00", end_time="2025-01-01T12:00:00", total_seats=1))
    client.post("/bookings", json={"user_id": 1, "event_id": event.id})

    response = client.delete(
        f"/admin/events/{event.id}",
        headers={"X-User-Role": "admin"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot delete event with active bookings"

def test_get_analytics_with_seat_data(client: TestClient, db: Session):
    event = services.create_event(db, schemas.EventCreate(name="Analytics Event", venue="Venue", start_time="2025-01-01T10:00:00", end_time="2025-01-01T12:00:00", total_seats=10))
    client.post("/bookings", json={"user_id": 1, "event_id": event.id})

    response = client.get(
        "/admin/analytics",
        headers={"X-User-Role": "admin"}
    )
    assert response.status_code == 200
    data = response.json()

    assert "capacity_utilization_per_event" in data
    utilization_data = next((e for e in data["capacity_utilization_per_event"] if e["event_id"] == event.id), None)
    assert utilization_data is not None
    assert utilization_data["total_seats"] == 10
    assert utilization_data["booked_seats"] == 1
    assert utilization_data["utilization"] == 0.1
