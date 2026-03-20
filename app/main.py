from fastapi import FastAPI

from app.api.routers.auth_router import router as auth_router
from app.api.routers.user_router import router as user_router
from app.api.routers.test_router import router as test_router


app = FastAPI() # Создаем экземпляр приложения


# Подключаем все роутеры
app.include_router(auth_router)
app.include_router(user_router)

# Тестовый роутер
app.include_router(test_router)
