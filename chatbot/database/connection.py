import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import redis
from typing import Optional
from chatbot.config import settings

# Configuración de PostgreSQL
def crear_engine_postgresql():
    """Crea el engine de SQLAlchemy para PostgreSQL"""
    try:
        # Configuración del pool de conexiones
        engine = create_engine(
            settings.DB_URL,
            poolclass=QueuePool,
            pool_size=10,  # Número máximo de conexiones en el pool
            max_overflow=20,  # Conexiones adicionales que se pueden crear
            pool_pre_ping=True,  # Verifica conexiones antes de usarlas
            pool_recycle=3600,  # Recicla conexiones cada hora
            echo=False  # Set to True para ver las consultas SQL
        )
        return engine
    except Exception as e:
        print(f"Error al crear engine de PostgreSQL: {e}")
        return None

# Configuración de Redis
def crear_cliente_redis():
    """Crea el cliente de Redis para chat memory"""
    try:
        # Usar directamente las variables de configuración
        cliente_redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True,  # Decodifica automáticamente las respuestas
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Verificar conexión
        cliente_redis.ping()
        print(f"Conexión a Redis establecida correctamente en {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        return cliente_redis
            
    except Exception as e:
        print(f"Error al conectar con Redis: {e}")
        return None

# Variables globales para las conexiones
engine_postgresql: Optional[object] = None
cliente_redis: Optional[object] = None
SessionLocal: Optional[object] = None

def inicializar_conexiones():
    """Inicializa todas las conexiones de base de datos"""
    global engine_postgresql, cliente_redis, SessionLocal
    
    # Inicializar PostgreSQL
    engine_postgresql = crear_engine_postgresql()
    if engine_postgresql:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgresql)
        print(f"Conexión a PostgreSQL establecida correctamente en {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    # Inicializar Redis
    cliente_redis = crear_cliente_redis()

def obtener_session_db():
    """Obtiene una sesión de base de datos"""
    if not SessionLocal:
        raise Exception("Base de datos no inicializada")
    
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e

def obtener_cliente_redis():
    """Obtiene el cliente de Redis"""
    if not cliente_redis:
        raise Exception("Redis no inicializado")
    return cliente_redis
