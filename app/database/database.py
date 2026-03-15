from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


DATABASE_URL = settings.DATABASE_URL

# Асинхронный движок для обработки запросов 
engine = create_async_engine(DATABASE_URL)

# Создатель сессий
async_session_maker = async_sessionmaker(engine=engine, expire_on_commit=False)

# Базовый класс для всех моделей
class Base(DeclarativeBase):
    pass
