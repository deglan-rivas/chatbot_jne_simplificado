import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Cargar .env pero NO sobrescribir variables de entorno existentes
# Esto permite que docker-compose.yml sobrescriba con environment:
load_dotenv(override=False)

def _detect_docker_environment():
    """Detecta si estamos ejecutando en Docker"""
    # Verificar si estamos en Docker de varias formas
    if os.path.exists("/.dockerenv"):
        return True
    # Verificar si el hostname es un contenedor Docker
    try:
        with open("/proc/self/cgroup", "r") as f:
            return "docker" in f.read()
    except:
        pass
    return False

# Detectar si estamos en Docker
IS_DOCKER = _detect_docker_environment()

class Settings:
    # Configuración de Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    API_KEY: str = os.getenv("API_KEY", "")
    
    # Configuración de PostgreSQL
    # Si estamos en Docker y no hay DB_HOST definido, usar nombre de servicio
    _default_db_host = "postgres" if IS_DOCKER else "localhost"
    _db_host_env = os.getenv("DB_HOST")
    DB_HOST: str = _db_host_env if _db_host_env else _default_db_host
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "ELECCIA_CHATBOT")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "123456")
    
    # Configuración de Redis (compatible con Docker)
    # Si estamos en Docker y no hay REDIS_HOST definido, usar nombre de servicio
    _default_redis_host = "redis" if IS_DOCKER else "localhost"
    _redis_host_env = os.getenv("REDIS_HOST")
    REDIS_HOST: str = _redis_host_env if _redis_host_env else _default_redis_host
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    
    # Configuración de Oracle Database
    ORACLE_USER: str = os.getenv("ORACLE_USER", "eleccia")
    ORACLE_PASS: str = os.getenv("ORACLE_PASS", "desarrollo")
    ORACLE_DSN: str = os.getenv("ORACLE_DSN", "oda-x8-2ha-vm1:1521/OPEXTDESA")
    ORACLE_SCHEMA: str = "ELECCIA"

    TNS_ADMIN = os.getenv("TNS_ADMIN", "/app")
    ORACLEDB_CLIENT_PATH = os.getenv("ORACLEDB_CLIENT_PATH", "/opt/oracle/instantclient_23_8")
    
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

# Crear instancia y forzar logging
settings = Settings()

# Log de configuración al cargar el módulo
logger.info(f"🔧 Configuración de conexiones cargada:")
logger.info(f"   Docker detectado: {IS_DOCKER}")
logger.info(f"   DB_HOST (env): {os.getenv('DB_HOST', 'NO DEFINIDO')}")
logger.info(f"   DB_HOST (final): {settings.DB_HOST}")
logger.info(f"   REDIS_HOST (env): {os.getenv('REDIS_HOST', 'NO DEFINIDO')}")
logger.info(f"   REDIS_HOST (final): {settings.REDIS_HOST}")
logger.info(f"   DB_NAME: {settings.DB_NAME}")
