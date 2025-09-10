import datetime as dt
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class SeatBase(BaseModel):
    seat_number: str

class UserBase(BaseModel):
    email: str
    username: str

class EventBase(BaseModel):
    name: str
    venue: str
    start_time: dt.datetime
    end_time: dt.datetime

class BookingBase(BaseModel):
    user_id: int
    event_id: int

class UserCreate(UserBase):
    password: str
    role: str = 'user'

class EventCreate(EventBase):
    total_seats: int

class BookingCreate(BookingBase):
    seat_number: Optional[str] = None

class Seat(SeatBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class User(UserBase):
    id: int
    role: str
    model_config = ConfigDict(from_attributes=True)

class Event(EventBase):
    id: int
    seats: List[Seat] = []
    model_config = ConfigDict(from_attributes=True)

class Booking(BaseModel):
    id: int
    user_id: int
    event_id: int
    seat_id: int
    status: str
    created_at: dt.datetime
    model_config = ConfigDict(from_attributes=True)

class BookingDetails(Booking):
    event: EventBase 
    seat: SeatBase
    model_config = ConfigDict(from_attributes=True)

class WaitlistEntry(BaseModel):
    id: int
    user_id: int
    event_id: int
    created_at: dt.datetime
    model_config = ConfigDict(from_attributes=True)

class Notification(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: dt.datetime
    model_config = ConfigDict(from_attributes=True)
