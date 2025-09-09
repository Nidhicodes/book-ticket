from fastapi import Header, HTTPException, status
from typing import Optional

def get_current_user(x_user_id: Optional[int] = Header(None)):
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not provided in X-User-ID header"
        )
    return x_user_id
