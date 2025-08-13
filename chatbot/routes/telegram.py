from fastapi import APIRouter, Request
from chatbot.services.intent_validator import validate_intent
from chatbot.services.prompt_enricher import enrich_prompt
from chatbot.services.langgraph_runner import run_langgraph
from chatbot.services.db_logger import log_message

router = APIRouter()

@router.post("/x")
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

import os
import httpx

from dotenv import load_dotenv
from typing import Dict
from openai import OpenAI

load_dotenv()

# Cliente LLM (usa OpenAI, pero puedes cambiar a cualquier API)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}"

# Estado de usuarios en memoria (puedes cambiar a base de datos)
user_states: Dict[int, dict] = {}

# Definición de menús y submenús
menus = {
    "main": {
        "text": "Menú principal:\n1. procesos_electorales\n2. sistemas_informaticos\n3. consulta_jne",
        "options": {"1": "procesos_electorales", "2": "sistemas_informaticos", "3": "consulta_jne"}
    },
    "procesos_electorales": {
        "text": "Procesos electorales:\n1. Organización Política\n2. Cronograma Electoral\n3. Jurado Especial Electoral\n4. Alianzas Políticas\n5. Afiliados\n6. Personeros\n7. Candidatos\n8. Autoridades Electas",
        "options": {"1": "organizacion_politica", "2": "cronograma_electoral", "3": "jee", "4": "alianzas_politicas", "5": "afiliados", "6": "personeros", "7": "candidatos", "8": "autoridades_electas"}
    },
    "sistemas_informaticos": {
        "text": "Sistemas informáticos:\n1. Jurisprudencia\n2. Administrativos",
        "options": {"1": "jurisprudencia", "2": "administrativos"}
    },
    "consulta_jne": {
        "text": "Información general:\n1. Pleno\n2. Sedes\n3. Organigrama\n4. Funcionarios\n1. ODE",
        "options": {"1": "pleno", "2": "sedes", "3": "organigrama", "4": "funcionarios", "5": "ode"}
    }
}

# Contexto adicional según el submenú final
context_map = {
    "organizacion_politica": "El Partido Aurora Nacional cuenta con presencia en las 25 regiones del país.",
    "cronograma_electoral": "Las elecciones internas se realizarán el 15 de septiembre y la campaña oficial inicia el 1 de octubre.",
    "jee": "Contamos con jurados especiales en las provincias de Cajamarca, Arequipa, Lima y Trujillo.",
    "alianzas_politicas": "Actualmente tenemos alianza con el Movimiento Verde y la Unión Ciudadana.",
    "afiliados": "La organización cuenta con 12,450 afiliados inscritos hasta julio de 2025.",
    "personeros": "Se han acreditado 1,200 personeros para la supervisión de mesas de votación.",
    "candidatos": "Se presentarán 180 candidatos a alcaldías y 25 a gobiernos regionales.",
    "autoridades_electas": "En las últimas elecciones ganamos 5 gobiernos regionales y 40 alcaldías.",
    "jurisprudencia": "Existen 15 resoluciones del JNE que han establecido precedentes en materia electoral.",
    "administrativos": "La oficina central cuenta con 85 trabajadores administrativos distribuidos en 10 áreas.",
    "pleno": "El pleno está conformado por 5 miembros titulares y 2 suplentes.",
    "sedes": "Tenemos sedes en Lima, Cusco, Piura y Chiclayo.",
    "organigrama": "La estructura incluye presidencia, secretaría general, direcciones técnicas y oficinas regionales.",
    "funcionarios": "Entre nuestros funcionarios destacan la presidenta, el secretario general y 8 directores regionales.",
    "ode": "Las Oficinas Descentralizadas de Elecciones operan en 45 provincias del país."
}


def send_to_llm(user_input: str, extra_context: str) -> str:
    """Envía la pregunta al LLM con contexto adicional."""
    prompt = f"{extra_context}\n\nPregunta del usuario: {user_input}"
    response = client.chat.completions.create(
        model="gpt-5-nano",
        # model="gpt-5",
        # model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Eres un asistente experto en el tema indicado. Responde brevemente en menos de 60 palabras"},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


@router.post("")
async def tilin_chatbot(req: Request):
    body = await req.json()
    chat_id = body.get("chat_id", 0)  # Si usas Telegram, este será el ID del usuario
    text = body.get("text", "").strip()
    print(f"chat_id: {chat_id}, text: {text}")
    print(f"user_states: {user_states}")

    # Inicializar estado de usuario
    if chat_id not in user_states:
        user_states[chat_id] = {"stage": "main", "flow": []}
        return {"reply": menus["main"]["text"]}

    state = user_states[chat_id]
    print(f"state: {state} para chat_id: {chat_id}")

    # Si el usuario está en un menú
    if state["stage"] in menus:
        options = menus[state["stage"]]["options"]
        print(f"options: {options}")
        if text in options:
            chosen_key = options[text]
            print(f"chosen_key: {chosen_key}")
            state["flow"].append(chosen_key)
            if chosen_key in menus:  # Es otro menú intermedio
                state["stage"] = chosen_key
                return {"reply": menus[chosen_key]["text"]}
            else:  # Es un submenú final, ahora esperamos la pregunta
                state["stage"] = "awaiting_question"
                state["final_choice"] = chosen_key
                return {"reply": f"Has seleccionado {chosen_key}. Ahora envía tu pregunta:"}
        else:
            return {"reply": f"Opción no válida. {menus[state['stage']]['text']}"}

    # Si el usuario ya eligió submenú y está enviando pregunta
    if state["stage"] == "awaiting_question":
        context = context_map.get(state["final_choice"], "")
        llm_reply = send_to_llm(text, context)
        # Reiniciar flujo
        user_states[chat_id] = {"stage": "main", "flow": []}
        return {"reply": llm_reply + "\n\n" + menus["main"]["text"]}

    # Si todo falla, reiniciar
    user_states[chat_id] = {"stage": "main", "flow": []}
    return {"reply": menus["main"]["text"]}

# para probar el http de vscode ports con datos móviles de mi celular, con wifi NAZCA o ethernet NAZCAG hay firewall :c con https de vscode ports pide loguearse a github e igual no funca desde cliente xd con http y datos móviles si corre bien pero algo más lento, cuando pase a qa pedirle a infra que le dé un dominio y reemplazarlo en el webhook de telegram
@router.get("/ra")
async def tilin_chatbot_ra(req: Request):
    return {"reply": "raaa"}

@router.post("/jne")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("Mensaje recibido:", data)
    # Mensaje recibido: {'update_id': 23831431, 'message': {'message_id': 804, 'from': {'id': 1272944550, 'is_bot': False, 'first_name': 'Jesus', 'last_name': 'R', 'username': 'TitisTilin', 'language_code': 'en'}, 'chat': {'id': 1272944550, 'first_name': 'Jesus', 'last_name': 'R', 'username': 'TitisTilin', 'type': 'private'}, 'date': 1755102670, 'text': 'hola'}}

    # Si hay texto en el mensaje
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        # Responder al usuario
        async with httpx.AsyncClient() as client:
            await client.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"Recibí tu mensaje: {text}"
            })

    return {"ok": True}