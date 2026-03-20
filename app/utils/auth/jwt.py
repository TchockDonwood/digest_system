from datetime import timedelta
from jose import jwt

from app.utils.time_utils import utc_now
from app.config import settings

def create_access_token(user_id: str | int):
    payload = {
        "sub": str(user_id),
        "exp": utc_now() + timedelta(days=3)
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
