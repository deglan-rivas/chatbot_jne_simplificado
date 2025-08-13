from fastapi import APIRouter, Request
from chatbot.services.intent_validator import validate_intent
from chatbot.services.prompt_enricher import enrich_prompt
from chatbot.services.langgraph_runner import run_langgraph
from chatbot.services.db_logger import log_message
from chatbot.services.chat_memory_manager import ChatMemoryManager

router = APIRouter()

# Inicializar el gestor de memoria de chat (se creará cuando se necesite)
_chat_memory = None

def get_chat_memory():
    """Obtiene la instancia de ChatMemoryManager, creándola si es necesario"""
    global _chat_memory
    if _chat_memory is None:
        _chat_memory = ChatMemoryManager()
    return _chat_memory

import os
import httpx

from dotenv import load_dotenv
from typing import Dict
# from openai import OpenAI
from google import genai
from google.genai import types

load_dotenv()

# Cliente LLM (usa OpenAI, pero puedes cambiar a cualquier API)
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = genai.Client()

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}"

# Estado de usuarios en memoria (puedes cambiar a base de datos)
user_states: Dict[int, dict] = {}

# Definición de menús y submenús
menus = {
    "main": {
        "text": "Menú principal:\n1. Procesos Electorales\n2. Información Institucional\n3. Servicios Digitales",
        "options": {"1": "procesos_electorales", "2": "informacion_institucional", "3": "servicios_digitales"}
    },
    "procesos_electorales": {
        "text": "Procesos electorales:\n1. Organización Política\n2. Cronograma Electoral\n3. Jurado Especial Electoral\n4. Alianzas Políticas\n5. Afiliados\n6. Personeros\n7. Candidatos\n8. Autoridades Electas",
        "options": {"1": "organizacion_politica", "2": "cronograma_electoral", "3": "jee", "4": "alianzas_politicas", "5": "afiliados", "6": "personeros", "7": "candidatos", "8": "autoridades_electas"}
    },    
    "informacion_institucional": {
        "text": "Información general:\n1. Pleno\n2. Sedes\n3. Organigrama\n4. Funcionarios\n5. ODE",
        "options": {"1": "pleno", "2": "sedes", "3": "organigrama", "4": "funcionarios", "5": "ode"}
    },
    "servicios_digitales": {
        "text": "Sistemas informáticos:\n1. Jurisprudencia\n2. Administrativos",
        "options": {"1": "jurisprudencia", "2": "administrativos"}
    },
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

    # usando OpenAI
    # response = client.chat.completions.create(
    #     model="gpt-5-nano",
    #     # model="gpt-5",
    #     # model="gpt-4o-mini",
    #     messages=[{"role": "system", "content": "Eres un asistente experto en el tema indicado. Responde brevemente en menos de 60 palabras"},
    #               {"role": "user", "content": prompt}]
    # )
    # return response.choices[0].message.content

    # usando Gemini
    response = client.models.generate_content(
        # model="gemini-2.5-flash",
        # model="gemini-2.5-flash-lite",
        model="gemma-3-27b-it",
        contents=prompt,
        # config=types.GenerateContentConfig(
        #     thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
        # ),
    )
    print(f"respuesta: {response.text}")
    return response.text

@router.post("")
async def tilin_chatbot(req: Request):
    body = await req.json()
    chat_id = body.get("chat_id", 0)  # Si usas Telegram, este será el ID del usuario
    text = body.get("text", "").strip()
    print(f"chat_id: {chat_id}, text: {text}")
    print(f"user_states: {user_states}")

    # Obtener instancia de ChatMemoryManager
    chat_memory = get_chat_memory()

    # Verificar si el usuario tiene una conversación activa
    conversacion_activa = chat_memory.obtener_conversacion_activa(str(chat_id))
    
    # Si no hay conversación activa o no existe estado del usuario, iniciar una nueva
    if not conversacion_activa or chat_id not in user_states:
        # Inicializar estado del usuario
        user_states[chat_id] = {"stage": "main", "flow": []}
        
        # Iniciar conversación en Redis si no existe
        if not conversacion_activa:
            chat_memory.iniciar_conversacion(str(chat_id))
        
        respuesta = menus["main"]["text"]
        
        # Agregar respuesta del bot a la conversación
        chat_memory.agregar_respuesta_bot(
            user_id=str(chat_id),
            respuesta=respuesta,
            menu_actual="main",
            estado_actual={"stage": "main", "flow": []}
        )
        
        return {"reply": respuesta}

    # Obtener el estado actual del usuario
    state = user_states[chat_id]
    print(f"state: {state} para chat_id: {chat_id}")

    # Agregar mensaje del usuario a la conversación
    chat_memory.agregar_mensaje_usuario(
        user_id=str(chat_id),
        mensaje=text,
        intent="navegacion_menu" if state["stage"] in menus else "consulta_informacion"
    )

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
                respuesta = menus[chosen_key]["text"]
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual=chosen_key,
                    estado_actual=state.copy()
                )
                
                return {"reply": respuesta}
            else:  # Es un submenú final, ahora esperamos la pregunta
                state["stage"] = "awaiting_question"
                state["final_choice"] = chosen_key
                respuesta = f"Has seleccionado {chosen_key}. Ahora envía tu pregunta:"
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual=chosen_key,
                    estado_actual=state.copy()
                )
                
                return {"reply": respuesta}
        else:
            respuesta = f"Opción no válida. {menus[state['stage']]['text']}"
            
            # Agregar respuesta del bot a la conversación
            chat_memory.agregar_respuesta_bot(
                user_id=str(chat_id),
                respuesta=respuesta,
                menu_actual=state["stage"],
                estado_actual=state.copy()
            )
            
            return {"reply": respuesta}

    # Si el usuario ya eligió submenú y está enviando pregunta
    if state["stage"] == "awaiting_question":
        try:
            context = context_map.get(state["final_choice"], "")
            llm_reply = send_to_llm(text, context)
            respuesta_completa = llm_reply + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
            
            # Agregar respuesta del bot a la conversación
            chat_memory.agregar_respuesta_bot(
                user_id=str(chat_id),
                respuesta=respuesta_completa,
                menu_actual=state["final_choice"],
                estado_actual=state.copy()
            )
            
            # Cambiar estado a esperando confirmación de otra consulta
            state["stage"] = "awaiting_another_question"
            return {"reply": respuesta_completa}
            
        except Exception as e:
            error_msg = f"Error al procesar la pregunta: {str(e)}"
            respuesta_error = "Lo siento, ha ocurrido un error al procesar tu pregunta. Por favor, intenta de nuevo."
            
            # Agregar respuesta del bot a la conversación
            chat_memory.agregar_respuesta_bot(
                user_id=str(chat_id),
                respuesta=respuesta_error,
                menu_actual=state["final_choice"],
                estado_actual=state.copy()
            )
            
            # Reiniciar flujo
            user_states[chat_id] = {"stage": "main", "flow": []}
            return {"reply": respuesta_error}

    # Si el usuario está confirmando si tiene otra consulta
    if state["stage"] == "awaiting_another_question":
        text_lower = text.lower().strip()
        
        if text_lower in ["si", "sí", "yes", "y", "1"]:
            # Usuario quiere hacer otra consulta, volver al menú principal
            respuesta = "Perfecto, volvamos al menú principal:\n\n" + menus["main"]["text"]
            
            # Agregar respuesta del bot a la conversación
            chat_memory.agregar_respuesta_bot(
                user_id=str(chat_id),
                respuesta=respuesta,
                menu_actual="main",
                estado_actual={"stage": "main", "flow": []}
            )
            
            # Reiniciar flujo
            user_states[chat_id] = {"stage": "main", "flow": []}
            return {"reply": respuesta}
            
        elif text_lower in ["no", "n", "0"]:
            # Usuario no quiere más consultas, finalizar sesión
            respuesta_final = "Perfecto, ha sido un placer ayudarte. Tu conversación ha sido guardada. ¡Hasta luego!"
            
            # Agregar respuesta final del bot
            chat_memory.agregar_respuesta_bot(
                user_id=str(chat_id),
                respuesta=respuesta_final,
                menu_actual="finalizacion",
                estado_actual=state.copy()
            )
            
            # Finalizar conversación y guardar en PostgreSQL
            chat_memory.finalizar_conversacion(
                user_id=str(chat_id),
                motivo="Usuario confirmó que no tiene más consultas"
            )
            
            # Limpiar estado del usuario
            if chat_id in user_states:
                del user_states[chat_id]
            
            return {"reply": respuesta_final}
            
        else:
            # Respuesta no reconocida, pedir clarificación
            respuesta_clarificacion = "Por favor, responde 'si' o 'no' si tienes otra consulta:"
            
            # Agregar respuesta del bot a la conversación
            chat_memory.agregar_respuesta_bot(
                user_id=str(chat_id),
                respuesta=respuesta_clarificacion,
                menu_actual=state["final_choice"],
                estado_actual=state.copy()
            )
            
            return {"reply": respuesta_clarificacion}

    # Si todo falla, reiniciar
    user_states[chat_id] = {"stage": "main", "flow": []}
    respuesta_fallback = menus["main"]["text"]
    
    # Agregar respuesta del bot a la conversación
    chat_memory.agregar_respuesta_bot(
        user_id=str(chat_id),
        respuesta=respuesta_fallback,
        menu_actual="main",
        estado_actual={"stage": "main", "flow": []}
    )
    
    return {"reply": respuesta_fallback}

