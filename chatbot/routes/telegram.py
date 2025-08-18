from fastapi import APIRouter, Request
from chatbot.services.intent_validator import validate_intent
from chatbot.services.prompt_enricher import enrich_prompt
from chatbot.services.langgraph_runner import run_langgraph
from chatbot.services.db_logger import log_message
from chatbot.services.chat_memory_manager import ChatMemoryManager
from chatbot.services.servicios_digitales_manager import ServiciosDigitalesManager
from chatbot.services.informacion_institucional_manager import InformacionInstitucionalManager
from chatbot.services.procesos_electorales_manager import ProcesosElectoralesManager
import os
import httpx
from dotenv import load_dotenv
from typing import Dict, Optional
from google import genai

load_dotenv()

router = APIRouter()

# Configuración
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
client = genai.Client()

# Estado de usuarios en memoria
user_states: Dict[int, dict] = {}

# Gestores de servicios (lazy loading)
_chat_memory = None
_servicios_manager = None
_info_institucional_manager = None
_procesos_electorales_manager = None

def get_chat_memory():
    global _chat_memory
    if _chat_memory is None:
        _chat_memory = ChatMemoryManager()
    return _chat_memory

def get_servicios_manager():
    global _servicios_manager
    if _servicios_manager is None:
        _servicios_manager = ServiciosDigitalesManager()
    return _servicios_manager

def get_info_institucional_manager():
    global _info_institucional_manager
    if _info_institucional_manager is None:
        _info_institucional_manager = InformacionInstitucionalManager()
    return _info_institucional_manager

def get_procesos_electorales_manager():
    global _procesos_electorales_manager
    if _procesos_electorales_manager is None:
        _procesos_electorales_manager = ProcesosElectoralesManager()
    return _procesos_electorales_manager

# Definición de menús
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
    "servicios_ciudadano": {"text": "", "options": {}},
    "pleno": {
        "text": "",
        "options": {}
    },
}

class ChatbotStateManager:
    """Maneja el estado del chatbot y las transiciones"""
    
    @staticmethod
    def initialize_user(chat_id: int) -> dict:
        """Inicializa el estado de un usuario"""
        user_states[chat_id] = {"stage": "main", "flow": []}
        return user_states[chat_id]
    
    @staticmethod
    def reset_user(chat_id: int):
        """Reinicia el estado de un usuario"""
        if chat_id in user_states:
            del user_states[chat_id]
    
    @staticmethod
    def get_user_state(chat_id: int) -> Optional[dict]:
        """Obtiene el estado de un usuario"""
        return user_states.get(chat_id)
    
    @staticmethod
    def update_user_state(chat_id: int, **kwargs):
        """Actualiza el estado de un usuario"""
        if chat_id in user_states:
            user_states[chat_id].update(kwargs)

class ResponseManager:
    """Maneja las respuestas del bot y el logging"""
    
    @staticmethod
    async def send_response(chat_id: int, text: str, state: dict, menu_actual: str = "main"):
        """Envía respuesta y la registra en la conversación"""
        # Enviar a Telegram
        await enviar_mensaje_telegram({"chat_id": chat_id, "text": text})
        
        # Registrar en conversación
        chat_memory = get_chat_memory()
        chat_memory.agregar_respuesta_bot(
            user_id=str(chat_id),
            respuesta=text,
            menu_actual=menu_actual,
            estado_actual=state.copy()
        )
    
    @staticmethod
    def log_user_message(chat_id: int, text: str, intent: str = "navegacion_menu"):
        """Registra mensaje del usuario"""
        chat_memory = get_chat_memory()
        chat_memory.agregar_mensaje_usuario(
            user_id=str(chat_id),
            mensaje=text,
            intent=intent
        )

