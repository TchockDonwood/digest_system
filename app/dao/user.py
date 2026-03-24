from datetime import datetime
from typing import Literal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.base import BaseDAO
from app.database.models.user import User


class UserDAO(BaseDAO):
    
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)
    
    async def get_by_telegram_id(self, telegram_id: int | str):
        telegram_id = int(telegram_id)
        return await self.get_one_or_none(telegram_id=telegram_id)

    async def get_user_registrations(
        self,
        date_from: datetime,
        date_to: datetime,
        group_by: Literal["day", "week", "month"] = "day",
    ):
        date_trunc = func.date_trunc(group_by, User.created_at)

        stmt = select(
            date_trunc.label("period"),
            func.count().label("registrations")
        ).where(
            User.created_at.between(date_from, date_to)
        ).group_by("period").order_by("period")

        result = await self.session.execute(stmt)
        return result.mappings().all()
