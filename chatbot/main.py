from fastapi import FastAPI, Request
from chatbot.routes import telegram, api_gateway
from chatbot.database.connection import inicializar_conexiones

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
app.include_router(api_gateway.router, prefix="/api", tags=["API Gateway"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