class MenuHandler:
    """Maneja la lógica de navegación por menús"""
    
    @staticmethod
    def handle_menu_selection(chat_id: int, text: str, state: dict) -> tuple[str, bool]:
        """Maneja la selección de opciones de menú"""
        current_menu = state["stage"]
        
        if current_menu not in menus:
            return "Menú no válido", False
            
        options = menus[current_menu]["options"]
        
        if text not in options:
            return f"Opción no válida. Escribe 'menu' para volver al menú principal.\n\n{menus[current_menu]['text']}", False
            
        chosen_key = options[text]
        state["flow"].append(chosen_key)
        
        # Casos especiales que requieren manejo específico
        if chosen_key == "servicios_ciudadano":
            return MenuHandler._handle_servicios_ciudadano(chat_id, state)
        elif chosen_key == "pleno":
            return MenuHandler._handle_pleno(chat_id, state)
        elif chosen_key == "tramite":
            return MenuHandler._handle_tramite(chat_id, state)
        elif chosen_key in ["funcionarios", "jee", "sedes", "organizacion_politica", "consulta_afiliacion"]:
            return MenuHandler._handle_info_directa(chosen_key, state)
        elif chosen_key == "cronograma_electoral":
            return MenuHandler._handle_cronograma_electoral(chat_id, state)
        elif chosen_key == "consulta_politico":
            return MenuHandler._handle_consulta_politico(chat_id, state)
        elif chosen_key in menus:
            return MenuHandler._handle_submenu(chosen_key, state)
        else:
            return MenuHandler._handle_final_choice(chosen_key, state)
    
    @staticmethod
    def _handle_servicios_ciudadano(chat_id: int, state: dict) -> tuple[str, bool]:
        """Maneja la selección de servicios ciudadano"""
        servicios_manager = get_servicios_manager()
        menus["servicios_ciudadano"]["text"] = servicios_manager.generar_menu_servicios_digitales()
        menus["servicios_ciudadano"]["options"] = servicios_manager.generar_opciones_servicios_digitales()
        state["stage"] = "servicios_ciudadano"
        return menus["servicios_ciudadano"]["text"], False
    
    @staticmethod
    def _handle_pleno(chat_id: int, state: dict) -> tuple[str, bool]:
        """Maneja la selección del pleno"""
        info_manager = get_info_institucional_manager()
        menus["pleno"]["text"] = info_manager.generar_menu_pleno()
        menus["pleno"]["options"] = info_manager.generar_opciones_pleno()
        state["stage"] = "pleno"
        return menus["pleno"]["text"], False
    
    @staticmethod
    def _handle_tramite(chat_id: int, state: dict) -> tuple[str, bool]:
        """Maneja la consulta de trámite"""
        state["stage"] = "awaiting_tramite_query"
        return "Por favor, describe qué tipo de trámite o servicio estás buscando. Por ejemplo: 'Necesito información sobre multas electorales', 'Quiero saber cómo afiliarme a un partido político', 'Busco información sobre certificados electorales', '¿Cómo puedo consultar mi padrón electoral?' o describe tu consulta con más detalle.", False
    
    @staticmethod
    def _handle_info_directa(choice: str, state: dict) -> tuple[str, bool]:
        """Maneja opciones que devuelven información directa"""
        state["stage"] = "awaiting_another_question"
        state["final_choice"] = choice
        
        if choice == "funcionarios":
            info_manager = get_info_institucional_manager()
            return info_manager.obtener_info_funcionarios() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):", True
        elif choice == "jee":
            info_manager = get_info_institucional_manager()
            return info_manager.obtener_info_jee() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):", True
        elif choice == "sedes":
            info_manager = get_info_institucional_manager()
            return info_manager.obtener_info_sedes() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):", True
        elif choice == "organizacion_politica":
            procesos_manager = get_procesos_electorales_manager()
            return procesos_manager.obtener_tipos_organizaciones_politicas() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):", True
        elif choice == "consulta_afiliacion":
            procesos_manager = get_procesos_electorales_manager()
            return procesos_manager.obtener_consulta_afiliacion() + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):", True
        
        return "Opción no implementada", False
    
    @staticmethod
    def _handle_cronograma_electoral(chat_id: int, state: dict) -> tuple[str, bool]:
        """Maneja la selección de cronograma electoral"""
        procesos_manager = get_procesos_electorales_manager()
        respuesta = procesos_manager.generar_menu_cronograma_electoral()
        state["stage"] = "awaiting_proceso_electoral"
        return respuesta, False
    
    @staticmethod
    def _handle_consulta_politico(chat_id: int, state: dict) -> tuple[str, bool]:
        """Maneja la consulta de político"""
        state["stage"] = "awaiting_politico_nombres"
        return "👤 **Consulta tu Político**\n\nPor favor, proporciona el nombre del político que deseas consultar (mínimo 1 nombre y 1 apellido):", False
    
    @staticmethod
    def _handle_submenu(menu_key: str, state: dict) -> tuple[str, bool]:
        """Maneja la navegación a submenús"""
        state["stage"] = menu_key
        return menus[menu_key]["text"], False
    
    @staticmethod
    def _handle_final_choice(choice: str, state: dict) -> tuple[str, bool]:
        """Maneja opciones finales que requieren pregunta del usuario"""
        state["stage"] = "awaiting_question"
        state["final_choice"] = choice
        return f"Has seleccionado {choice}. Ahora envía tu pregunta:", False

