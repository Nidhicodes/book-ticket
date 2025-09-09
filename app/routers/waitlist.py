from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import services, schemas, models
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/waitlists",
    tags=["waitlists"],
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=List[schemas.WaitlistEntry])
def list_my_waitlist_entries(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    """
    Get all waitlist entries for the current user.
    """
    return services.get_user_waitlist_entries(db=db, user_id=current_user_id)

@router.delete("/{waitlist_entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def leave_waitlist(waitlist_entry_id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user)):
    """
    Remove the current user from a waitlist.
    A user can only remove themselves from a waitlist.
    """
    services.remove_from_waitlist(db=db, waitlist_entry_id=waitlist_entry_id, user_id=current_user_id)
    return None
