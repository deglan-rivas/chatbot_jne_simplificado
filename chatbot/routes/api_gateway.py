from fastapi import APIRouter, Request
from chatbot.services.intent_validator import validate_intent
from chatbot.services.prompt_enricher import enrich_prompt
from chatbot.services.langgraph_runner import run_langgraph
from chatbot.services.db_logger import log_message

router = APIRouter()

@router.post("/chat")
async def chat_via_api(req: Request):
    body = await req.json()
    incoming_message = body.get("message", "")
    user_id = body.get("user_id", "api_user")
    
    intent = validate_intent(incoming_message)
    enriched_prompt = enrich_prompt(incoming_message, intent)
    response = run_langgraph(enriched_prompt, user_id)

    log_message(user_id, "telefono", "username", incoming_message, response, intent, "api")
    return {"response": response}