class StateHandler:
    """Maneja los diferentes estados del chatbot"""
    
    @staticmethod
    def _handle_exit_command(text: str, state: dict) -> tuple[str, bool]:
        """Maneja comandos de salida y retorna respuesta y si debe salir"""
        if text.lower().strip() in ["menu"]:
            # Solo regresar al menú principal (sin reiniciar estado)
            state["stage"] = "main"
            mensaje_regreso = """🔄 **¡Perfecto! Volvamos al menú principal**

🤖 **ELECCIA** está aquí para ayudarte. ¿En qué más puedo asistirte?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""
            
            return mensaje_regreso + "\n\n" + menus["main"]["text"], True
        elif text.lower().strip() in ["salir", "cancelar", "exit", "quit", "cancel", "volver", "adios", "adiós"]:
            # Finalizar conversación (comportamiento como "adios")
            state["stage"] = "main"
            mensaje_despedida = """🤖 **¡Ha sido un placer ayudarte!**

👋 **ELECCIA** se despide de ti

💡 Recuerda que siempre puedes volver cuando tengas más consultas sobre el JNE.

¡Que tengas un excelente día! 👋"""
            
            return mensaje_despedida, True
        return "", False
    
    @staticmethod
    def _get_invalid_option_message(menu_name: str, max_options: int = 0) -> str:
        """Genera mensaje de opción inválida con opción de salida"""
        if max_options > 0:
            return f"Opción no válida. Por favor, elige un número entre 1 y {max_options} o escribe 'menu' para volver al menú principal."
        else:
            return f"Por favor, elige una opción válida del menú de {menu_name} o escribe 'menu' para volver al menú principal."
    
    @staticmethod
    async def handle_state(chat_id: int, text: str, state: dict) -> str:
        """Maneja el estado actual del usuario"""
        stage = state["stage"]
        
        if stage == "awaiting_question":
            return await StateHandler._handle_question(chat_id, text, state)
        elif stage == "awaiting_tramite_query":
            return await StateHandler._handle_tramite_query(chat_id, text, state)
        elif stage == "awaiting_tramite_selection":
            return await StateHandler._handle_tramite_selection(chat_id, text, state)
        elif stage == "awaiting_pleno_selection":
            return await StateHandler._handle_pleno_selection(chat_id, text, state)
        elif stage == "awaiting_proceso_electoral":
            return await StateHandler._handle_proceso_electoral(chat_id, text, state)
        elif stage == "awaiting_hito_consulta":
            return await StateHandler._handle_hito_consulta(chat_id, text, state)
        elif stage == "awaiting_hito_selection":
            return await StateHandler._handle_hito_selection(chat_id, text, state)
        elif stage == "awaiting_politico_nombres":
            return await StateHandler._handle_politico_nombres(chat_id, text, state)
        elif stage == "awaiting_politico_segundo_apellido":
            return await StateHandler._handle_politico_segundo_apellido(chat_id, text, state)
        elif stage == "awaiting_candidato_selection":
            return await StateHandler._handle_candidato_selection(chat_id, text, state)
        elif stage == "awaiting_eleccion_candidato_selection":
            return await StateHandler._handle_eleccion_candidato_selection(chat_id, text, state)
        elif stage == "awaiting_another_question":
            return await StateHandler._handle_another_question(chat_id, text, state)
        elif stage == "servicios_ciudadano":
            return await StateHandler._handle_servicios_ciudadano_selection(chat_id, text, state)
        elif stage == "pleno":
            return await StateHandler._handle_pleno_selection(chat_id, text, state)
        
        return "Lo siento, no entiendo qué quieres hacer. Por favor, vuelve al menú principal escribiendo 'menu'.", False
    
    @staticmethod
    async def _handle_question(chat_id: int, text: str, state: dict) -> str:
        """Maneja preguntas del usuario"""
        try:
            context = context_map.get(state["final_choice"], "")
            llm_reply = send_to_llm(text, context)
            respuesta_completa = llm_reply + "\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
            state["stage"] = "awaiting_another_question"
            return respuesta_completa
        except Exception as e:
            state["stage"] = "main"
            return "Lo siento, ha ocurrido un error al procesar tu pregunta. Por favor, intenta de nuevo."
    
    @staticmethod
    async def _handle_tramite_query(chat_id: int, text: str, state: dict) -> str:
        """Maneja consultas de trámites"""
        try:
            servicios_manager = get_servicios_manager()
            servicios_encontrados = servicios_manager.buscar_servicios_semanticamente(text, top_k=5)
            
            if servicios_encontrados:
                state["servicios_encontrados"] = servicios_encontrados
                state["stage"] = "awaiting_tramite_selection"
                return servicios_manager.generar_menu_servicios_busqueda(servicios_encontrados)
            else:
                state["stage"] = "main"
                return "No se encontraron servicios relevantes para tu consulta. Te sugiero intentar con términos más específicos como 'consulta de afiliación a partidos', 'certificados electorales', 'padrón electoral', 'multas electorales' o 'información de candidatos'. ¿Quieres intentar con otra consulta?"
        except Exception as e:
            state["stage"] = "main"
            return "Lo siento, ha ocurrido un error al buscar trámites. Por favor, intenta de nuevo."
    
    @staticmethod
    async def _handle_tramite_selection(chat_id: int, text: str, state: dict) -> str:
        """Maneja la selección de trámites"""
        servicios_encontrados = state.get("servicios_encontrados", [])
        
        # Verificar si hay servicios disponibles
        if not servicios_encontrados:
            state["stage"] = "main"
            return "No hay servicios disponibles para seleccionar en este momento. Esto puede deberse a un problema temporal con la base de datos o que la información no esté disponible. ¿Quieres intentar con otra consulta o buscar otra información?"
        
        if text.isdigit():
            opcion = int(text)
            
            if 1 <= opcion <= len(servicios_encontrados):
                servicio = servicios_encontrados[opcion - 1]
                respuesta = f"📋 **{servicio['nombre']}**\n\n📝 **Descripción:** {servicio['descripcion']}\n\n🔗 **Enlace:** {servicio['enlace']}\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
                state["stage"] = "awaiting_another_question"
                state["final_choice"] = "tramite_seleccion"
                return respuesta
            else:
                return f"Opción no válida. Por favor, elige un número entre 1 y {len(servicios_encontrados)} o escribe 'menu' para volver al menú principal."
        else:
            # Verificar si es un comando de salida
            exit_response, should_exit = StateHandler._handle_exit_command(text, state)
            if should_exit:
                return exit_response
            else:
                return StateHandler._get_invalid_option_message("servicios")
    
    @staticmethod
    async def _handle_pleno_selection(chat_id: int, text: str, state: dict) -> str:
        """Maneja la selección de miembros del pleno"""
        info_manager = get_info_institucional_manager()
        pleno_miembros = info_manager.pleno_miembros
        
        # Verificar si hay miembros del pleno disponibles
        if not pleno_miembros:
            state["stage"] = "main"
            return "No hay información del pleno disponible en este momento. Esto puede deberse a un problema temporal con la base de datos o que la información no esté disponible. ¿Quieres consultar otra información o intentar más tarde?"
        
        if text.isdigit():
            opcion = int(text)
            
            if 1 <= opcion <= len(pleno_miembros):
                miembro = pleno_miembros[str(opcion)]
                respuesta = f"👨‍⚖️ **{miembro['cargo']}**\n\n👤 **Nombre:** {miembro['nombre']}\n\n📝 **Descripción:** {miembro['descripcion']}\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
                state["stage"] = "awaiting_another_question"
                state["final_choice"] = "pleno_seleccion"
                return respuesta
            else:
                return f"Opción no válida. Por favor, elige un número entre 1 y {len(pleno_miembros)} o escribe 'menu' para volver al menú principal."
        else:
            # Verificar si es un comando de salida
            exit_response, should_exit = StateHandler._handle_exit_command(text, state)
            if should_exit:
                return exit_response
            else:
                return StateHandler._get_invalid_option_message("pleno")
    
    @staticmethod
    async def _handle_proceso_electoral(chat_id: int, text: str, state: dict) -> str:
        """Maneja la selección de procesos electorales"""
        if text.isdigit():
            opcion = int(text)
            procesos_especificos = ["EG.2026", "EMC.2025", "ERM.2022", "EG.2021"]
            
            if opcion == len(procesos_especificos) + 1:
                procesos_manager = get_procesos_electorales_manager()
                respuesta = procesos_manager.obtener_otros_procesos_electorales()
                state["stage"] = "awaiting_another_question"
                state["final_choice"] = "otros_procesos_electorales"
                return respuesta
            elif 1 <= opcion <= len(procesos_especificos):
                proceso_seleccionado = procesos_especificos[opcion - 1]
                state["proceso_electoral"] = proceso_seleccionado
                state["stage"] = "awaiting_hito_consulta"
                return f"📅 Has seleccionado: **{proceso_seleccionado}**\n\n¿Qué hitos electorales deseas consultar? Por ejemplo: '¿Cuándo son las elecciones generales?', '¿Cuál es la fecha límite para inscripción de candidatos?', '¿En qué fechas se realizarán las votaciones?' o describe lo que buscas."
            else:
                return f"Opción no válida. Por favor, elige un número entre 1 y {len(procesos_especificos) + 1} o escribe 'menu' para volver al menú principal."
        else:
            # Verificar si es un comando de salida
            exit_response, should_exit = StateHandler._handle_exit_command(text, state)
            if should_exit:
                return exit_response
            else:
                return StateHandler._get_invalid_option_message("procesos electorales")
    
    @staticmethod
    async def _handle_hito_consulta(chat_id: int, text: str, state: dict) -> str:
        """Maneja consultas de hitos electorales"""
        try:
            procesos_manager = get_procesos_electorales_manager()
            proceso_electoral = state.get("proceso_electoral")
            
            if not proceso_electoral:
                state["stage"] = "main"
                return "Error: No se encontró el proceso electoral seleccionado. Por favor, vuelve al menú principal."
            
            hitos = procesos_manager.buscar_hitos_electorales_semanticamente(proceso_electoral, text)
            
            if hitos:
                state["hitos_encontrados"] = hitos
                state["stage"] = "awaiting_hito_selection"
                return procesos_manager.generar_menu_hitos(hitos)
            else:
                state["stage"] = "main"
                return "No se encontraron hitos electorales que coincidan exactamente con tu consulta. Te sugiero intentar con términos más específicos como 'elecciones generales', 'inscripción de candidatos', 'votaciones', 'fechas límite' o 'cronograma electoral'. ¿Quieres intentar con otra consulta?"
        except Exception as e:
            state["stage"] = "main"
            return "Error al buscar hitos electorales. Por favor, intenta de nuevo."
    
    @staticmethod
    async def _handle_hito_selection(chat_id: int, text: str, state: dict) -> str:
        """Maneja la selección de hitos electorales"""
        hitos = state.get("hitos_encontrados", [])
        
        # Verificar si hay hitos disponibles
        if not hitos:
            state["stage"] = "main"
            return "No hay hitos electorales disponibles para seleccionar en este momento. Esto puede deberse a un problema temporal con la base de datos o que la información no esté disponible. ¿Quieres intentar con otra consulta o buscar otra información?"
        
        if text.isdigit():
            opcion = int(text)
            
            if 1 <= opcion <= len(hitos):
                hito_seleccionado = hitos[opcion - 1]
                procesos_manager = get_procesos_electorales_manager()
                respuesta = procesos_manager.formatear_hito_electoral(hito_seleccionado)
                state["stage"] = "awaiting_another_question"
                state["final_choice"] = "hito_electoral"
                return respuesta
            else:
                return f"Opción no válida. Por favor, elige un número entre 1 y {len(hitos)} o escribe 'menu' para volver al menú principal."
        else:
            # Verificar si es un comando de salida
            exit_response, should_exit = StateHandler._handle_exit_command(text, state)
            if should_exit:
                return exit_response
            else:
                return StateHandler._get_invalid_option_message("hitos electorales")
    
    @staticmethod
    async def _handle_politico_nombres(chat_id: int, text: str, state: dict) -> str:
        """Maneja la entrada de nombres del político"""
        texto_entrada = text.strip()
        
        if len(texto_entrada.split()) < 2:
            return "Por favor, proporciona al menos un nombre y un apellido del político que deseas consultar."
        
        procesos_manager = get_procesos_electorales_manager()
        
        # Usar búsqueda inteligente que maneja múltiples formatos
        candidatos = procesos_manager.buscar_candidatos_inteligente(texto_entrada)
        
        if not candidatos:
            # No se encontraron candidatos, volver al menú principal
            state["stage"] = "main"
            return "No se encontraron candidatos que coincidan exactamente con tu búsqueda. \n\n🔗 **Más Información:** https://infogob.jne.gob.pe/Politico\n\n¿Quieres intentar con otra búsqueda?"
        
        if len(candidatos) > 10:
            # Parsear el texto para obtener nombres y primer apellido
            parsed = procesos_manager.parsear_nombre_completo(texto_entrada)
            state["nombres_politico"] = parsed["nombres"]
            state["primer_apellido"] = parsed["apellido_paterno"]
            state["stage"] = "awaiting_politico_segundo_apellido"
            return f"Se encontraron {len(candidatos)} candidatos. Por favor, proporciona el segundo apellido para refinar la búsqueda."
        else:
            state["candidatos_encontrados"] = candidatos
            state["stage"] = "awaiting_candidato_selection"
            return procesos_manager.generar_menu_candidatos(candidatos)
    
    @staticmethod
    async def _handle_politico_segundo_apellido(chat_id: int, text: str, state: dict) -> str:
        """Maneja el segundo apellido del político"""
        nombres = state.get("nombres_politico", "")
        primer_apellido = state.get("primer_apellido", "")
        
        texto_entrada = text.strip()
        palabras_entrada = texto_entrada.split()
        
        procesos_manager = get_procesos_electorales_manager()
        
        # Validar que el usuario ingrese solo un apellido
        if len(palabras_entrada) > 1:
            return f"❌ **Por favor, ingresa SOLO el segundo apellido.**\n\n💡 **No ingreses el nombre completo, solo el segundo apellido para refinar la búsqueda.**"
        
        if len(palabras_entrada) == 0:
            return "❌ **Por favor, ingresa el segundo apellido.**"
        
        # Usuario ingresó solo un segundo apellido (caso correcto)
        segundo_apellido = texto_entrada
        
        # Buscar candidatos con ambos apellidos
        candidatos = procesos_manager.buscar_candidatos_por_apellidos_separados(nombres, primer_apellido, segundo_apellido)
        
        if not candidatos:
            # No se encontraron candidatos, volver al menú principal
            state["stage"] = "main"
            return f"❌ **No se encontraron candidatos** con el nombre '{nombres}' y apellidos '{primer_apellido} {segundo_apellido}'.\n\n🔗 **Más Información:** https://infogob.jne.gob.pe/Politico\n\n¿Quieres intentar con otra búsqueda?"
        
        state["candidatos_encontrados"] = candidatos
        state["stage"] = "awaiting_candidato_selection"
        return procesos_manager.generar_menu_candidatos(candidatos)
    
    @staticmethod
    async def _handle_candidato_selection(chat_id: int, text: str, state: dict) -> str:
        """Maneja la selección de candidatos"""
        candidatos = state.get("candidatos_encontrados", [])
        
        # Verificar si hay candidatos disponibles
        if not candidatos:
            state["stage"] = "main"
            return "No hay candidatos disponibles para seleccionar en este momento. Esto puede deberse a un problema temporal con la base de datos o que la información no esté disponible. ¿Quieres intentar con otra búsqueda o consultar otra información?"
        
        if text.isdigit():
            opcion = int(text)
            
            if 1 <= opcion <= len(candidatos):
                candidato_seleccionado = candidatos[opcion - 1]
                procesos_manager = get_procesos_electorales_manager()
                elecciones = procesos_manager.obtener_elecciones_por_candidato(
                    candidato_seleccionado["nombres"],
                    candidato_seleccionado["apellido_paterno"],
                    candidato_seleccionado["apellido_materno"]
                )
                
                if elecciones:
                    state["candidato_seleccionado"] = candidato_seleccionado
                    state["elecciones_candidato"] = elecciones
                    state["stage"] = "awaiting_eleccion_candidato_selection"
                    return procesos_manager.generar_menu_elecciones_candidato(elecciones, candidato_seleccionado["nombre_completo"])
                else:
                    state["stage"] = "main"
                    return f"No se encontraron elecciones para {candidato_seleccionado['nombre_completo']}. Esto puede deberse a que el candidato no participó en elecciones o la información no está disponible en este momento. ¿Quieres consultar otro candidato?"
            else:
                return f"Opción no válida. Por favor, elige un número entre 1 y {len(candidatos)} o escribe 'menu' para volver al menú principal."
        else:
            # Verificar si es un comando de salida
            exit_response, should_exit = StateHandler._handle_exit_command(text, state)
            if should_exit:
                return exit_response
            else:
                return StateHandler._get_invalid_option_message("candidatos")
    
    @staticmethod
    async def _handle_eleccion_candidato_selection(chat_id: int, text: str, state: dict) -> str:
        """Maneja la selección de elección para un candidato"""
        elecciones = state.get("elecciones_candidato", [])
        candidato = state.get("candidato_seleccionado", {})
        
        # Verificar si hay elecciones disponibles
        if not elecciones:
            state["stage"] = "main"
            return "No hay elecciones disponibles para este candidato en este momento. Esto puede deberse a que el candidato no participó en elecciones o la información no está disponible. ¿Quieres consultar otro candidato o buscar otra información?"
        
        if text.isdigit():
            opcion = int(text)
            
            if 1 <= opcion <= len(elecciones):
                eleccion_seleccionada = elecciones[opcion - 1]
                procesos_manager = get_procesos_electorales_manager()
                detalle = procesos_manager.obtener_detalle_candidato_eleccion(
                    candidato["nombres"],
                    candidato["apellido_paterno"],
                    candidato["apellido_materno"],
                    eleccion_seleccionada
                )
                
                if detalle:
                    respuesta = procesos_manager.formatear_politico(detalle)
                    state["stage"] = "awaiting_another_question"
                    return respuesta
                else:
                    state["stage"] = "main"
                    return f"No se encontró información detallada para {candidato['nombre_completo']} en {eleccion_seleccionada}. Esto puede deberse a que la información no está completa en la base de datos o el candidato no participó en esa elección específica. ¿Quieres consultar otro candidato o elección?"
            else:
                return f"Opción no válida. Por favor, elige un número entre 1 y {len(elecciones)} o escribe 'menu' para volver al menú principal."
        else:
            # Verificar si es un comando de salida
            exit_response, should_exit = StateHandler._handle_exit_command(text, state)
            if should_exit:
                return exit_response
            else:
                return StateHandler._get_invalid_option_message("elecciones")
    
    @staticmethod
    async def _handle_servicios_ciudadano_selection(chat_id: int, text: str, state: dict) -> str:
        """Maneja la selección de servicios digitales del ciudadano"""
        servicios_manager = get_servicios_manager()
        
        if text.isdigit():
            opcion = int(text)
            servicios_disponibles = servicios_manager.obtener_servicios_digitales()
            
            if 1 <= opcion <= len(servicios_disponibles):
                servicio = servicios_disponibles[opcion - 1]
                respuesta = f"📋 **{servicio['nombre']}**\n\n📝 **Descripción:** {servicio['descripcion']}\n\n🔗 **Enlace:** {servicio['enlace']}\n\n¿Tienes otra consulta? (responde 'si' o 'no'):"
                state["stage"] = "awaiting_another_question"
                state["final_choice"] = "servicio_digital_seleccion"
                return respuesta
            else:
                return f"Opción no válida. Por favor, elige un número entre 1 y {len(servicios_disponibles)} o escribe 'menu' para volver al menú principal."
        else:
            # Verificar si es un comando de salida
            exit_response, should_exit = StateHandler._handle_exit_command(text, state)
            if should_exit:
                return exit_response
            else:
                return StateHandler._get_invalid_option_message("servicios digitales")
    
    @staticmethod
    async def _handle_another_question(chat_id: int, text: str, state: dict) -> str:
        """Maneja la confirmación de otra consulta"""
        text_lower = text.lower().strip()
        
        if text_lower in ["si", "sí", "yes", "y", "1"]:
            state["stage"] = "main"
            mensaje_regreso = """🔄 **¡Excelente! Volvamos al menú principal**

