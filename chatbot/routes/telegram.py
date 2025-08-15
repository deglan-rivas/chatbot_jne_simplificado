from fastapi import APIRouter, Request
from chatbot.services.intent_validator import validate_intent
from chatbot.services.prompt_enricher import enrich_prompt
from chatbot.services.langgraph_runner import run_langgraph
from chatbot.services.db_logger import log_message
from chatbot.services.chat_memory_manager import ChatMemoryManager
from chatbot.services.servicios_digitales_manager import ServiciosDigitalesManager
from chatbot.services.informacion_institucional_manager import InformacionInstitucionalManager
from chatbot.services.procesos_electorales_manager import ProcesosElectoralesManager

router = APIRouter()

# Inicializar el gestor de memoria de chat (se creará cuando se necesite)
_chat_memory = None

def get_chat_memory():
    """Obtiene la instancia de ChatMemoryManager, creándola si es necesario"""
    global _chat_memory
    if _chat_memory is None:
        _chat_memory = ChatMemoryManager()
    return _chat_memory

# Inicializar el gestor de servicios digitales (se creará cuando se necesite)
_servicios_manager = None

def get_servicios_manager():
    """Obtiene la instancia de ServiciosDigitalesManager, creándola si es necesario"""
    global _servicios_manager
    if _servicios_manager is None:
        _servicios_manager = ServiciosDigitalesManager()
    return _servicios_manager

# Inicializar el gestor de información institucional (se creará cuando se necesite)
_info_institucional_manager = None

def get_info_institucional_manager():
    """Obtiene la instancia de InformacionInstitucionalManager, creándola si es necesario"""
    global _info_institucional_manager
    if _info_institucional_manager is None:
        _info_institucional_manager = InformacionInstitucionalManager()
    return _info_institucional_manager

# Inicializar el gestor de procesos electorales (se creará cuando se necesite)
_procesos_electorales_manager = None

def get_procesos_electorales_manager():
    """Obtiene la instancia de ProcesosElectoralesManager, creándola si es necesario"""
    global _procesos_electorales_manager
    if _procesos_electorales_manager is None:
        _procesos_electorales_manager = ProcesosElectoralesManager()
    return _procesos_electorales_manager

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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Estado de usuarios en memoria (puedes cambiar a base de datos)
user_states: Dict[int, dict] = {}

# Definición de menús y submenús
menus = {
    "main": {
        "text": "Menú principal:\n1. Procesos Electorales\n2. Organizaciones Políticas\n3. Información Institucional\n4. Servicios Digitales",
        "options": {"1": "procesos_electorales", "2": "organizaciones_politicas", "3": "informacion_institucional", "4": "servicios_digitales"}
    },
    "procesos_electorales": {
        "text": "Procesos electorales:\n1. Cronograma Electoral\n2. Consulta tu Político",
        "options": {"1": "cronograma_electoral", "2": "consulta_politico"}
    },    
    "organizaciones_politicas": {
        "text": "Organizaciones Políticas:\n1. Tipos de Organizaciones Políticas\n2. Consulta de Afiliación",
        "options": {"1": "organizacion_politica", "2": "consulta_afiliacion"}
    },   
    "informacion_institucional": {
        "text": "Información general:\n1. Pleno y Presidencia\n2. Funcionarios\n3. Jurados Electorales Especiales\n4. Sedes",
        "options": {"1": "pleno", "2": "funcionarios", "3": "jee", "4": "sedes"}
    },
    "servicios_digitales": {
        "text": "Servicios Digitales:\n1. Los servicios mas usados por la ciudadanía\n2. Consulta por un trámite específico",
        "options": {"1": "servicios_ciudadano", "2": "tramite"}
    },
    "servicios_ciudadano": {
        "text": "", 
        "options": {}
    }
}

