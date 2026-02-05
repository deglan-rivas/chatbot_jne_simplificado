from typing import Optional, Dict, Any
from datetime import datetime
from chatbot.utils.chatbot_core import (
    ChatbotStateManager, get_chat_memory, menus
)
from chatbot.utils.chatbot_handlers import (
    ResponseManager, MenuHandler, StateHandler
)
from chatbot.utils.response_builder import ResponseBuilder
import logging

logger = logging.getLogger(__name__)

class ChatbotService:
    """Servicio centralizado para procesar mensajes del chatbot"""
    
    def __init__(self):
        self.chat_memory = get_chat_memory()
        self.state_manager = ChatbotStateManager()
        self.response_manager = ResponseManager()
        self.menu_handler = MenuHandler()
        self.state_handler = StateHandler()
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        platform: str = "web",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario
        
        Args:
            user_id: ID único del usuario
            message: Mensaje del usuario
            platform: Plataforma (telegram, whatsapp, web)
            metadata: Metadatos adicionales (opcional)
        
        Returns:
            {
                "response": str,
                "state": dict,
                "menu_actual": str,
                "should_finalize": bool,
                "conversation_active": bool
            }
        """
        # Normalizar user_id a string
        user_id_str = str(user_id)
        
        try:
            # Obtener conversación activa
            conversacion_activa = self.chat_memory.obtener_conversacion_activa(user_id_str)
            
            # Inicializar si no hay conversación activa
            if not conversacion_activa:
                self.chat_memory.iniciar_conversacion(
                    user_id_str,
                    mensaje_inicial="Inicio de conversación",
                    numero_telefono=metadata.get("numero_telefono") if metadata else None,
                    usuario=metadata.get("usuario") if metadata else None
                )
                conversacion_activa = self.chat_memory.obtener_conversacion_activa(user_id_str)
            
            # Obtener o inicializar estado
            state = self.state_manager.get_user_state(user_id_str)
            if not state:
                state = self.state_manager.initialize_user(user_id_str)
            
            # Registrar mensaje del usuario
            self.response_manager.log_user_message(
                user_id_str,
                message,
                "navegacion_menu" if state["stage"] in menus else "consulta_informacion"
            )
            
            # Procesar comandos especiales
            if message.lower().strip() in ["menu"]:
                state["stage"] = "main"
                respuesta = self._get_menu_message() + "\n\n" + menus["main"]["text"]
                await self.response_manager.send_response(
                    user_id_str, respuesta, state, "main", platform=platform
                )
                result = {
                    "response": respuesta,
                    "state": state,
                    "menu_actual": "main",
                    "should_finalize": False,
                    "conversation_active": True
                }
                # Agregar response_rich para web
                if platform == "web":
                    response_rich = ResponseBuilder.build_response(
                        respuesta, state, "main", False
                    )
                    if response_rich:
                        result["response_rich"] = response_rich
                return result
            
            elif message.lower().strip() in ["salir", "cancelar", "exit", "quit", 
                                             "cancel", "volver", "adios", "adiós"]:
                self.chat_memory.finalizar_conversacion(
                    user_id_str,
                    motivo="Usuario finalizó conversación con comando de salida"
                )
                self.state_manager.reset_user(user_id_str)
                respuesta = self._get_farewell_message()
                result = {
                    "response": respuesta,
                    "state": {"stage": "main", "flow": []},
                    "menu_actual": "despedida",
                    "should_finalize": True,
                    "conversation_active": False
                }
                # Agregar response_rich para web
                if platform == "web":
                    response_rich = ResponseBuilder.build_response(
                        respuesta, {"stage": "main", "flow": []}, "despedida", True
                    )
                    if response_rich:
                        result["response_rich"] = response_rich
                return result
            
            # Procesar según estado actual
            if state["stage"] in menus and state["stage"] not in ["servicios_ciudadano", "pleno"]:
                # Manejar selección de menú
                respuesta, is_final = self.menu_handler.handle_menu_selection(
                    user_id_str, message, state
                )
                # Asegurar que menu_actual siempre tenga un valor
                menu_actual = state.get("final_choice", state["stage"]) if is_final else state["stage"]
                await self.response_manager.send_response(
                    user_id_str, respuesta, state, menu_actual, platform=platform
                )
                result = {
                    "response": respuesta,
                    "state": state,
                    "menu_actual": menu_actual,
                    "should_finalize": is_final,
                    "conversation_active": True
                }
                # Agregar response_rich para web (siempre que sea plataforma web)
                if platform == "web":
                    response_rich = ResponseBuilder.build_response(
                        respuesta, state, menu_actual, is_final
                    )
                    if response_rich:
                        result["response_rich"] = response_rich
                return result
            else:
                # Manejar estado específico
                respuesta = await self.state_handler.handle_state(user_id_str, message, state)
                menu_actual = state.get("final_choice", "consulta_general")
                await self.response_manager.send_response(
                    user_id_str, respuesta, state, menu_actual, platform=platform
                )
                
                # Verificar si se debe finalizar
                should_finalize = "adiós" in respuesta.lower() or "despedida" in menu_actual
                
                result = {
                    "response": respuesta,
                    "state": state,
                    "menu_actual": menu_actual,
                    "should_finalize": should_finalize,
                    "conversation_active": not should_finalize
                }
                # Agregar response_rich para web
                if platform == "web":
                    response_rich = ResponseBuilder.build_response(
                        respuesta, state, menu_actual, should_finalize
                    )
                    if response_rich:
                        result["response_rich"] = response_rich
                return result
        
        except Exception as e:
            logger.error(f"Error procesando mensaje para usuario {user_id_str}: {e}", exc_info=True)
            return {
                "response": "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, intenta de nuevo.",
                "state": {"stage": "main", "flow": []},
                "menu_actual": "error",
                "should_finalize": False,
                "conversation_active": True
            }
    
    def _get_menu_message(self) -> str:
        """Retorna mensaje de regreso al menú"""
        return """🔄 **¡Perfecto! Volvamos al menú principal**

🤖 **ELECCIA** está aquí para ayudarte. ¿En qué más puedo asistirte?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""
    
    def _get_farewell_message(self) -> str:
        """Retorna mensaje de despedida"""
        return """🤖 **¡Ha sido un placer ayudarte!**

👋 **ELECCIA** se despide de ti

💡 Recuerda que siempre puedes volver cuando tengas más consultas sobre el JNE.

¡Que tengas un excelente día! 👋"""
    
    def get_welcome_message(self) -> str:
        """Retorna mensaje de bienvenida"""
        return """🤖 **¡Hola! Soy ELECCIA, tu asistente virtual del JNE**

👋 **Bienvenido/a al Jurado Nacional de Elecciones**

¿En qué puedo ayudarte hoy?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""


# Instancia global
_chatbot_service = None

def get_chatbot_service() -> ChatbotService:
    """Obtiene instancia singleton del servicio"""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service
