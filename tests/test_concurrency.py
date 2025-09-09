import threading
from fastapi.testclient import TestClient
import pytest
from tests.conftest import engine

def book_seat_thread(client: TestClient, event_id: int, seat_number: str, user_id: int, results: list):
    response = client.post(
        "/bookings",
        json={"user_id": user_id, "event_id": event_id, "seat_number": seat_number}
    )
    results.append(response.status_code)

@pytest.mark.skipif(engine.dialect.name == "sqlite", reason="SQLite does not support SELECT FOR UPDATE on seats")
def test_concurrent_seat_bookings_prevent_overselling(client: TestClient):
    event_id = 2  
    seat_to_book = "Seat-1"
    num_concurrent_requests = 3

    results = []
    threads = []

    user_ids = [1, 2, 10] 

    for i in range(num_concurrent_requests):
        thread = threading.Thread(
            target=book_seat_thread,
            args=(client, event_id, seat_to_book, user_ids[i], results)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    successful_bookings = [res for res in results if res == 201]
    assert len(successful_bookings) == 1, f"Expected 1 successful booking, but got {len(successful_bookings)}"

    failed_bookings = [res for res in results if res == 400]
    assert len(failed_bookings) == num_concurrent_requests - 1, f"Expected {num_concurrent_requests - 1} failed bookings, but got {len(failed_bookings)}"

    response = client.get(f"/events")
    event_data = next((e for e in response.json() if e["id"] == event_id), None)
    assert event_data is not None

    booked_seat = next((s for s in event_data["seats"] if s["seat_number"] == seat_to_book), None)
    assert booked_seat is not None
    assert booked_seat["booking_id"] is not None
