import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Configuración de Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    API_KEY: str = os.getenv("API_KEY", "")
    
    # Configuración de PostgreSQL
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "ELECCIA_CHATBOT")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "123456")
    
    # Configuración de Redis (compatible con Docker)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # Configuración de Oracle Database
    ORACLE_USER: str = os.getenv("ORACLE_USER", "eleccia")
    ORACLE_PASS: str = os.getenv("ORACLE_PASS", "desarrollo")
    ORACLE_DSN: str = os.getenv("ORACLE_DSN", "oda-x8-2ha-vm1:1521/OPEXTDESA")
    ORACLE_SCHEMA: str = "ELECCIA"
    
    @property
    def DB_URL(self) -> str:
        """Construye la URL de conexión a PostgreSQL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def REDIS_URL(self) -> str:
        """Construye la URL de conexión a Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def ORACLE_URL(self) -> str:
        """Construye la URL de conexión a Oracle"""
        return f"oracle+oracledb://{self.ORACLE_USER}:{self.ORACLE_PASS}@{self.ORACLE_DSN}"

settings = Settings()
