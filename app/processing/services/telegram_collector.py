import asyncio
import logging
from datetime import datetime
from typing import List
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError
from sqlalchemy import select

from app.database.models.channel import TelegramChannel
from app.database.models.news import News
from app.database.database import async_session_maker

logger = logging.getLogger(__name__)

class TelegramCollector:
    def __init__(self, api_id: int, api_hash: str, phone: str, session_name: str = 'user_session'):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_name = session_name
        self.client = None

    async def _ensure_client(self):
        if self.client is None:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start(phone=self.phone)
            logger.info("✅ TelegramCollector: клиент подключён")

    async def get_entity(self, link: str):
        await self._ensure_client()
        return await self.client.get_entity(link)

    async def collect_news_for_channels(self, channels: List[TelegramChannel], date_from: datetime) -> List[News]:
        logger.info(f"Начинаем сбор новостей из {len(channels)} каналов с {date_from}")
        await self._ensure_client()
        new_news = []

        async with async_session_maker() as session:
            for channel in channels:
                if not channel.is_active:
                    continue
                channel_new_news = []
                try:
                    entity = await self.client.get_entity(channel.username)  # username = link
                    logger.info(f"📡 Скачиваем сообщения из {channel.username}...")
                    async for msg in self.client.iter_messages(entity, reverse=False):
                        if msg.date.replace(tzinfo=None) < date_from:
                            break
                        if msg.text:
                            stmt = select(News).where(News.telegram_message_id == msg.id)
                            existing = await session.execute(stmt)
                            if not existing.scalar_one_or_none():
                                news_item = News(
                                    channel_id=channel.id,
                                    telegram_message_id=msg.id,
                                    text=msg.text,
                                    published_at=msg.date.replace(tzinfo=None)
                                )
                                session.add(news_item)
                                new_news.append(news_item)
                                channel_new_news.append(news_item)
                    await session.commit()
                    logger.info(f"Канал {channel.username}: загружено {len(channel_new_news)} новых сообщений")
                except ChannelPrivateError:
                    logger.error(f"❌ Канал {channel.username} закрыт. Помечаем как неактивный.")
                    channel.is_active = False
                    await session.commit()
                except FloodWaitError as e:
                    logger.warning(f"⚠️ Ожидание {e.seconds} сек...")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    logger.error(f"❌ Ошибка при обработке {channel.username}: {e}")

        logger.info(f"Всего загружено {len(new_news)} новых новостей")
        return new_news

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()