# Contexto adicional según el submenú final
context_map = {
    #"organizacion_politica": "El Partido Aurora Nacional cuenta con presencia en las 25 regiones del país.",
    "cronograma_electoral": "Las elecciones internas se realizarán el 15 de septiembre y la campaña oficial inicia el 1 de octubre.",
    "jee": "Contamos con jurados especiales en las provincias de Cajamarca, Arequipa, Lima y Trujillo.",
    "alianzas_politicas": "Actualmente tenemos alianza con el Movimiento Verde y la Unión Ciudadana.",
    "afiliados": "La organización cuenta con 12,450 afiliados inscritos hasta julio de 2025.",
    "personeros": "Se han acreditado 1,200 personeros para la supervisión de mesas de votación.",
    "candidatos": "Se presentarán 180 candidatos a alcaldías y 25 a gobiernos regionales.",
    "autoridades_electas": "En las últimas elecciones ganamos 5 gobiernos regionales y 40 alcaldías.",
    "servicios_ciudadano": "Existen 15 resoluciones del JNE que han establecido precedentes en materia electoral.",
    "tramite": "La oficina central cuenta con 85 trabajadores administrativos distribuidos en 10 áreas.",
    "pleno": "El pleno del JNE está conformado por 5 miembros titulares y 2 suplentes, todos expertos en derecho electoral y constitucional.",
    "funcionarios": "El JNE cuenta con un equipo de funcionarios especializados distribuidos en diferentes direcciones y oficinas regionales.",
    "sedes": "El JNE tiene presencia en Lima (sede central), Cusco, Nazca y cuenta con un Museo Electoral, además de oficinas desconcentradas en todo el país."
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
    datos = normalizar_input_telegram(body)

    chat_id = datos["chat_id"]
    text = datos["text"]

    # print(f"chat_id: {chat_id}, text: {text}")
    # print(f"user_states: {user_states}")

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
        
        await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
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
            
            # Verificar si es un servicio digital específico
            if chosen_key.startswith("servicio_"):
                # Es un servicio digital seleccionado
                servicio_numero = chosen_key.replace("servicio_", "")
                servicios_manager = get_servicios_manager()
                servicio = servicios_manager.obtener_servicio_principal(servicio_numero)
                if servicio:
                    respuesta = f"📋 **{servicio['nombre']}**\n\n"
                    respuesta += f"📝 **Descripción:** {servicio['descripcion']}\n\n"
                    respuesta += f"🔗 **Enlace:** {servicio['enlace']}\n\n"
                    respuesta += "¿Tienes otra consulta? (responde 'si' o 'no'):"
                    
                    # Agregar respuesta del bot a la conversación
                    chat_memory.agregar_respuesta_bot(
                        user_id=str(chat_id),
                        respuesta=respuesta,
                        menu_actual="servicios_digitales",
                        estado_actual=state.copy()
                    )
                    
                    # Cambiar estado a esperando confirmación de otra consulta
                    state["stage"] = "awaiting_another_question"
                    await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                    return {"reply": respuesta}
                else:
                    respuesta = "Servicio no encontrado. Por favor, elige una opción válida."
                    await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                    return {"reply": respuesta}
            
            # Verificar si es un miembro del pleno
            elif chosen_key.startswith("pleno_"):
                # Es un miembro del pleno seleccionado
                pleno_numero = chosen_key.replace("pleno_", "")
                info_manager = get_info_institucional_manager()
                miembro = info_manager.obtener_miembro_pleno(pleno_numero)
                if miembro:
                    respuesta = f"👨‍⚖️ **{miembro['cargo']}**\n\n"
                    respuesta += f"👤 **Nombre:** {miembro['nombre']}\n\n"
                    respuesta += f"📝 **Descripción:** {miembro['descripcion']}\n\n"
                    respuesta += "¿Tienes otra consulta? (responde 'si' o 'no'):"
                    
                    # Agregar respuesta del bot a la conversación
                    chat_memory.agregar_respuesta_bot(
                        user_id=str(chat_id),
                        respuesta=respuesta,
                        menu_actual="pleno",
                        estado_actual=state.copy()
                    )
                    
                    # Cambiar estado a esperando confirmación de otra consulta
                    state["stage"] = "awaiting_another_question"
                    await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                    return {"reply": respuesta}
                else:
                    respuesta = "Miembro del pleno no encontrado. Por favor, elige una opción válida."
                    await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                    return {"reply": respuesta}
            
            # Verificar si es un servicio de búsqueda semántica
            elif chosen_key.startswith("busqueda_"):
                # Es un servicio encontrado por búsqueda semántica
                busqueda_index = int(chosen_key.replace("busqueda_", ""))
                if hasattr(state, 'servicios_encontrados') and busqueda_index < len(state['servicios_encontrados']):
                    servicio = state['servicios_encontrados'][busqueda_index]
                    respuesta = f"📋 **{servicio['nombre']}**\n\n"
                    respuesta += f"📝 **Descripción:** {servicio['descripcion']}\n\n"
                    respuesta += f"🔗 **Enlace:** {servicio['enlace']}\n\n"
                    respuesta += "¿Tienes otra consulta? (responde 'si' o 'no'):"
                    
                    # Agregar respuesta del bot a la conversación
                    chat_memory.agregar_respuesta_bot(
                        user_id=str(chat_id),
                        respuesta=respuesta,
                        menu_actual="servicios_digitales",
                        estado_actual=state.copy()
                    )
                    
                    # Cambiar estado a esperando confirmación de otra consulta
                    state["stage"] = "awaiting_another_question"
                    await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                    return {"reply": respuesta}
                else:
                    respuesta = "Servicio no encontrado. Por favor, elige una opción válida."
                    await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                    return {"reply": respuesta}
            
            elif chosen_key in menus:  # Es otro menú intermedio
                state["stage"] = chosen_key
                
                # Si es el menú de servicios ciudadano, inicializarlo dinámicamente
                if chosen_key == "servicios_ciudadano":
                    servicios_manager = get_servicios_manager()
                    menus[chosen_key]["text"] = servicios_manager.generar_menu_servicios_digitales()
                    menus[chosen_key]["options"] = servicios_manager.generar_opciones_servicios_digitales()
                
                # Si es el menú del pleno, inicializarlo dinámicamente
                elif chosen_key == "pleno":
                    info_manager = get_info_institucional_manager()
                    menus[chosen_key]["text"] = info_manager.generar_menu_pleno()
                    menus[chosen_key]["options"] = info_manager.generar_opciones_pleno()
                
                respuesta = menus[chosen_key]["text"]
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual=chosen_key,
                    estado_actual=state.copy()
                )
                
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            elif chosen_key == "tramite":  # Opción de búsqueda de trámite específico
                state["stage"] = "awaiting_tramite_query"
                respuesta = "Por favor, describe qué tipo de trámite o servicio estás buscando. Por ejemplo: 'multas electorales', 'afiliación a partidos', 'certificados', etc."
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="servicios_digitales",
                    estado_actual=state.copy()
                )
                
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            elif chosen_key == "funcionarios":  # Opción de funcionarios
                info_manager = get_info_institucional_manager()
                respuesta = info_manager.obtener_info_funcionarios() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="informacion_institucional",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperando confirmación de otra consulta
                state["stage"] = "awaiting_another_question"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            elif chosen_key == "jee":  # Opción de JEE
                info_manager = get_info_institucional_manager()
                respuesta = info_manager.obtener_info_jee() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="informacion_institucional",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperando confirmación de otra consulta
                state["stage"] = "awaiting_another_question"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            elif chosen_key == "sedes":  # Opción de sedes
                info_manager = get_info_institucional_manager()
                respuesta = info_manager.obtener_info_sedes() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="informacion_institucional",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperando confirmación de otra consulta
                state["stage"] = "awaiting_another_question"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            elif chosen_key == "organizacion_politica":  # Opción de tipos de organizaciones políticas
                procesos_manager = get_procesos_electorales_manager()
                respuesta = procesos_manager.obtener_tipos_organizaciones_politicas() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="procesos_electorales",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperando confirmación de otra consulta
                state["stage"] = "awaiting_another_question"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            elif chosen_key == "consulta_afiliacion":  # Opción de consulta de afiliación
                procesos_manager = get_procesos_electorales_manager()
                respuesta = procesos_manager.obtener_consulta_afiliacion() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="procesos_electorales",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperando confirmación de otra consulta
                state["stage"] = "awaiting_another_question"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            elif chosen_key == "cronograma_electoral":  # Opción de cronograma electoral
                procesos_manager = get_procesos_electorales_manager()
                respuesta = procesos_manager.generar_menu_cronograma_electoral()
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="cronograma_electoral",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperar selección de proceso electoral
                state["stage"] = "awaiting_proceso_electoral"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            elif chosen_key == "consulta_politico":  # Opción de consulta de político
                respuesta = "👤 **Consulta tu Político**\n\nPor favor, proporciona el nombre del político que deseas consultar (mínimo 1 nombre y 1 apellido):"
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="consulta_politico",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperar datos del político
                state["stage"] = "awaiting_politico_nombres"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            else:  # Es un submenú final, ahora esperamos la pregunta
                state["stage"] = "awaiting_question"
                state["final_choice"] = chosen_key
                
                # Si es pleno, mostrar menú especial
                if chosen_key == "pleno":
                    info_manager = get_info_institucional_manager()
                    respuesta = info_manager.generar_menu_pleno()
                    
                    # Agregar respuesta del bot a la conversación
                    chat_memory.agregar_respuesta_bot(
                        user_id=str(chat_id),
                        respuesta=respuesta,
                        menu_actual=chosen_key,
                        estado_actual=state.copy()
                    )
                    
                    # Cambiar estado a esperar selección del pleno
                    state["stage"] = "awaiting_pleno_selection"
                    await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                    return {"reply": respuesta}
                else:
                    respuesta = f"Has seleccionado {chosen_key}. Ahora envía tu pregunta:"
                    
                    # Agregar respuesta del bot a la conversación
                    chat_memory.agregar_respuesta_bot(
                        user_id=str(chat_id),
                        respuesta=respuesta,
                        menu_actual=chosen_key,
                        estado_actual=state.copy()
                    )
                    
                    await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
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
            
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
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
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta_completa})
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
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta_error})
            return {"reply": respuesta_error}

    # Si el usuario está consultando por un trámite específico
    if state["stage"] == "awaiting_tramite_query":
        try:
            # Buscar servicios relevantes usando búsqueda semántica
            servicios_manager = get_servicios_manager()
            servicios_encontrados = servicios_manager.buscar_servicios_semanticamente(text, top_k=5)
            
            if servicios_encontrados:
                # Guardar servicios encontrados en el estado
                state["servicios_encontrados"] = servicios_encontrados
                state["stage"] = "awaiting_tramite_selection"
                
                # Generar menú con servicios encontrados
                respuesta = servicios_manager.generar_menu_servicios_busqueda(servicios_encontrados)
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="servicios_digitales",
                    estado_actual=state.copy()
                )
                
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            else:
                respuesta = "No se encontraron servicios relevantes para tu consulta. Por favor, intenta con otros términos o vuelve al menú principal."
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="servicios_digitales",
                    estado_actual=state.copy()
                )
                
                # Reiniciar flujo
                user_states[chat_id] = {"stage": "main", "flow": []}
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
                
        except Exception as e:
            error_msg = f"Error en búsqueda de trámites: {str(e)}"
            respuesta_error = "Lo siento, ha ocurrido un error al buscar trámites. Por favor, intenta de nuevo."
            
            # Agregar respuesta del bot a la conversación
            chat_memory.agregar_respuesta_bot(
                user_id=str(chat_id),
                respuesta=respuesta_error,
                menu_actual="servicios_digitales",
                estado_actual=state.copy()
            )
            
            # Reiniciar flujo
            user_states[chat_id] = {"stage": "main", "flow": []}
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta_error})
            return {"reply": respuesta_error}

    # Si el usuario está seleccionando un trámite de la búsqueda
    if state["stage"] == "awaiting_tramite_selection":
        # Verificar si la opción seleccionada es válida
        if "servicios_encontrados" in state and text.isdigit():
            opcion = int(text)
            servicios_encontrados = state["servicios_encontrados"]
            
            if 1 <= opcion <= len(servicios_encontrados):
                servicio = servicios_encontrados[opcion - 1]
                respuesta = f"📋 **{servicio['nombre']}**\n\n"
                respuesta += f"📝 **Descripción:** {servicio['descripcion']}\n\n"
                respuesta += f"🔗 **Enlace:** {servicio['enlace']}\n\n"
                respuesta += "¿Tienes otra consulta? (responde 'si' o 'no'):"
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="servicios_digitales",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperando confirmación de otra consulta
                state["stage"] = "awaiting_another_question"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            else:
                respuesta = f"Opción no válida. Por favor, elige un número entre 1 y {len(servicios_encontrados)}."
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
        else:
            respuesta = "Por favor, elige una opción válida del menú."
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}

    # Si el usuario está seleccionando un miembro del pleno
    if state["stage"] == "awaiting_pleno_selection":
        # Verificar si la opción seleccionada es válida
        if text.isdigit():
            opcion = int(text)
            info_manager = get_info_institucional_manager()
            pleno_miembros = info_manager.pleno_miembros
            
            if 1 <= opcion <= len(pleno_miembros):
                miembro = pleno_miembros[str(opcion)]
                respuesta = f"👨‍⚖️ **{miembro['cargo']}**\n\n"
                respuesta += f"👤 **Nombre:** {miembro['nombre']}\n\n"
                respuesta += f"📝 **Descripción:** {miembro['descripcion']}\n\n"
                respuesta += "¿Tienes otra consulta? (responde 'si' o 'no'):"
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="pleno",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperando confirmación de otra consulta
                state["stage"] = "awaiting_another_question"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            else:
                respuesta = f"Opción no válida. Por favor, elige un número entre 1 y {len(pleno_miembros)}."
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
        else:
            respuesta = "Por favor, elige una opción válida del menú del pleno."
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}

    # Si el usuario está seleccionando un proceso electoral
    if state["stage"] == "awaiting_proceso_electoral":
        if text.isdigit():
            opcion = int(text)
            procesos_manager = get_procesos_electorales_manager()
            procesos = procesos_manager.obtener_procesos_electorales()
            
            if 1 <= opcion <= len(procesos):
                proceso_seleccionado = procesos[opcion - 1]
                state["proceso_electoral"] = proceso_seleccionado
                state["stage"] = "awaiting_hito_consulta"
                
                respuesta = f"📅 Has seleccionado: **{proceso_seleccionado}**\n\n¿Qué hitos electorales deseas consultar? Por ejemplo: 'elecciones', 'votación', 'inscripción', etc."
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="cronograma_electoral",
                    estado_actual=state.copy()
                )
                
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            else:
                respuesta = f"Opción no válida. Por favor, elige un número entre 1 y {len(procesos)}."
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
        else:
            respuesta = "Por favor, elige una opción válida del menú de procesos electorales."
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}

    # Si el usuario está consultando hitos electorales
    if state["stage"] == "awaiting_hito_consulta":
        try:
            procesos_manager = get_procesos_electorales_manager()
            proceso_electoral = state.get("proceso_electoral")
            
            if not proceso_electoral:
                respuesta = "Error: No se encontró el proceso electoral seleccionado. Por favor, vuelve al menú principal."
                state["stage"] = "main"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            
            # Buscar hitos electorales
            hitos = procesos_manager.buscar_hitos_electorales(proceso_electoral, text)
            
            if hitos:
                state["hitos_encontrados"] = hitos
                state["stage"] = "awaiting_hito_selection"
                
                respuesta = procesos_manager.generar_menu_hitos(hitos)
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="cronograma_electoral",
                    estado_actual=state.copy()
                )
                
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            else:
                respuesta = "No se encontraron hitos electorales que coincidan con tu consulta. Por favor, intenta con otros términos."
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="cronograma_electoral",
                    estado_actual=state.copy()
                )
                
                # Reiniciar flujo
                user_states[chat_id] = {"stage": "main", "flow": []}
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
                
        except Exception as e:
            respuesta = "Error al buscar hitos electorales. Por favor, intenta de nuevo."
            user_states[chat_id] = {"stage": "main", "flow": []}
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}

    # Si el usuario está seleccionando un hito electoral
    if state["stage"] == "awaiting_hito_selection":
        if text.isdigit():
            opcion = int(text)
            hitos = state.get("hitos_encontrados", [])
            
            if 1 <= opcion <= len(hitos):
                hito_seleccionado = hitos[opcion - 1]
                procesos_manager = get_procesos_electorales_manager()
                respuesta = procesos_manager.formatear_hito_electoral(hito_seleccionado)
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="cronograma_electoral",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperando confirmación de otra consulta
                state["stage"] = "awaiting_another_question"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            else:
                respuesta = f"Opción no válida. Por favor, elige un número entre 1 y {len(hitos)}."
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
        else:
            respuesta = "Por favor, elige una opción válida del menú de hitos electorales."
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}

    # Si el usuario está proporcionando nombres del político
    if state["stage"] == "awaiting_politico_nombres":
        # Separar nombres y apellidos
        palabras = text.strip().split()
        
        if len(palabras) < 2:
            respuesta = "Por favor, proporciona al menos un nombre y un apellido del político que deseas consultar."
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}
        
        # Asumir que la primera palabra es nombre y la segunda es apellido
        nombres = palabras[0]
        apellidos = palabras[1] if len(palabras) > 1 else ""
        
        procesos_manager = get_procesos_electorales_manager()
        politicos = procesos_manager.buscar_politicos(nombres, apellidos)
        
        if len(politicos) > 10:
            # Pedir segundo apellido
            state["nombres_politico"] = nombres
            state["primer_apellido"] = apellidos
            state["stage"] = "awaiting_politico_segundo_apellido"
            
            respuesta = f"Se encontraron {len(politicos)} políticos. Por favor, proporciona un segundo apellido para refinar la búsqueda."
            
            # Agregar respuesta del bot a la conversación
            chat_memory.agregar_respuesta_bot(
                user_id=str(chat_id),
                respuesta=respuesta,
                menu_actual="consulta_politico",
                estado_actual=state.copy()
            )
            
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}
        else:
            # Mostrar resultados
            state["politicos_encontrados"] = politicos
            state["stage"] = "awaiting_politico_selection"
            
            respuesta = procesos_manager.generar_menu_politicos(politicos)
            
            # Agregar respuesta del bot a la conversación
            chat_memory.agregar_respuesta_bot(
                user_id=str(chat_id),
                respuesta=respuesta,
                menu_actual="consulta_politico",
                estado_actual=state.copy()
            )
            
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}

    # Si el usuario está proporcionando segundo apellido del político
    if state["stage"] == "awaiting_politico_segundo_apellido":
        nombres = state.get("nombres_politico", "")
        primer_apellido = state.get("primer_apellido", "")
        segundo_apellido = text.strip()
        
        # Combinar apellidos
        apellidos_completos = f"{primer_apellido} {segundo_apellido}".strip()
        
        procesos_manager = get_procesos_electorales_manager()
        politicos = procesos_manager.buscar_politicos(nombres, apellidos_completos)
        
        state["politicos_encontrados"] = politicos
        state["stage"] = "awaiting_politico_selection"
        
        respuesta = procesos_manager.generar_menu_politicos(politicos)
        
        # Agregar respuesta del bot a la conversación
        chat_memory.agregar_respuesta_bot(
            user_id=str(chat_id),
            respuesta=respuesta,
            menu_actual="consulta_politico",
            estado_actual=state.copy()
        )
        
        await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
        return {"reply": respuesta}

    # Si el usuario está seleccionando un político
    if state["stage"] == "awaiting_politico_selection":
        if text.isdigit():
            opcion = int(text)
            politicos = state.get("politicos_encontrados", [])
            
            if 1 <= opcion <= len(politicos):
                politico_seleccionado = politicos[opcion - 1]
                procesos_manager = get_procesos_electorales_manager()
                respuesta = procesos_manager.formatear_politico(politico_seleccionado)
                
                # Agregar respuesta del bot a la conversación
                chat_memory.agregar_respuesta_bot(
                    user_id=str(chat_id),
                    respuesta=respuesta,
                    menu_actual="consulta_politico",
                    estado_actual=state.copy()
                )
                
                # Cambiar estado a esperando confirmación de otra consulta
                state["stage"] = "awaiting_another_question"
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
            else:
                respuesta = f"Opción no válida. Por favor, elige un número entre 1 y {len(politicos)}."
                await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
                return {"reply": respuesta}
        else:
            respuesta = "Por favor, elige una opción válida del menú de políticos."
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}

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
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta})
            return {"reply": respuesta}
            
        elif text_lower in ["no", "n", "0"]:
            # Usuario no quiere más consultas, finalizar sesión
            respuesta_final = "Perfecto, ha sido un placer ayudarte. ¡Hasta luego!"
            
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
            
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta_final})
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
            
            await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta_clarificacion})
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
    
    await enviar_mensaje_telegram({"chat_id": chat_id, "text": respuesta_fallback})
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

