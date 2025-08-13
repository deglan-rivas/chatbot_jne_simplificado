import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
from chatbot.database.repository import RepositorioConversaciones

class ConversationLogger:
    """
    Clase para gestionar el logging de conversaciones en PostgreSQL.
    Mantiene la lógica separada del flujo principal del chatbot.
    """
    
    def __init__(self):
        self.repositorio = RepositorioConversaciones()
    
    def log_conversation(
        self,
        user_id: str,
        mensaje_entrada: str,
        mensaje_salida: str,
        numero_telefono: Optional[str] = None,
        usuario: Optional[str] = None,
        menu_principal: Optional[str] = None,
        canal: str = "telegram",
        flujo: Optional[Dict[str, Any]] = None,
        intent: Optional[str] = None,
        error: bool = False,
        mensaje_error: Optional[str] = None
    ) -> bool:
        """
        Registra una conversación en la base de datos PostgreSQL.
        
        Args:
            user_id: ID del usuario en Telegram
            mensaje_entrada: Mensaje que envió el usuario
            mensaje_salida: Respuesta del chatbot
            numero_telefono: Número de teléfono del usuario (opcional)
            usuario: Username del usuario (opcional)
            menu_principal: Menú donde se encuentra el usuario (opcional)
            canal: Canal de comunicación (default: "telegram")
            flujo: Estado del flujo de conversación (opcional)
            intent: Intención detectada del mensaje (opcional)
            error: Indica si hubo error en la conversación (default: False)
            mensaje_error: Descripción del error si ocurrió (opcional)
        
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        try:
            # Calcular duración de procesamiento si es necesario
            duracion_procesamiento = None
            
            # Guardar la conversación usando el repositorio
            with self.repositorio as repo:
                conversacion = repo.guardar_conversacion(
                    user_id=user_id,
                    mensaje_entrada=mensaje_entrada,
                    mensaje_salida=mensaje_salida,
                    numero_telefono=numero_telefono,
                    usuario=usuario,
                    menu_principal=menu_principal,
                    canal=canal,
                    flujo=flujo,
                    intent=intent,
                    error=error,
                    mensaje_error=mensaje_error,
                    duracion_procesamiento=duracion_procesamiento
                )
                
                print(f"Conversación registrada exitosamente - ID: {conversacion.id}")
                return True
                
        except Exception as e:
            print(f"Error al registrar conversación: {e}")
            return False
    
    def log_successful_conversation(
        self,
        user_id: str,
        mensaje_entrada: str,
        mensaje_salida: str,
        numero_telefono: Optional[str] = None,
        usuario: Optional[str] = None,
        menu_principal: Optional[str] = None,
        flujo: Optional[Dict[str, Any]] = None,
        intent: Optional[str] = None
    ) -> bool:
        """
        Registra una conversación exitosa (sin errores).
        
        Args:
            user_id: ID del usuario en Telegram
            mensaje_entrada: Mensaje que envió el usuario
            mensaje_salida: Respuesta del chatbot
            numero_telefono: Número de teléfono del usuario (opcional)
            usuario: Username del usuario (opcional)
            menu_principal: Menú donde se encuentra el usuario (opcional)
            flujo: Estado del flujo de conversación (opcional)
            intent: Intención detectada del mensaje (opcional)
        
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        return self.log_conversation(
            user_id=user_id,
            mensaje_entrada=mensaje_entrada,
            mensaje_salida=mensaje_salida,
            numero_telefono=numero_telefono,
            usuario=usuario,
            menu_principal=menu_principal,
            canal="telegram",
            flujo=flujo,
            intent=intent,
            error=False,
            mensaje_error=None
        )
    
    def log_error_conversation(
        self,
        user_id: str,
        mensaje_entrada: str,
        mensaje_salida: str,
        mensaje_error: str,
        numero_telefono: Optional[str] = None,
        usuario: Optional[str] = None,
        menu_principal: Optional[str] = None,
        flujo: Optional[Dict[str, Any]] = None,
        intent: Optional[str] = None
    ) -> bool:
        """
        Registra una conversación con error.
        
        Args:
            user_id: ID del usuario en Telegram
            mensaje_entrada: Mensaje que envió el usuario
            mensaje_salida: Respuesta del chatbot (puede ser mensaje de error)
            mensaje_error: Descripción del error que ocurrió
            numero_telefono: Número de teléfono del usuario (opcional)
            usuario: Username del usuario (opcional)
            menu_principal: Menú donde se encuentra el usuario (opcional)
            flujo: Estado del flujo de conversación (opcional)
            intent: Intención detectada del mensaje (opcional)
        
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        return self.log_conversation(
            user_id=user_id,
            mensaje_entrada=mensaje_entrada,
            mensaje_salida=mensaje_salida,
            numero_telefono=numero_telefono,
            usuario=usuario,
            menu_principal=menu_principal,
            canal="telegram",
            flujo=flujo,
            intent=intent,
            error=True,
            mensaje_error=mensaje_error
        )
    
    def log_menu_navigation(
        self,
        user_id: str,
        mensaje_entrada: str,
        mensaje_salida: str,
        menu_principal: str,
        numero_telefono: Optional[str] = None,
        usuario: Optional[str] = None,
        flujo: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Registra la navegación entre menús del chatbot.
        
        Args:
            user_id: ID del usuario en Telegram
            mensaje_entrada: Opción seleccionada por el usuario
            mensaje_salida: Respuesta del chatbot (nuevo menú)
            menu_principal: Menú al que navegó el usuario
            numero_telefono: Número de teléfono del usuario (opcional)
            usuario: Username del usuario (opcional)
            flujo: Estado del flujo de conversación (opcional)
        
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        return self.log_conversation(
            user_id=user_id,
            mensaje_entrada=mensaje_entrada,
            mensaje_salida=mensaje_salida,
            numero_telefono=numero_telefono,
            usuario=usuario,
            menu_principal=menu_principal,
            canal="telegram",
            flujo=flujo,
            intent="navegacion_menu",
            error=False,
            mensaje_error=None
        )
    
    def log_question_answer(
        self,
        user_id: str,
        mensaje_entrada: str,
        mensaje_salida: str,
        menu_principal: str,
        intent: str,
        numero_telefono: Optional[str] = None,
        usuario: Optional[str] = None,
        flujo: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Registra una pregunta y respuesta del usuario.
        
        Args:
            user_id: ID del usuario en Telegram
            mensaje_entrada: Pregunta del usuario
            mensaje_salida: Respuesta del chatbot
            menu_principal: Menú donde se hizo la pregunta
            intent: Intención detectada de la pregunta
            numero_telefono: Número de teléfono del usuario (opcional)
            usuario: Username del usuario (opcional)
            flujo: Estado del flujo de conversación (opcional)
        
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        return self.log_conversation(
            user_id=user_id,
            mensaje_entrada=mensaje_entrada,
            mensaje_salida=mensaje_salida,
            numero_telefono=numero_telefono,
            usuario=usuario,
            menu_principal=menu_principal,
            canal="telegram",
            flujo=flujo,
            intent=intent,
            error=False,
            mensaje_error=None
        )
    
    def get_user_conversation_history(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> list:
        """
        Obtiene el historial de conversaciones de un usuario.
        
        Args:
            user_id: ID del usuario en Telegram
            limit: Número máximo de conversaciones a obtener
        
        Returns:
            list: Lista de conversaciones del usuario
        """
        try:
            with self.repositorio as repo:
                conversaciones = repo.obtener_conversaciones_usuario(user_id, limit)
                return conversaciones
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return []
    
    def get_abandonment_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre el abandono de conversaciones.
        
        Returns:
            Dict: Estadísticas de abandono
        """
        try:
            with self.repositorio as repo:
                estadisticas = repo.obtener_estadisticas_abandono()
                return estadisticas
        except Exception as e:
            print(f" Error al obtener estadísticas: {e}")
            return {}