🤖 **ELECCIA** está aquí para ayudarte. ¿En qué más puedo asistirte?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""
            
            return mensaje_regreso + "\n\n" + menus["main"]["text"]
        elif text_lower in ["menu"]:
            # Regresar al menú principal
            state["stage"] = "main"
            mensaje_regreso = """🔄 **¡Perfecto! Volvamos al menú principal**

🤖 **ELECCIA** está aquí para ayudarte. ¿En qué más puedo asistirte?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""
            
            return mensaje_regreso + "\n\n" + menus["main"]["text"]
        elif text_lower in ["no", "n", "0"]:
            # Finalizar conversación
            chat_memory = get_chat_memory()
            chat_memory.finalizar_conversacion(
                user_id=str(chat_id),
                motivo="Usuario confirmó que no tiene más consultas"
            )
            ChatbotStateManager.reset_user(chat_id)
            
            mensaje_despedida = """🤖 **¡Ha sido un placer ayudarte!**

👋 **ELECCIA** se despide de ti

💡 Recuerda que siempre puedes volver cuando tengas más consultas sobre el JNE.

¡Que tengas un excelente día! 👋"""
            
            return mensaje_despedida
        elif text_lower in ["adios", "adiós"]:
            # Finalizar conversación con comando adios
            chat_memory = get_chat_memory()
            chat_memory.finalizar_conversacion(
                user_id=str(chat_id),
                motivo="Usuario finalizó conversación con comando adios"
            )
            ChatbotStateManager.reset_user(chat_id)
            
            mensaje_despedida = """🤖 **¡Ha sido un placer ayudarte!**