# Comando para recargar servicios digitales
@router.post("/recargar-servicios")
async def recargar_servicios_digitales():
    servicios_manager = get_servicios_manager()
    
    # Recargar servicios desde CSV
    servicios_manager.recargar_servicios()
    
    # Actualizar menús dinámicamente
    if "servicios_ciudadano" in menus:
        menus["servicios_ciudadano"]["text"] = servicios_manager.generar_menu_servicios_digitales()
        menus["servicios_ciudadano"]["options"] = servicios_manager.generar_opciones_servicios_digitales()
    
    return {
        "reply": f"Servicios digitales recargados: {servicios_manager.obtener_estadisticas()['servicios_principales']} servicios disponibles",
        "servicios_cargados": servicios_manager.obtener_estadisticas()['servicios_principales']
    }

# Comando para ver servicios digitales disponibles
@router.get("/servicios-disponibles")
async def ver_servicios_disponibles():
    servicios_manager = get_servicios_manager()
    return {
        "total_servicios": servicios_manager.obtener_estadisticas()['servicios_principales'],
        "servicios": servicios_manager.servicios_digitales
    }

# Comando para recargar servicios de búsqueda
@router.post("/recargar-servicios-busqueda")
async def recargar_servicios_busqueda():
    servicios_manager = get_servicios_manager()
    
    # Recargar servicios desde CSV
    servicios_manager.recargar_servicios()
    
    return {
        "reply": f"Servicios de búsqueda recargados: {servicios_manager.obtener_estadisticas()['servicios_busqueda']} servicios disponibles",
        "servicios_cargados": servicios_manager.obtener_estadisticas()['servicios_busqueda']
    }

