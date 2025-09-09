import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models, services, schemas

def test_add_to_waitlist_when_event_is_full(client: TestClient, db: Session):
    admin_user = db.query(models.User).filter(models.User.role == "admin").first()
    user1 = models.User(email="testuser1@example.com", username="testuser1")
    user2 = models.User(email="testuser2@example.com", username="testuser2")
    db.add_all([user1, user2])
    db.commit()

    event = services.create_event(db, schemas.EventCreate(
        name="Sold Out Show", venue="Tiny Hall",
        start_time="2025-01-01T19:00:00", end_time="2025-01-01T22:00:00",
        total_seats=1
    ))

    booking_data = {"user_id": user1.id, "event_id": event.id}
    response = client.post("/bookings", json=booking_data)
    assert response.status_code == 201

    booking_data_user2 = {"user_id": user2.id, "event_id": event.id}
    response_user2 = client.post("/bookings", json=booking_data_user2)

    assert response_user2.status_code == 202
    assert response_user2.json()["detail"] == "Event is full. You have been added to the waitlist."

    waitlist_entry = db.query(models.WaitlistEntry).filter(
        models.WaitlistEntry.user_id == user2.id,
        models.WaitlistEntry.event_id == event.id
    ).first()
    assert waitlist_entry is not None

def test_cancel_booking_triggers_notification(client: TestClient, db: Session):
    admin_user = db.query(models.User).filter(models.User.role == "admin").first()
    user1 = models.User(email="testuser3@example.com", username="testuser3")
    user2 = models.User(email="testuser4@example.com", username="testuser4")
    db.add_all([user1, user2])
    db.commit()

    event = services.create_event(db, schemas.EventCreate(
        name="Limited Spot Workshop", venue="Maker Space",
        start_time="2025-02-01T10:00:00", end_time="2025-02-01T14:00:00",
        total_seats=1
    ))

    booking_resp = client.post("/bookings", json={"user_id": user1.id, "event_id": event.id})
    booking_id = booking_resp.json()["id"]

    client.post("/bookings", json={"user_id": user2.id, "event_id": event.id}) 

    response = client.delete(f"/bookings/{booking_id}", headers={"X-User-ID": str(user1.id)})
    assert response.status_code == 204

    notification = db.query(models.Notification).filter(models.Notification.user_id == user2.id).first()
    assert notification is not None
    assert f"A spot has opened up for the event: '{event.name}'" in notification.message

    waitlist_entry = db.query(models.WaitlistEntry).filter(models.WaitlistEntry.user_id == user2.id).first()
    assert waitlist_entry is None

def test_user_can_view_and_leave_waitlist(client: TestClient, db: Session):
    user = models.User(email="testuser5@example.com", username="testuser5")
    db.add(user)
    db.commit()
    event = services.create_event(db, schemas.EventCreate(
        name="Full Event", venue="Stadium",
        start_time="2025-03-01T19:00:00", end_time="2025-03-01T22:00:00",
        total_seats=0
    ))
    waitlist_entry = models.WaitlistEntry(user_id=user.id, event_id=event.id)
    db.add(waitlist_entry)
    db.commit()

    response = client.get("/waitlists/me", headers={"X-User-ID": str(user.id)})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["event_id"] == event.id
    waitlist_entry_id = response.json()[0]["id"]

    response = client.delete(f"/waitlists/{waitlist_entry_id}", headers={"X-User-ID": str(user.id)})
    assert response.status_code == 204

    db_entry = db.query(models.WaitlistEntry).filter_by(id=waitlist_entry_id).first()
    assert db_entry is None

def test_user_can_view_notifications(client: TestClient, db: Session):
    user = models.User(email="testuser6@example.com", username="testuser6")
    db.add(user)
    db.commit()
    notification = models.Notification(user_id=user.id, message="Test notification")
    db.add(notification)
    db.commit()

    response = client.get("/users/me/notifications", headers={"X-User-ID": str(user.id)})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["message"] == "Test notification"
