from fastapi import APIRouter, Depends

from app.api.schemas.user import SUserProfile
from app.database.models.user import User
from app.utils.auth.dependencies import get_current_user


router = APIRouter(prefix="/user", tags=["users"])


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)) -> SUserProfile:
    return SUserProfile(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        role=user.role,
        token_balance=user.token_balance,
    )


@router.patch("/me")
async def edit_user_data():
    pass


@router.get("/me/subscription")
async def get_user_subscription():
    pass