# Comando para ver servicios de búsqueda disponibles
@router.get("/servicios-busqueda")
async def ver_servicios_busqueda():
    servicios_manager = get_servicios_manager()
    return {
        "total_servicios": servicios_manager.obtener_estadisticas()['servicios_busqueda'],
        "servicios": servicios_manager.servicios_busqueda
    }

# Comando para obtener estadísticas generales de servicios
@router.get("/estadisticas-servicios")
async def obtener_estadisticas_servicios():
    servicios_manager = get_servicios_manager()
    return {
        "estadisticas": servicios_manager.obtener_estadisticas(),
        "servicios_principales": servicios_manager.servicios_digitales,
        "servicios_busqueda": servicios_manager.servicios_busqueda
    }

# Comando para recargar información del pleno
@router.post("/recargar-pleno")
async def recargar_pleno():
    info_manager = get_info_institucional_manager()
    
    # Recargar información del pleno desde CSV
    info_manager.recargar_pleno()
    
    return {
        "reply": f"Información del pleno recargada: {info_manager.obtener_estadisticas()['miembros_pleno']} miembros disponibles",
        "miembros_cargados": info_manager.obtener_estadisticas()['miembros_pleno']
    }

# Comando para ver información del pleno disponible
@router.get("/pleno-disponible")
async def ver_pleno_disponible():
    info_manager = get_info_institucional_manager()
    return {
        "total_miembros": info_manager.obtener_estadisticas()['miembros_pleno'],
        "miembros": info_manager.pleno_miembros
    }

