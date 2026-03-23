from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.bot.middlewares.auth import AuthMiddleware
from app.bot.middlewares.database import DatabaseSessionMiddleware
from app.bot.handlers import *
from app.database.database import async_session_maker

def setup_dispatcher() -> Dispatcher:
    # TODO: Переделать под Redis
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(channels.router)
    dp.include_router(digest.router)
    dp.include_router(favorites.router)
    #dp.include_router(admin.router)

    dp.update.middleware(AuthMiddleware())
    dp.update.middleware(DatabaseSessionMiddleware(session_pool=async_session_maker))

    return dp