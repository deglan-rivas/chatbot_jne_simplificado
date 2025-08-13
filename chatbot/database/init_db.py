
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

sys.path.append(os.path.join(project_root, 'chatbot'))
from chatbot.database.connection import crear_engine_postgresql, inicializar_conexiones
from chatbot.database.models import Base
from sqlalchemy import inspect

def crear_tablas():
    """Crea todas las tablas en la base de datos PostgreSQL"""
    try:
        # Crear engine
        engine = crear_engine_postgresql()
        if not engine:
            print("Error: No se pudo crear el engine de PostgreSQL")
            return False
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente en PostgreSQL")
        
        # Verificar que las tablas se crearon usando inspect() moderno
        inspector = inspect(engine)
        tablas_creadas = inspector.get_table_names()
        print(f"📋 Tablas disponibles: {tablas_creadas}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        return False

def verificar_conexion_redis():
    """Verifica la conexión a Redis"""
    try:
        from chatbot.database.connection import obtener_cliente_redis
        redis_client = obtener_cliente_redis()
        redis_client.ping()
        print("✅ Conexión a Redis verificada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al conectar con Redis: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Inicializando base de datos...")
    
    # Primero inicializar todas las conexiones
    print("\n🔌 Inicializando conexiones...")
    inicializar_conexiones()
    
    # Verificar Redis
    print("\n📡 Verificando conexión a Redis...")
    verificar_conexion_redis()
    
    # Crear tablas PostgreSQL
    print("\n🗄️ Creando tablas en PostgreSQL...")
    crear_tablas()
    
    print("\n✅ Inicialización completada")