# Comando para obtener estadísticas de información institucional
@router.get("/estadisticas-institucional")
async def obtener_estadisticas_institucional():
    info_manager = get_info_institucional_manager()
    return {
        "estadisticas": info_manager.obtener_estadisticas(),
        "miembros_pleno": info_manager.pleno_miembros
    }

# Comando para obtener estadísticas de procesos electorales
@router.get("/estadisticas-procesos-electorales")
async def obtener_estadisticas_procesos_electorales():
    procesos_manager = get_procesos_electorales_manager()
    return {
        "estadisticas": procesos_manager.obtener_estadisticas()
    }

# Comando para recargar datos de procesos electorales
@router.post("/recargar-procesos-electorales")
async def recargar_procesos_electorales():
    procesos_manager = get_procesos_electorales_manager()
    resultado = procesos_manager.recargar_datos()
    
    return {
        "reply": resultado,
        "timestamp": "2025-01-15T10:00:00Z"
    }

# Comando para obtener reporte de organizaciones políticas
@router.get("/reporte-organizaciones-politicas")
async def obtener_reporte_organizaciones_politicas():
    procesos_manager = get_procesos_electorales_manager()
    reporte = procesos_manager.obtener_tipos_organizaciones_politicas()
    
    return {
        "reporte": reporte,
        "timestamp": "2025-01-15T10:00:00Z"
    }

