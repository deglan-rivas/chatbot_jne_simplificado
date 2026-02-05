#!/usr/bin/env python3
"""
Script para probar la conexión a Oracle desde el contenedor Docker
Ejecutar: docker exec chatbot_app python /app/test_oracle_connection.py
"""
import os
import sys
import oracledb
from chatbot.config import settings

def test_oracle_connection():
    """Prueba la conexión a Oracle"""
    print("=" * 60)
    print("🔍 Verificando Configuración de Oracle")
    print("=" * 60)
    
    # Mostrar configuración
    print(f"\n📋 Variables de Entorno:")
    print(f"   ORACLE_USER: {settings.ORACLE_USER}")
    print(f"   ORACLE_PASS: {'*' * len(settings.ORACLE_PASS) if settings.ORACLE_PASS else 'NO DEFINIDO'}")
    print(f"   ORACLE_DSN: {settings.ORACLE_DSN}")
    print(f"   TNS_ADMIN: {settings.TNS_ADMIN}")
    print(f"   ORACLEDB_CLIENT_PATH: {settings.ORACLEDB_CLIENT_PATH}")
    print(f"   LD_LIBRARY_PATH: {os.getenv('LD_LIBRARY_PATH', 'NO DEFINIDO')}")
    
    # Verificar si el cliente Oracle está disponible
    print(f"\n🔧 Verificando Cliente Oracle:")
    try:
        client_path = settings.ORACLEDB_CLIENT_PATH
        if os.path.exists(client_path):
            print(f"   ✅ Cliente Oracle encontrado en: {client_path}")
            
            # Listar archivos principales
            libclntsh = os.path.join(client_path, "libclntsh.so")
            if os.path.exists(libclntsh):
                print(f"   ✅ libclntsh.so encontrado")
            else:
                print(f"   ⚠️  libclntsh.so NO encontrado en {client_path}")
        else:
            print(f"   ❌ Cliente Oracle NO encontrado en: {client_path}")
    except Exception as e:
        print(f"   ❌ Error verificando cliente: {e}")
    
    # Intentar inicializar el cliente Oracle
    print(f"\n🔌 Inicializando Cliente Oracle:")
    try:
        # En Docker/Linux, usar lib_dir
        if os.path.exists("/.dockerenv") or os.path.exists("/proc/self/cgroup"):
            print(f"   Detectado entorno Docker/Linux")
            if os.path.exists(settings.ORACLEDB_CLIENT_PATH):
                oracledb.init_oracle_client(lib_dir=settings.ORACLEDB_CLIENT_PATH)
                print(f"   ✅ Cliente Oracle inicializado (modo Linux)")
            else:
                print(f"   ⚠️  Intentando inicialización sin lib_dir...")
                oracledb.init_oracle_client()
                print(f"   ✅ Cliente Oracle inicializado (modo automático)")
        else:
            print(f"   Detectado entorno Windows")
            oracledb.init_oracle_client()
            print(f"   ✅ Cliente Oracle inicializado (modo Windows)")
    except Exception as e:
        print(f"   ❌ Error inicializando cliente Oracle: {e}")
        print(f"   Detalles: {type(e).__name__}")
        return False
    
    # Intentar conectar
    print(f"\n🌐 Intentando Conectar a Oracle:")
    print(f"   DSN: {settings.ORACLE_DSN}")
    print(f"   User: {settings.ORACLE_USER}")
    
    try:
        connection = oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASS,
            dsn=settings.ORACLE_DSN
        )
        
        print(f"   ✅ ¡Conexión exitosa!")
        
        # Ejecutar una consulta simple
        print(f"\n📊 Ejecutando Consulta de Prueba:")
        cursor = connection.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        print(f"   ✅ Fecha del servidor Oracle: {result[0]}")
        
        # Obtener versión de Oracle
        cursor.execute("SELECT * FROM V$VERSION WHERE BANNER LIKE 'Oracle%'")
        version = cursor.fetchone()
        if version:
            print(f"   ✅ Versión Oracle: {version[0]}")
        
        # Cerrar conexión
        cursor.close()
        connection.close()
        print(f"\n✅ Prueba completada exitosamente!")
        return True
        
    except oracledb.Error as e:
        error, = e.args
        print(f"   ❌ Error de conexión Oracle:")
        print(f"   Código: {error.code}")
        print(f"   Mensaje: {error.message}")
        print(f"\n💡 Posibles causas:")
        print(f"   1. El servidor Oracle no es accesible desde el contenedor")
        print(f"   2. Credenciales incorrectas")
        print(f"   3. El DSN está mal formado")
        print(f"   4. Problemas de red/firewall")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        print(f"   Tipo: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_oracle_connection()
    sys.exit(0 if success else 1)
