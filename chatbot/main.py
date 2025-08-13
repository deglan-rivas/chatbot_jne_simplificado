from fastapi import FastAPI, Request
from chatbot.routes import telegram, api_gateway
from chatbot.database.connection import inicializar_conexiones

app = FastAPI(title="Chatbot JNE Simplificado")

# Inicializar conexiones de base de datos al arrancar
@app.on_event("startup")
async def startup_event():
    print("🚀 Inicializando conexiones de base de datos...")
    inicializar_conexiones()
    print("✅ Conexiones inicializadas")

# Routers
app.include_router(telegram.router, prefix="/webhook/telegram", tags=["Telegram"])
app.include_router(api_gateway.router, prefix="/api", tags=["API Gateway"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
