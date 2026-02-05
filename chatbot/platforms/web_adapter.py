from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from fastapi import WebSocket
from chatbot.platforms.base import PlatformAdapter
import logging

logger = logging.getLogger(__name__)

# Zona horaria de Perú (America/Lima, UTC-5)
PERU_TIMEZONE = timezone(timedelta(hours=-5))

def get_current_timestamp() -> str:
    """
    Obtiene el timestamp actual en la zona horaria de Perú (America/Lima, UTC-5)
    Retorna formato ISO8601 con información de zona horaria
    """
    now = datetime.now(PERU_TIMEZONE)
    return now.isoformat()

class WebAdapter(PlatformAdapter):
    """Adaptador para interfaz web con WebSocket"""
    
    def __init__(self):
        # Diccionario de conexiones WebSocket activas por user_id
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def send_message(self, user_id: str, message: str) -> bool:
        """
        Envía mensaje al usuario web a través de WebSocket
        
        Args:
            user_id: ID único del usuario
            message: Mensaje a enviar
        
        Returns:
            bool: True si se envió correctamente
        """
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_json({
                    "type": "message",
                    "content": message,
                    "timestamp": get_current_timestamp()
                })
                return True
            except Exception as e:
                logger.error(f"Error enviando mensaje WebSocket a {user_id}: {e}")
                # Eliminar conexión si falla
                self.unregister_connection(user_id)
                return False
        return False
    
    def normalize_input(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza input de la interfaz web
        
        Esperado:
        {
            "user_id": "string" o "session_id": "string",
            "message": "string",
            "metadata": dict (opcional)
        }
        
        Returns:
            {
                "chat_id": str,
                "text": str,
                "metadata": dict
            }
        """
        user_id = raw_input.get("user_id") or raw_input.get("session_id", "unknown")
        message = raw_input.get("message", "").strip()
        
        return {
            "chat_id": str(user_id),
            "text": message,
            "metadata": raw_input.get("metadata", {
                "session_id": raw_input.get("session_id"),
                "user_agent": raw_input.get("user_agent"),
                "ip_address": raw_input.get("ip_address")
            })
        }
    
    def register_connection(self, user_id: str, websocket: WebSocket):
        """
        Registra una conexión WebSocket
        
        Args:
            user_id: ID único del usuario
            websocket: Conexión WebSocket
        """
        self.active_connections[user_id] = websocket
        logger.info(f"Conexión WebSocket registrada para usuario {user_id}")
    
    def unregister_connection(self, user_id: str):
        """
        Elimina una conexión WebSocket
        
        Args:
            user_id: ID único del usuario
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"Conexión WebSocket eliminada para usuario {user_id}")
    
    def is_connected(self, user_id: str) -> bool:
        """
        Verifica si un usuario tiene conexión activa
        
        Args:
            user_id: ID único del usuario
        
        Returns:
            bool: True si está conectado
        """
        return user_id in self.active_connections
    
    def get_active_connections_count(self) -> int:
        """
        Obtiene el número de conexiones activas
        
        Returns:
            int: Número de conexiones activas
        """
        return len(self.active_connections)
