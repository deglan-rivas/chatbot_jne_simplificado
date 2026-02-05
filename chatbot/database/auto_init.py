"""
Script para inicialización automática de la base de datos
Se ejecuta al iniciar la aplicación si las tablas no existen
"""
import logging
import time
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from chatbot.database.connection import crear_engine_postgresql, obtener_cliente_redis
from chatbot.database.models import Base

logger = logging.getLogger(__name__)

def verificar_tablas_existen(engine) -> bool:
    """Verifica si las tablas ya existen en la base de datos"""
    try:
        inspector = inspect(engine)
        tablas = inspector.get_table_names()
        return "conversaciones" in tablas
    except Exception as e:
        logger.warning(f"Error al verificar tablas: {e}")
        return False

def crear_tablas_si_no_existen(max_retries=5, retry_delay=2):
    """
    Crea las tablas si no existen
    Con reintentos en caso de que PostgreSQL aún no esté listo
    """
    for attempt in range(max_retries):
        try:
            engine = crear_engine_postgresql()
            if not engine:
                if attempt < max_retries - 1:
                    logger.warning(f"Intento {attempt + 1}/{max_retries}: No se pudo crear el engine de PostgreSQL, reintentando...")
                    time.sleep(retry_delay)
                    continue
                logger.error("No se pudo crear el engine de PostgreSQL después de varios intentos")
                return False
            
            # Verificar si las tablas ya existen
            if verificar_tablas_existen(engine):
                logger.info("✅ Las tablas ya existen en PostgreSQL")
                return True
            
            # Crear todas las tablas
            logger.info("📋 Creando tablas en PostgreSQL...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tablas creadas exitosamente en PostgreSQL")
            
            # Verificar que se crearon correctamente
            inspector = inspect(engine)
            tablas_creadas = inspector.get_table_names()
            logger.info(f"📋 Tablas disponibles: {tablas_creadas}")
            
            return True
            
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Intento {attempt + 1}/{max_retries}: PostgreSQL aún no está listo ({str(e)[:100]}), reintentando en {retry_delay}s...")
                time.sleep(retry_delay)
                continue
            else:
                logger.error(f"❌ Error al conectar con PostgreSQL después de {max_retries} intentos: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Error al crear tablas: {e}", exc_info=True)
            return False
    
    return False

def verificar_redis():
    """Verifica la conexión a Redis"""
    try:
        redis_client = obtener_cliente_redis()
        if redis_client:
            redis_client.ping()
            logger.info("✅ Conexión a Redis verificada correctamente")
            return True
        return False
    except Exception as e:
        logger.warning(f"⚠️ Redis no está disponible: {e}")
        logger.warning("   El sistema funcionará pero sin memoria de chat")
        return False

def inicializar_bases_de_datos():
    """
    Inicializa las bases de datos (PostgreSQL y Redis)
    Se ejecuta automáticamente al iniciar la aplicación
    """
    logger.info("🚀 Inicializando bases de datos...")
    
    # Verificar Redis
    verificar_redis()
    
    # Crear tablas PostgreSQL si no existen
    crear_tablas_si_no_existen()
    
    logger.info("✅ Inicialización de bases de datos completada")
