from pydantic import BaseModel
from uuid import UUID
from app.database.models.user import UserRole

class SUserProfile(BaseModel):
    id: UUID
    telegram_id: int
    username: str | None
    first_name: str | None
    role: UserRole
    token_balance: int

    class Config:
        from_attributes = True