# Comando para obtener procesos electorales disponibles
@router.get("/procesos-electorales")
async def obtener_procesos_electorales():
    procesos_manager = get_procesos_electorales_manager()
    procesos = procesos_manager.obtener_procesos_electorales()
    
    return {
        "procesos": procesos,
        "total": len(procesos),
        "timestamp": "2025-01-15T10:00:00Z"
    }

# Comando para buscar hitos electorales
@router.post("/buscar-hitos-electorales")
async def buscar_hitos_electorales(req: Request):
    body = await req.json()
    proceso_electoral = body.get("proceso_electoral", "")
    consulta = body.get("consulta", "")
    
    procesos_manager = get_procesos_electorales_manager()
    hitos = procesos_manager.buscar_hitos_electorales(proceso_electoral, consulta)
    
    return {
        "hitos": hitos,
        "total": len(hitos),
        "proceso_electoral": proceso_electoral,
        "consulta": consulta,
        "timestamp": "2025-01-15T10:00:00Z"
    }

# Comando para buscar políticos
@router.post("/buscar-politicos")
async def buscar_politicos(req: Request):
    body = await req.json()
    nombres = body.get("nombres", "")
    apellidos = body.get("apellidos", "")
    
    procesos_manager = get_procesos_electorales_manager()
    politicos = procesos_manager.buscar_politicos(nombres, apellidos)
    
    return {
        "politicos": politicos,
        "total": len(politicos),
        "nombres": nombres,
        "apellidos": apellidos,
        "timestamp": "2025-01-15T10:00:00Z"
    }

