from fastapi import FastAPI, Request
from chatbot.routes import telegram, api_gateway, whatsapp, web_chat
from chatbot.database.connection import inicializar_conexiones
from chatbot.database.auto_init import inicializar_bases_de_datos
from chatbot.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatbot JNE Simplificado")

# Inicializar conexiones de base de datos al arrancar
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Inicializando conexiones de base de datos...")
    
    # Inicializar PostgreSQL y Redis
    inicializar_conexiones()
    logger.info("✅ Conexiones PostgreSQL y Redis inicializadas")
    
    # Inicializar tablas automáticamente si no existen
    inicializar_bases_de_datos()

# Routers
app.include_router(telegram.router, prefix="/webhook/telegram", tags=["Telegram"])
app.include_router(whatsapp.router, prefix="/webhook/whatsapp", tags=["WhatsApp"])
app.include_router(api_gateway.router, prefix="/api", tags=["API Gateway"])
app.include_router(web_chat.router, prefix="/api/web/chat", tags=["Web Chat"])

@app.get("/health")
async def health_check():
    """Health check básico"""
    return {"status": "ok"}

@app.get("/health/oracle")
async def health_check_oracle():
    """Health check de conexión Oracle"""
    try:
        from chatbot.database.oracle_connection import motor
        from sqlalchemy import text
        
        with motor.connect() as conn:
            result = conn.execute(text("SELECT SYSDATE FROM DUAL"))
            fecha = result.fetchone()[0]
            
        return {
            "status": "ok",
            "oracle": {
                "connected": True,
                "server_date": str(fecha),
                "dsn": settings.ORACLE_DSN,
                "user": settings.ORACLE_USER
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "oracle": {
                "connected": False,
                "error": str(e),
                "dsn": settings.ORACLE_DSN,
                "user": settings.ORACLE_USER
            }
        }
