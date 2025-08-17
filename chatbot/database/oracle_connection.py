import oracledb
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from chatbot.config import settings
import logging
from sqlalchemy.ext.declarative import declarative_base

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# windows
oracledb.init_oracle_client()

# linux
# oracledb.init_oracle_client(lib_dir=settings.ORACLEDB_CLIENT_PATH)

motor = create_engine(
    f"oracle+oracledb://{settings.ORACLE_USER}:{settings.ORACLE_PASS}@{settings.ORACLE_DSN}",
    thick_mode=True,  # Forzar modo thick
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30
)

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
