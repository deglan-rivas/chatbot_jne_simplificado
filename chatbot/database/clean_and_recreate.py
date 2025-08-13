"""
Script para limpiar la base de datos y recrear las tablas con el nuevo modelo.
Este script elimina las tablas existentes y crea las nuevas con la estructura simplificada.
"""

import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from chatbot.database.connection import crear_engine_postgresql, inicializar_conexiones
from chatbot.database.models import Base
from sqlalchemy import inspect, text

def limpiar_base_datos():
    """Elimina todas las tablas existentes de la base de datos"""
    try:
        # Inicializar conexiones
        inicializar_conexiones()
        
        # Crear engine
        engine = crear_engine_postgresql()
        if not engine:
            print("❌ Error: No se pudo crear el engine de PostgreSQL")
            return False
        
        # Obtener inspector
        inspector = inspect(engine)
        tablas_existentes = inspector.get_table_names()
        
        if not tablas_existentes:
            print("ℹ️ No hay tablas para eliminar")
            return True
        
        print(f"🗑️ Eliminando {len(tablas_existentes)} tablas existentes...")
        
        # Eliminar todas las tablas
        Base.metadata.drop_all(bind=engine)
        
        print("✅ Tablas eliminadas correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al limpiar base de datos: {e}")
        return False

def crear_nuevas_tablas():
    """Crea las nuevas tablas con el modelo simplificado"""
    try:
        # Crear engine
        engine = crear_engine_postgresql()
        if not engine:
            print("❌ Error: No se pudo crear el engine de PostgreSQL")
            return False
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Nuevas tablas creadas exitosamente")
        
        # Verificar que las tablas se crearon
        inspector = inspect(engine)
        tablas_creadas = inspector.get_table_names()
        print(f"📋 Tablas disponibles: {tablas_creadas}")
        
        # Mostrar estructura de la tabla conversaciones
        if "conversaciones" in tablas_creadas:
            print("\n🔍 Estructura de la tabla 'conversaciones':")
            columnas = inspector.get_columns("conversaciones")
            for columna in columnas:
                print(f"  - {columna['name']}: {columna['type']} ({'NULL' if columna['nullable'] else 'NOT NULL'})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear nuevas tablas: {e}")
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

def main():
    """Función principal del script"""
    print("🚀 Iniciando limpieza y recreación de base de datos...")
    
    # Verificar Redis
    print("\n📡 Verificando conexión a Redis...")
    verificar_conexion_redis()
    
    # Limpiar base de datos
    print("\n🗑️ Limpiando base de datos existente...")
    if not limpiar_base_datos():
        print("❌ No se pudo limpiar la base de datos")
        return
    
    # Crear nuevas tablas
    print("\n🏗️ Creando nuevas tablas...")
    if not crear_nuevas_tablas():
        print("❌ No se pudieron crear las nuevas tablas")
        return
    
    print("\n🎉 Proceso completado exitosamente!")
    print("\n📝 Resumen de cambios:")
    print("  ✅ Tablas antiguas eliminadas")
    print("  ✅ Nuevas tablas creadas con modelo simplificado")
    print("  ✅ Campo 'flujo' ahora almacena toda la conversación")
    print("  ✅ Campos individuales de mensajes eliminados")
    print("  ✅ Sistema preparado para memoria de chat con Redis")

if __name__ == "__main__":
    main()
