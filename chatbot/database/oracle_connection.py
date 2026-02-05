import oracledb
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from chatbot.config import settings
import logging
from sqlalchemy.ext.declarative import declarative_base
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detectar si estamos en Docker/Linux
_is_docker = os.path.exists("/.dockerenv") or os.path.exists("/proc/self/cgroup")

# IMPORTANTE: El problema DPY-2017 ocurre cuando init_oracle_client() se llama dos veces
# con argumentos diferentes. SQLAlchemy con thick_mode=True intenta inicializarlo automáticamente.
#
# SOLUCIÓN: Inicializar manualmente UNA VEZ antes de crear el engine, y cuando SQLAlchemy
# intente inicializarlo de nuevo, capturar el error y continuar (porque ya está inicializado).

# Variable global para rastrear si ya se inicializó
_oracle_client_initialized = False

def _init_oracle_client_once():
    """
    Inicializa el cliente Oracle una sola vez antes de crear el engine.
    Esto asegura que se inicializa con los parámetros correctos (lib_dir en Docker).
    """
    global _oracle_client_initialized
    
    if _oracle_client_initialized:
        return
    
    try:
        if _is_docker:
            # En Docker/Linux, usar lib_dir
            if os.path.exists(settings.ORACLEDB_CLIENT_PATH):
                oracledb.init_oracle_client(lib_dir=settings.ORACLEDB_CLIENT_PATH)
                logger.info(f"✅ Cliente Oracle inicializado (Linux/Docker) desde {settings.ORACLEDB_CLIENT_PATH}")
            else:
                # Fallback: intentar sin lib_dir
                oracledb.init_oracle_client()
                logger.warning(f"⚠️ Cliente Oracle inicializado sin lib_dir (path no encontrado: {settings.ORACLEDB_CLIENT_PATH})")
        else:
            # En Windows, inicializar sin lib_dir
            oracledb.init_oracle_client()
            logger.info("✅ Cliente Oracle inicializado (Windows)")
        
        _oracle_client_initialized = True
    except oracledb.exceptions.ProgrammingError as e:
        # Si ya está inicializado (error DPY-2017), está bien, continuar
        error_str = str(e).lower()
        if "already called" in error_str or "dpy-2017" in error_str:
            logger.info("✅ Cliente Oracle ya estaba inicializado previamente")
            _oracle_client_initialized = True
        else:
            logger.error(f"❌ Error inicializando cliente Oracle: {e}")
            raise
    except Exception as e:
        logger.error(f"❌ Error inicializando cliente Oracle: {e}")
        raise

# Inicializar el cliente antes de crear el engine
_init_oracle_client_once()

# Crear engine con thick_mode=True
# SQLAlchemy detectará que el cliente ya está inicializado y no debería intentar inicializarlo de nuevo.
# Sin embargo, si lo intenta y falla, el error se propagará. En ese caso, el cliente ya está
# inicializado correctamente, así que podemos continuar.
try:
    motor = create_engine(
        f"oracle+oracledb://{settings.ORACLE_USER}:{settings.ORACLE_PASS}@{settings.ORACLE_DSN}",
        thick_mode=True,  # Usar modo thick (cliente ya inicializado arriba)
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30
    )
    logger.info("✅ Engine Oracle creado exitosamente")
except Exception as e:
    # Si SQLAlchemy intenta inicializar de nuevo y falla, el cliente ya está inicializado,
    # así que podemos crear el engine sin thick_mode (aunque el cliente está en modo thick)
    error_str = str(e).lower()
    if "already called" in error_str or "dpy-2017" in error_str:
        logger.warning("⚠️ SQLAlchemy intentó inicializar el cliente de nuevo. El cliente ya está inicializado, continuando...")
        # El cliente ya está en modo thick, así que podemos usar thick_mode=False
        # (SQLAlchemy no intentará inicializarlo de nuevo)
        motor = create_engine(
            f"oracle+oracledb://{settings.ORACLE_USER}:{settings.ORACLE_PASS}@{settings.ORACLE_DSN}",
            thick_mode=False,  # No intentar inicializar (ya está inicializado)
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30
        )
        logger.info("✅ Engine Oracle creado exitosamente (sin thick_mode)")
    else:
        # Otro error, re-lanzar
        logger.error(f"❌ Error creando engine Oracle: {e}")
        raise

# Configurar la sesión de la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)
OracleBase = declarative_base()

# Dependencia para obtener la sesión de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
