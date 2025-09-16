from fastapi import APIRouter, Request, Response
import os
from datetime import datetime

router = APIRouter()

WSSP_VERIFY_TOKEN = os.getenv("WSSP_VERIFY_TOKEN")

@router.get("")
async def verify_webhook(request: Request):
    """
    Verificación del webhook (GET)
    """
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge")
    token = params.get("hub.verify_token")

    if mode == "subscribe" and token == WSSP_VERIFY_TOKEN:
        print("WEBHOOK VERIFIED")
        return Response(content=challenge, status_code=200)
    else:
        return Response(status_code=403)

@router.post("")
async def receive_webhook(request: Request):
    """
    Recepción de eventos (POST)
    """
    body = await request.json()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n\nWebhook received {timestamp}\n")
    print(body)
    return Response(status_code=200)