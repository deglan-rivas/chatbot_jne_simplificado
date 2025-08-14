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
import csv
from pathlib import Path

from dotenv import load_dotenv
from typing import Dict, List
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

# Cargar servicios digitales desde CSV
def cargar_servicios_digitales() -> Dict[str, dict]:
    """Carga los servicios digitales desde el archivo CSV"""
    servicios = {}
    csv_path = Path("./RAG/PRINCIPALES.csv")
    
    try:
        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')
                for i, row in enumerate(reader, 1):
                    servicios[str(i)] = {
                        "nombre": row.get('TXNOMBRE', ''),
                        "descripcion": row.get('TXDESCRIPCIONCORTA', ''),
                        "enlace": row.get('TXENLACE', '')
                    }
            print(f"Servicios digitales cargados: {len(servicios)} servicios")
        else:
            print(f"Archivo CSV no encontrado en: {csv_path}")
    except Exception as e:
        print(f"Error al cargar servicios digitales: {e}")
    
    return servicios

# Cargar servicios para búsqueda semántica
def cargar_servicios_busqueda() -> List[dict]:
    """Carga todos los servicios para búsqueda semántica"""
    servicios = []
    csv_path = Path("./RAG/SERVICIOS_DIGITALES.csv")
    
    try:
        if csv_path.exists():
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=';')
                for row in reader:
                    servicios.append({
                        "nombre": row.get('TXNOMBRE', ''),
                        "descripcion": row.get('TXDESCRIPCIONCORTA', ''),
                        "enlace": row.get('TXENLACE', '')
                    })
            print(f"Servicios para búsqueda cargados: {len(servicios)} servicios")
        else:
            print(f"Archivo CSV de búsqueda no encontrado en: {csv_path}")
    except Exception as e:
        print(f"Error al cargar servicios para búsqueda: {e}")
    
    return servicios

# Cargar servicios al inicio
servicios_digitales = cargar_servicios_digitales()
servicios_busqueda = cargar_servicios_busqueda()

def buscar_servicios_semanticamente(consulta_usuario: str, top_k: int = 5) -> List[dict]:
    """
    Busca servicios relevantes usando el LLM para análisis semántico
    """
    if not servicios_busqueda:
        return []
    
    # Crear prompt para el LLM
    servicios_texto = ""
    for i, servicio in enumerate(servicios_busqueda):
        servicios_texto += f"{i+1}. {servicio['nombre']}: {servicio['descripcion']}\n"
    
    prompt = f"""
    Eres un asistente experto en servicios digitales del JNE. 
    
    El usuario busca: "{consulta_usuario}"
    
    Analiza los siguientes servicios y selecciona los {top_k} más relevantes para la consulta del usuario.
    Responde SOLO con los números de los servicios más relevantes, separados por comas.
    
    Servicios disponibles:
    {servicios_texto}
    
    Números de servicios más relevantes:"""
    
    try:
        # Usar el LLM para encontrar servicios relevantes
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=prompt
        )
        
        # Parsear la respuesta del LLM
        numeros_texto = response.text.strip()
        numeros = []
        
        # Extraer números de la respuesta
        for parte in numeros_texto.split(','):
            parte = parte.strip()
            if parte.isdigit():
                numero = int(parte) - 1  # Convertir a índice base 0
                if 0 <= numero < len(servicios_busqueda):
                    numeros.append(numero)
        
        # Obtener los servicios seleccionados
        servicios_seleccionados = []
        for numero in numeros[:top_k]:
            servicios_seleccionados.append(servicios_busqueda[numero])
        
        return servicios_seleccionados
        
    except Exception as e:
        print(f"Error en búsqueda semántica: {e}")
        # Fallback: devolver primeros servicios
        return servicios_busqueda[:top_k]

def generar_menu_servicios_busqueda(servicios_encontrados: List[dict]) -> str:
    """Genera el menú de servicios encontrados por búsqueda semántica"""
    if not servicios_encontrados:
        return "No se encontraron servicios relevantes para tu consulta. Por favor, intenta con otros términos."
    
    menu_text = "Servicios encontrados para tu consulta:\n\n"
    for i, servicio in enumerate(servicios_encontrados, 1):
        nombre = servicio.get('nombre', 'Sin nombre')
        # Truncar nombre si es muy largo
        if len(nombre) > 60:
            nombre = nombre[:57] + "..."
        menu_text += f"{i}. {nombre}\n"
    
    menu_text += "\nElige un número para ver más detalles:"
    return menu_text

