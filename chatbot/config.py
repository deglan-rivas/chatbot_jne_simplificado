import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    API_KEY: str = os.getenv("API_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DB_URL: str = os.getenv("DB_URL", "sqlite:///./chatbot.db")

settings = Settings()
