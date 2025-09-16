import os
import httpx
from typing import Dict

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

def normalizar_input_telegram(body: dict) -> dict:
    """Normaliza el input de Telegram"""
    if "message" in body and "chat" in body["message"]:
        chat_id = body["message"]["chat"]["id"]
        text = body["message"].get("text", "").strip()
        return {"chat_id": chat_id, "text": text}
    
    if "chat_id" in body and "text" in body:
        return {
            "chat_id": body.get("chat_id", 0),
            "text": body.get("text", "").strip()
        }
    
    return {"chat_id": 0, "text": ""}

def normalizar_input_whatsapp(body: dict) -> dict:
    """Normaliza el input de WhatsApp"""
    try:
        # Estructura típica de webhook de WhatsApp Business API
        if "entry" in body and len(body["entry"]) > 0:
            entry = body["entry"][0]
            if "changes" in entry and len(entry["changes"]) > 0:
                change = entry["changes"][0]
                if "value" in change and "messages" in change["value"]:
                    messages = change["value"]["messages"]
                    if len(messages) > 0:
                        message = messages[0]
                        chat_id = message.get("from", "")
                        
                        # Solo procesar mensajes de texto
                        if message.get("type") == "text":
                            text = message.get("text", {}).get("body", "").strip()
                            return {"chat_id": chat_id, "text": text}
                        else:
                            # Fallback para otros tipos de mensaje
                            return {
                                "chat_id": chat_id, 
                                "text": "Lo siento, solo puedo procesar mensajes de texto por el momento."
                            }
        
        # Fallback para estructura directa (testing)
        if "chat_id" in body and "text" in body:
            return {
                "chat_id": body.get("chat_id", ""),
                "text": body.get("text", "").strip()
            }
            
    except Exception as e:
        print(f"Error normalizando input de WhatsApp: {e}")
    
    return {"chat_id": "", "text": ""}

async def enviar_mensaje_telegram(datos: dict):
    """Envía un mensaje a Telegram"""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={
                "chat_id": datos["chat_id"],
                "text": datos["text"]
            }
        )

async def enviar_mensaje_whatsapp(datos: dict):
    """Envía un mensaje a WhatsApp"""
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print("⚠️ WhatsApp credentials not configured")
        return
    
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": datos["chat_id"],
        "type": "text",
        "text": {
            "body": datos["text"]
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                print(f"Error enviando mensaje WhatsApp: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error enviando mensaje WhatsApp: {e}")