def generar_opciones_servicios_busqueda(servicios_encontrados: List[dict]) -> Dict[str, str]:
    """Genera las opciones del menú de servicios encontrados"""
    opciones = {}
    for i in range(len(servicios_encontrados)):
        opciones[str(i + 1)] = f"busqueda_{i}"
    return opciones

def generar_menu_servicios_digitales() -> str:
    """Genera el texto del menú de servicios digitales"""
    if not servicios_digitales:
        return "No hay servicios digitales disponibles en este momento."
    
    menu_text = "Servicios digitales disponibles:\n"
    for opcion, servicio in servicios_digitales.items():
        nombre = servicio.get('nombre', 'Sin nombre')
        # Truncar nombre si es muy largo
        if len(nombre) > 50:
            nombre = nombre[:47] + "..."
        menu_text += f"{opcion}. {nombre}\n"
    
    menu_text += "\nElige un número para ver más detalles:"
    return menu_text

def generar_opciones_servicios_digitales() -> Dict[str, str]:
    """Genera las opciones del menú de servicios digitales"""
    opciones = {}
    for opcion in servicios_digitales.keys():
        opciones[opcion] = f"servicio_{opcion}"
    return opciones


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
        "text": "Servicios Digitales:\n1. Los servicios mas usados por la ciudadanía\n2. Consulta por un trámite específico",
        "options": {"1": "servicios_ciudadano", "2": "tramite"}
    },
    "servicios_ciudadano": {
        "text": generar_menu_servicios_digitales(),
        "options": generar_opciones_servicios_digitales()
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
    "servicios_ciudadano": "Existen 15 resoluciones del JNE que han establecido precedentes en materia electoral.",
    "tramite": "La oficina central cuenta con 85 trabajadores administrativos distribuidos en 10 áreas.",
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
                if servicio_numero in servicios_digitales:
                    servicio = servicios_digitales[servicio_numero]
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
            servicios_encontrados = buscar_servicios_semanticamente(text, top_k=5)
            
            if servicios_encontrados:
                # Guardar servicios encontrados en el estado
                state["servicios_encontrados"] = servicios_encontrados
                state["stage"] = "awaiting_tramite_selection"
                
                # Generar menú con servicios encontrados
                respuesta = generar_menu_servicios_busqueda(servicios_encontrados)
                
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
    global servicios_digitales
    
    # Recargar servicios desde CSV
    servicios_digitales = cargar_servicios_digitales()
    
    # Actualizar menús dinámicamente
    if "servicios_ciudadano" in menus:
        menus["servicios_ciudadano"]["text"] = generar_menu_servicios_digitales()
        menus["servicios_ciudadano"]["options"] = generar_opciones_servicios_digitales()
    
    return {
        "reply": f"Servicios digitales recargados: {len(servicios_digitales)} servicios disponibles",
        "servicios_cargados": len(servicios_digitales)
    }

# Comando para ver servicios digitales disponibles
@router.get("/servicios-disponibles")
async def ver_servicios_disponibles():
    return {
        "total_servicios": len(servicios_digitales),
        "servicios": servicios_digitales
    }

# Comando para recargar servicios de búsqueda
@router.post("/recargar-servicios-busqueda")
async def recargar_servicios_busqueda():
    global servicios_busqueda
    
    # Recargar servicios desde CSV
    servicios_busqueda = cargar_servicios_busqueda()
    
    return {
        "reply": f"Servicios de búsqueda recargados: {len(servicios_busqueda)} servicios disponibles",
        "servicios_cargados": len(servicios_busqueda)
    }

# Comando para ver servicios de búsqueda disponibles
@router.get("/servicios-busqueda")
async def ver_servicios_busqueda():
    return {
        "total_servicios": len(servicios_busqueda),
        "servicios": servicios_busqueda
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