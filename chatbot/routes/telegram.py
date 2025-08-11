from fastapi import APIRouter, Request
from chatbot.services.intent_validator import validate_intent
from chatbot.services.prompt_enricher import enrich_prompt
from chatbot.services.langgraph_runner import run_langgraph
from chatbot.services.db_logger import log_message

router = APIRouter()

@router.post("")
async def telegram_webhook(req: Request):
    # Aquí debes extraer el mensaje de Telegram y el user_id
    # Enviar "typing..." a Telegram para mejorar UX
    # Rate limiting por usuario
    incoming_message = "mensaje extraído del payload de Telegram"
    user_id = "id_usuario_telegram"
    
    intent = validate_intent(incoming_message)
    enriched_prompt = enrich_prompt(incoming_message, intent)
    response = run_langgraph(enriched_prompt, user_id)

    # Guardar en DB
    log_message(user_id, "telefono", "username", incoming_message, response, intent, "telegram")

    return {"status": "ok"}