👋 **ELECCIA** se despide de ti

💡 Recuerda que siempre puedes volver cuando tengas más consultas sobre el JNE.

¡Que tengas un excelente día! 👋"""
            
            return mensaje_despedida
        else:
            return "Por favor, responde 'si' o 'no' si tienes otra consulta:"

# Contexto adicional para LLM
context_map = {
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
    """Envía la pregunta al LLM con contexto adicional"""
    prompt = f"{extra_context}\n\nPregunta del usuario: {user_input}"
    
    try:
        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error al procesar la consulta: {str(e)}"

@router.post("")
async def tilin_chatbot(req: Request):
    """Endpoint principal del chatbot"""
    body = await req.json()
    datos = normalizar_input_telegram(body)
    
    chat_id = datos["chat_id"]
    text = datos["text"]
    
    # Obtener instancia de ChatMemoryManager
    chat_memory = get_chat_memory()
    
    # Verificar si el usuario tiene una conversación activa
    conversacion_activa = chat_memory.obtener_conversacion_activa(str(chat_id))
    
    # Si no hay conversación activa o no existe estado del usuario, iniciar una nueva
    if not conversacion_activa or chat_id not in user_states:
        state = ChatbotStateManager.initialize_user(chat_id)
        
        if not conversacion_activa:
            chat_memory.iniciar_conversacion(str(chat_id))
        
        # Mensaje de bienvenida amigable para ELECCIA
        mensaje_bienvenida = """🤖 **¡Hola! Soy ELECCIA, tu asistente virtual del JNE**