# Comando para finalizar conversación manualmente
@router.post("/finalizar")
async def finalizar_conversacion(req: Request):
    body = await req.json()
    chat_id = body.get("chat_id", 0)
    
    # Obtener instancia de ChatMemoryManager
    chat_memory = get_chat_memory()
    
    # Finalizar conversación y guardar en PostgreSQL
    success = chat_memory.finalizar_conversacion(
        user_id=str(chat_id),
        motivo="Usuario finalizó conversación manualmente"
    )
    
    # Limpiar estado del usuario
    if chat_id in user_states:
        del user_states[chat_id]
    
    if success:
        return {"reply": "Conversación finalizada correctamente y guardada en la base de datos"}
    else:
        return {"reply": "No se pudo finalizar la conversación"}

# Comando para finalizar conversación con texto específico
@router.post("/finalizar-texto")
async def finalizar_conversacion_texto(req: Request):
    body = await req.json()
    chat_id = body.get("chat_id", 0)
    texto_final = body.get("texto", "Conversación finalizada por comando")
    
    # Obtener instancia de ChatMemoryManager
    chat_memory = get_chat_memory()
    
    # Finalizar conversación y guardar en PostgreSQL
    success = chat_memory.finalizar_conversacion(
        user_id=str(chat_id),
        motivo=texto_final
    )
    
    # Limpiar estado del usuario
    if chat_id in user_states:
        del user_states[chat_id]
    
    if success:
        return {"reply": f"Conversación finalizada: {texto_final}"}
    else:
        return {"reply": "No se pudo finalizar la conversación"}