# para probar el http de vscode ports con datos móviles de mi celular, con wifi NAZCA o ethernet NAZCAG hay firewall :c con https de vscode ports pide loguearse a github e igual no funca desde cliente xd con http y datos móviles si corre bien pero algo más lento, cuando pase a qa pedirle a infra que le dé un dominio y reemplazarlo en el webhook de telegram
@router.get("/ra")
async def tilin_chatbot_ra(req: Request):
    # await enviar_mensaje_telegram({"chat_id": 1272944550, "text": "Hola desde Python"})
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

async def enviar_mensaje_telegram(datos: dict):
    """
    Envía un mensaje a Telegram usando los datos proporcionados.
    TODO: cambiar diccionario por objeto instanciado de clase TelegramManager 

    Parámetros:
        datos (dict): Debe contener las claves 'chat_id' y 'text'.
    """
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={
                "chat_id": datos["chat_id"],
                "text": datos["text"]
            }
        )

def normalizar_input_telegram(body: dict) -> dict:
    """
    Recibe el body del webhook de Telegram (o de pruebas tipo Postman)
    y devuelve un dict con chat_id y text normalizados.
    """
    # Caso 1: webhook real de Telegram
    if "message" in body and "chat" in body["message"]:
        chat_id = body["message"]["chat"]["id"]
        text = body["message"].get("text", "").strip()
        return {"chat_id": chat_id, "text": text}

    # Caso 2: input directo desde Postman o Insomnia (formato anterior)
    if "chat_id" in body and "text" in body:
        return {
            "chat_id": body.get("chat_id", 0),
            "text": body.get("text", "").strip()
        }

    # Si no coincide con ninguno
    return {"chat_id": 0, "text": ""}