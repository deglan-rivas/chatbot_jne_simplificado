import logging
import os

from fastapi import FastAPI, Request
from chatbot.routes import telegram, api_gateway, whatsapp
from chatbot.database.connection import inicializar_conexiones


def _configure_logging() -> None:
    """Configura logging global basado en la variable LOG_LEVEL."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, force=True)

    # Alinear logs de uvicorn (si se ejecuta con uvicorn/fastapi)
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(level)


_configure_logging()

app = FastAPI(title="Chatbot JNE Simplificado")

# Inicializar conexiones de base de datos al arrancar
@app.on_event("startup")
async def startup_event():
    print("🚀 Inicializando conexiones de base de datos...")
    
    # Inicializar PostgreSQL y Redis
    inicializar_conexiones()
    print("✅ Conexiones PostgreSQL y Redis inicializadas")
    
    # Verificar que Redis esté funcionando
    try:
        from chatbot.database.connection import obtener_cliente_redis
        redis_client = obtener_cliente_redis()
        redis_client.ping()
        print("✅ Redis conectado correctamente")
    except Exception as e:
        print(f"⚠️ Advertencia: Redis no está disponible: {e}")
        print("   El sistema funcionará pero sin memoria de chat")

# Routers
app.include_router(telegram.router, prefix="/webhook/telegram", tags=["Telegram"])
app.include_router(whatsapp.router, prefix="/webhook/whatsapp", tags=["WhatsApp"])
app.include_router(api_gateway.router, prefix="/api", tags=["API Gateway"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