👋 **Bienvenido/a al Jurado Nacional de Elecciones**

¿En qué puedo ayudarte hoy?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""
        
        respuesta = mensaje_bienvenida + "\n\n" + menus["main"]["text"]
        await ResponseManager.send_response(chat_id, respuesta, state, "main")
        return {"reply": respuesta}
    
    # Obtener el estado actual del usuario
    state = ChatbotStateManager.get_user_state(chat_id)
    
    # Agregar mensaje del usuario a la conversación
    ResponseManager.log_user_message(
        chat_id, 
        text, 
        "navegacion_menu" if state["stage"] in menus else "consulta_informacion"
    )
    
    # Verificar comandos especiales
    if text.lower().strip() in ["menu"]:
        # Solo regresar al menú principal (sin reiniciar estado)
        mensaje_regreso = """🔄 **¡Perfecto! Volvamos al menú principal**

🤖 **ELECCIA** está aquí para ayudarte. ¿En qué más puedo asistirte?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""
        
        respuesta = mensaje_regreso + "\n\n" + menus["main"]["text"]
        state["stage"] = "main"
        await ResponseManager.send_response(chat_id, respuesta, state, "main")
        return {"reply": respuesta}
    
    elif text.lower().strip() in ["salir", "cancelar", "exit", "quit", "cancel", "volver", "adios", "adiós"]:
        # Finalizar conversación (comportamiento como "adios")
        chat_memory = get_chat_memory()
        chat_memory.finalizar_conversacion(
            user_id=str(chat_id),
            motivo="Usuario finalizó conversación con comando de salida"
        )
        ChatbotStateManager.reset_user(chat_id)
        
        mensaje_despedida = """🤖 **¡Ha sido un placer ayudarte!**

