from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class STelegramAuthData(BaseModel):
    id: int
    first_name: str
    lastname: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
