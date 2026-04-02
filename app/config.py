from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Существующие поля
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    SECRET_KEY: str
    ALGORITHM: str
    BOT_TOKEN: str
    WIDGET_BOT_TOKEN: str | None = None
    WIDGET_BOT_USERNAME: str = "ru_news_manager_bot"

    API_ID: int
    API_HASH: str
    PHONE_NUMBER: str

    REDIS_HOST: str
    REDIS_PORT: int

    OLLAMA_HOST: str
    SAIGA_MODEL: str

    AUDIO_STORAGE_PATH: str

    @property
    def AUDIO_STORAGE_DIR(self) -> Path:
        return Path(self.AUDIO_STORAGE_PATH)

    @property
    def WIDGET_BOT_TOKEN_ACTUAL(self) -> str:
        return self.WIDGET_BOT_TOKEN or self.BOT_TOKEN

    @property
    def REDIS_URL(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"

settings = Settings()