👋 **ELECCIA** se despide de ti

💡 Recuerda que siempre puedes volver cuando tengas más consultas sobre el JNE.

¡Que tengas un excelente día! 👋"""
        
        await ResponseManager.send_response(chat_id, mensaje_despedida, {"stage": "main", "flow": []}, "despedida")
        return {"reply": mensaje_despedida}

    # Si el usuario está en un menú (excluyendo servicios_ciudadano y pleno que se manejan dinámicamente)
    if state["stage"] in menus and state["stage"] not in ["servicios_ciudadano", "pleno"]:
        respuesta, is_final = MenuHandler.handle_menu_selection(chat_id, text, state)
        
        if is_final:
            await ResponseManager.send_response(chat_id, respuesta, state, state.get("final_choice", "consulta_general"))
        else:
            await ResponseManager.send_response(chat_id, respuesta, state, state["stage"])
        
        return {"reply": respuesta}
    
    # Si el usuario está en un estado específico (incluyendo servicios_ciudadano)
    respuesta = await StateHandler.handle_state(chat_id, text, state)
    await ResponseManager.send_response(chat_id, respuesta, state, state.get("final_choice", "consulta_general"))
    
    return {"reply": respuesta}

# Endpoints de administración (mantenidos para compatibilidad)
@router.post("/finalizar")
async def finalizar_conversacion(req: Request):
    body = await req.json()
    chat_id = body.get("chat_id", 0)
    
    chat_memory = get_chat_memory()
    success = chat_memory.finalizar_conversacion(
        user_id=str(chat_id),
        motivo="Usuario finalizó conversación manualmente"
    )
    
    ChatbotStateManager.reset_user(chat_id)
    
    if success:
        mensaje_finalizacion = """✅ **¡Perfecto! Todo listo**

