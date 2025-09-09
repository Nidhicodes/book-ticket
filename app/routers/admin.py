from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Any

from app import services, schemas
from app.database import get_db

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={403: {"description": "Admin privileges required"}},
)

def get_admin_user(x_user_role: Optional[str] = Header(None)):
    if x_user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return x_user_role

@router.post("/events", response_model=schemas.Event, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_admin_user)])
def create_new_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    Create a new event. (Admin only)
    """
    return services.create_event(db=db, event=event)

@router.put("/events/{event_id}", response_model=schemas.Event, dependencies=[Depends(get_admin_user)])
def update_existing_event(event_id: int, event_update: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    Update an existing event. (Admin only)
    """
    return services.update_event(db=db, event_id=event_id, event_update=event_update)

@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_admin_user)])
def delete_existing_event(event_id: int, db: Session = Depends(get_db)):
    """
    Delete an event. (Admin only)
    """
    services.delete_event(db=db, event_id=event_id)
    return None

@router.get("/analytics", response_model=dict, dependencies=[Depends(get_admin_user)])
def get_system_analytics(db: Session = Depends(get_db)):
    """
    Get booking analytics, such as total bookings and capacity utilization. (Admin only)
    """
    return services.get_analytics(db=db)
