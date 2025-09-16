import os
from typing import Dict, Optional
from google import genai
from dotenv import load_dotenv

from chatbot.services.intent_validator import validate_intent
from chatbot.services.prompt_enricher import enrich_prompt
from chatbot.services.langgraph_runner import run_langgraph
from chatbot.services.db_logger import log_message
from chatbot.services.chat_memory_manager import ChatMemoryManager
from chatbot.services.servicios_digitales_manager import ServiciosDigitalesManager
from chatbot.services.informacion_institucional_manager import InformacionInstitucionalManager
from chatbot.services.procesos_electorales_manager import ProcesosElectoralesManager

load_dotenv()

# Configuración
client = genai.Client()

# Estado de usuarios en memoria
user_states: Dict[str, dict] = {}

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
    def initialize_user(chat_id) -> dict:
        """Inicializa el estado de un usuario"""
        # Convertir chat_id a string para consistencia
        chat_key = str(chat_id)
        user_states[chat_key] = {"stage": "main", "flow": []}
        return user_states[chat_key]
    
    @staticmethod
    def reset_user(chat_id):
        """Reinicia el estado de un usuario"""
        chat_key = str(chat_id)
        if chat_key in user_states:
            del user_states[chat_key]
    
    @staticmethod
    def get_user_state(chat_id) -> Optional[dict]:
        """Obtiene el estado de un usuario"""
        chat_key = str(chat_id)
        return user_states.get(chat_key)
    
    @staticmethod
    def update_user_state(chat_id, **kwargs):
        """Actualiza el estado de un usuario"""
        chat_key = str(chat_id)
        if chat_key in user_states:
            user_states[chat_key].update(kwargs)

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