# Comando para verificar conversaciones expiradas
@router.get("/verificar-expiracion")
async def verificar_expiracion():
    # Obtener instancia de ChatMemoryManager
    chat_memory = get_chat_memory()
    
    usuarios_expirados = chat_memory.verificar_expiracion_conversaciones()
    return {"usuarios_expirados": usuarios_expirados, "total": len(usuarios_expirados)}

# Comando para reiniciar estado de un usuario (útil para debugging)
@router.post("/reiniciar-estado")
async def reiniciar_estado_usuario(req: Request):
    body = await req.json()
    chat_id = body.get("chat_id", 0)
    
    # Reiniciar estado en memoria
    if chat_id in user_states:
        del user_states[chat_id]
    
    # Obtener instancia de ChatMemoryManager
    chat_memory = get_chat_memory()
    
    # Finalizar conversación activa si existe
    if chat_memory.obtener_conversacion_activa(str(chat_id)):
        chat_memory.finalizar_conversacion(
            user_id=str(chat_id),
            motivo="Estado reiniciado manualmente"
        )
    
    return {"reply": f"Estado reiniciado para usuario {chat_id}"}

# Comando para ver estado actual de un usuario
@router.get("/estado-usuario/{chat_id}")
async def ver_estado_usuario(chat_id: int):
    estado_memoria = user_states.get(chat_id, "No existe")
    
    # Obtener instancia de ChatMemoryManager
    chat_memory = get_chat_memory()
    
    conversacion_redis = chat_memory.obtener_conversacion_activa(str(chat_id))
    
    return {
        "chat_id": chat_id,
        "estado_memoria": estado_memoria,
        "conversacion_redis": conversacion_redis is not None,
        "conversacion_detalle": conversacion_redis
    }

# para probar el http de vscode ports con datos móviles de mi celular, con wifi NAZCA o ethernet NAZCAG hay firewall :c con https de vscode ports pide loguearse a github e igual no funca desde cliente xd con http y datos móviles si corre bien pero algo más lento, cuando pase a qa pedirle a infra que le dé un dominio y reemplazarlo en el webhook de telegram
@router.get("/ra")
async def tilin_chatbot_ra(req: Request):
    models = client.models.list()
    # model_names = []
    
    # Itera sobre el objeto Pager para obtener cada modelo
    for m in models:
        # Aquí puedes acceder a las propiedades de cada modelo, como el nombre
        # if 'generateContent' in m.supported_generation_methods:
        #     model_names.append(m.name)
        print(m.name)
            
    # print(f"Models: {model_names}")
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
        user_info = data["message"]["from"]
        
        # Extraer información del usuario
        user_id = str(user_info.get("id", ""))
        username = user_info.get("username", "")
        first_name = user_info.get("first_name", "")
        last_name = user_info.get("last_name", "")

        # Obtener instancia de ChatMemoryManager
        chat_memory = get_chat_memory()

        # Verificar si el usuario tiene una conversación activa
        conversacion_activa = chat_memory.obtener_conversacion_activa(user_id)
        
        # Si no hay conversación activa, iniciar una nueva
        if not conversacion_activa:
            chat_memory.iniciar_conversacion(
                user_id=user_id,
                numero_telefono=None,  # Telegram no proporciona número de teléfono por defecto
                usuario=username
            )

        # Agregar mensaje del usuario
        chat_memory.agregar_mensaje_usuario(user_id, text)

        # Responder al usuario
        async with httpx.AsyncClient() as client:
            await client.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"Recibí tu mensaje: {text}"
            })
        
        # Agregar respuesta del bot
        chat_memory.agregar_respuesta_bot(
            user_id=user_id,
            respuesta=f"Recibí tu mensaje: {text}"
        )

    return {"ok": True}