🤖 **ELECCIA** agradece tu consulta

¡Que tengas un excelente día! 👋"""
        return {"reply": mensaje_finalizacion}
    else:
        mensaje_error = """❌ **Ups, algo salió mal**

🤖 **ELECCIA** encontró un problema

Por favor, intenta nuevamente."""
        return {"reply": mensaje_error}

@router.get("/estado-usuario/{chat_id}")
async def ver_estado_usuario(chat_id: int):
    estado_memoria = user_states.get(chat_id, "No existe")
    chat_memory = get_chat_memory()
    conversacion_redis = chat_memory.obtener_conversacion_activa(str(chat_id))
    
    return {
        "chat_id": chat_id,
        "estado_memoria": estado_memoria,
        "conversacion_redis": conversacion_redis is not None,
        "conversacion_detalle": conversacion_redis
    }

@router.post("/reiniciar-estado")
async def reiniciar_estado_usuario(req: Request):
    body = await req.json()
    chat_id = body.get("chat_id", 0)
    
    ChatbotStateManager.reset_user(chat_id)
    
    chat_memory = get_chat_memory()
    if chat_memory.obtener_conversacion_activa(str(chat_id)):
        chat_memory.finalizar_conversacion(
            user_id=str(chat_id),
            motivo="Estado reiniciado manualmente"
        )
    
    mensaje_reinicio = """🔄 **¡Listo! Todo está listo para empezar de nuevo**

🤖 **ELECCIA** está listo para ayudarte nuevamente

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar

¡Bienvenido/a de vuelta! 👋"""
    
    return {"reply": mensaje_reinicio}

# Funciones auxiliares
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