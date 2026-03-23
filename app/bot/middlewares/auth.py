from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.database import async_session_maker
from app.dao.user import UserDAO
from app.dao.subscription import SubscriptionDAO


class AuthMiddleware(BaseMiddleware):
    def __init__(self):
        self.cache = {}

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        tg_user = data.get("event_from_user")

        if not tg_user:
            return await handler(event, data)

        if tg_user.id in self.cache:
            data["user"] = self.cache[tg_user.id]
            return await handler(event, data)

        async with async_session_maker() as session:
            user_dao = UserDAO(session)

            # Сначала проверяем, есть ли пользователь в базе (как в API)
            user = await user_dao.get_by_telegram_id(tg_user.id)

            # Если пользователя нет — создаем
            if not user:
                subscription_dao = SubscriptionDAO(session)
                base_subscription = await subscription_dao.get_one_or_none(name="Base")

                user = await user_dao.create(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    subscription_id=base_subscription.id if base_subscription else None
                )

                await session.commit()
                # Подтягиваем актуальные данные (включая сгенерированный ID, даты и т.д.)
                await session.refresh(user)

        self.cache[tg_user.id] = user
        data["user"] = user

        return await handler(event, data)