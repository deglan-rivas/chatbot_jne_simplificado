from abc import ABC, abstractmethod
from typing import Dict, Any

class PlatformAdapter(ABC):
    """Interfaz base para adaptadores de plataforma"""
    
    @abstractmethod
    async def send_message(self, user_id: str, message: str) -> bool:
        """
        Envía mensaje al usuario en la plataforma
        
        Args:
            user_id: ID único del usuario
            message: Mensaje a enviar
        
        Returns:
            bool: True si se envió correctamente
        """
        pass
    
    @abstractmethod
    def normalize_input(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza input de la plataforma a formato estándar
        
        Args:
            raw_input: Input crudo de la plataforma
        
        Returns:
            dict: {
                "chat_id": str,
                "text": str,
                "metadata": dict (opcional)
            }
        """
        pass
