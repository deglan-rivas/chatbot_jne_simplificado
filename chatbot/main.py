from fastapi import FastAPI, Request
from chatbot.routes import telegram, api_gateway

app = FastAPI(title="Chatbot JNE Simplificado")

# print("running")

# Routers
app.include_router(telegram.router, prefix="/webhook/telegram", tags=["Telegram"])
app.include_router(api_gateway.router, prefix="/api", tags=["API Gateway"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
