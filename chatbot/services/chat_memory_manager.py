import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from chatbot.database.repository import RepositorioConversaciones
from chatbot.database.connection import obtener_cliente_redis

class ChatMemoryManager:
    """
    Gestor de memoria de chat que mantiene conversaciones activas en Redis
    y las guarda en PostgreSQL cuando terminan.
    """
    
    def __init__(self):
        self.redis = obtener_cliente_redis()
        self.repositorio = RepositorioConversaciones()
        self.expiration_time = 1800  # 30 minutos en segundos
    
    def iniciar_conversacion(
        self, 
        user_id: str, 
        mensaje_inicial: str = "Inicio de conversación",
        numero_telefono: Optional[str] = None,
        usuario: Optional[str] = None
    ) -> bool:
        """
        Inicia una nueva conversación en Redis.
        
        Args:
            user_id: ID del usuario en Telegram
            mensaje_inicial: Primer mensaje de la conversación
            numero_telefono: Número de teléfono del usuario (opcional)
            usuario: Username del usuario (opcional)
        
        Returns:
            bool: True si se inició correctamente
        """
        try:
            # Crear estructura de conversación
            conversacion = {
                "user_id": user_id,
                "numero_telefono": numero_telefono,
                "usuario": usuario,
                "fecha_inicio": datetime.now().isoformat(),
                "mensajes": [],
                "estado_actual": {
                    "stage": "main",
                    "flow": [],
                    "menu_actual": "main"
                },
                "metadata": {
                    "num_mensajes": 0,
                    "ultima_actividad": datetime.now().isoformat()
                }
            }
            
            # Agregar mensaje inicial
            self._agregar_mensaje_a_conversacion(conversacion, "bot", mensaje_inicial)
            
            # Guardar en Redis con expiración
            clave = f"chatbot:conversacion:{user_id}"
            self.redis.setex(
                clave,
                self.expiration_time,
                json.dumps(conversacion, ensure_ascii=False, default=str)
            )
            
            print(f"✅ Conversación iniciada para usuario {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error al iniciar conversación: {e}")
            return False
    
    def obtener_conversacion_activa(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la conversación activa de un usuario desde Redis.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Dict: Conversación activa o None si no existe
        """
        try:
            clave = f"chatbot:conversacion:{user_id}"
            conversacion_json = self.redis.get(clave)
            
            if conversacion_json:
                conversacion = json.loads(conversacion_json)
                # Actualizar última actividad
                conversacion["metadata"]["ultima_actividad"] = datetime.now().isoformat()
                # Renovar expiración
                self.redis.expire(clave, self.expiration_time)
                return conversacion
            
            return None
            
        except Exception as e:
            print(f"❌ Error al obtener conversación: {e}")
            return None
    
    def agregar_mensaje_usuario(
        self, 
        user_id: str, 
        mensaje: str, 
        intent: Optional[str] = None
    ) -> bool:
        """
        Agrega un mensaje del usuario a la conversación activa.
        
        Args:
            user_id: ID del usuario
            mensaje: Mensaje del usuario
            intent: Intención detectada (opcional)
        
        Returns:
            bool: True si se agregó correctamente
        """
        try:
            conversacion = self.obtener_conversacion_activa(user_id)
            if not conversacion:
                return False
            
            # Agregar mensaje del usuario
            self._agregar_mensaje_a_conversacion(
                conversacion, 
                "usuario", 
                mensaje, 
                intent=intent
            )
            
            # Guardar conversación actualizada
            return self._guardar_conversacion_redis(user_id, conversacion)
            
        except Exception as e:
            print(f"❌ Error al agregar mensaje de usuario: {e}")
            return False
    
    def agregar_respuesta_bot(
        self, 
        user_id: str, 
        respuesta: str, 
        menu_actual: Optional[str] = None,
        estado_actual: Optional[Dict] = None
    ) -> bool:
        """
        Agrega una respuesta del bot a la conversación activa.
        
        Args:
            user_id: ID del usuario
            respuesta: Respuesta del bot
            menu_actual: Menú actual (opcional)
            estado_actual: Estado actual del flujo (opcional)
        
        Returns:
            bool: True si se agregó correctamente
        """
        try:
            conversacion = self.obtener_conversacion_activa(user_id)
            if not conversacion:
                return False
            
            # Agregar respuesta del bot
            self._agregar_mensaje_a_conversacion(
                conversacion, 
                "bot", 
                respuesta
            )
            
            # Actualizar estado si se proporciona
            if menu_actual:
                conversacion["estado_actual"]["menu_actual"] = menu_actual
            
            if estado_actual:
                conversacion["estado_actual"].update(estado_actual)
            
            # Guardar conversación actualizada
            return self._guardar_conversacion_redis(user_id, conversacion)
            
        except Exception as e:
            print(f"❌ Error al agregar respuesta del bot: {e}")
            return False
    
    def finalizar_conversacion(
        self, 
        user_id: str, 
        motivo: str = "Usuario finalizó conversación",
        error: bool = False,
        mensaje_error: Optional[str] = None
    ) -> bool:
        """
        Finaliza una conversación y la guarda en PostgreSQL.
        
        Args:
            user_id: ID del usuario
            motivo: Motivo de finalización
            error: Indica si hubo error
            mensaje_error: Descripción del error
        
        Returns:
            bool: True si se finalizó correctamente
        """
        try:
            conversacion = self.obtener_conversacion_activa(user_id)
            if not conversacion:
                return False
            
            # Calcular duración total
            fecha_inicio = datetime.fromisoformat(conversacion["fecha_inicio"])
            fecha_fin = datetime.now()
            duracion_total = int((fecha_fin - fecha_inicio).total_seconds())
            
            # Completar conversación
            conversacion["fecha_fin"] = fecha_fin.isoformat()
            conversacion["motivo_finalizacion"] = motivo
            conversacion["metadata"]["duracion_total"] = duracion_total
            conversacion["metadata"]["num_mensajes"] = len(conversacion["mensajes"])
            
            # Guardar en PostgreSQL
            with self.repositorio as repo:
                conversacion_db = repo.guardar_conversacion_completa(
                    user_id=conversacion["user_id"],
                    numero_telefono=conversacion["numero_telefono"],
                    usuario=conversacion["usuario"],
                    flujo=conversacion,
                    canal="telegram",
                    error=error,
                    mensaje_error=mensaje_error,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    duracion_total=duracion_total,
                    num_mensajes=len(conversacion["mensajes"])
                )
            
            # Eliminar de Redis
            clave = f"chatbot:conversacion:{user_id}"
            self.redis.delete(clave)
            
            print(f"✅ Conversación finalizada y guardada - ID: {conversacion_db.id}")
            return True
            
        except Exception as e:
            print(f"❌ Error al finalizar conversación: {e}")
            return False
    
    def verificar_expiracion_conversaciones(self) -> List[str]:
        """
        Verifica y finaliza conversaciones expiradas.
        
        Returns:
            List: Lista de IDs de usuarios con conversaciones expiradas
        """
        try:
            # Buscar conversaciones que están por expirar
            pattern = "chatbot:conversacion:*"
            claves = self.redis.keys(pattern)
            usuarios_expirados = []
            
            for clave in claves:
                user_id = clave.split(":")[-1]
                ttl = self.redis.ttl(clave)
                
                # Si expira en menos de 5 minutos, finalizar
                if ttl < 300:  # 5 minutos
                    self.finalizar_conversacion(
                        user_id, 
                        motivo="Conversación expirada por inactividad"
                    )
                    usuarios_expirados.append(user_id)
            
            return usuarios_expirados
            
        except Exception as e:
            print(f"❌ Error al verificar expiración: {e}")
            return []
    
    def _agregar_mensaje_a_conversacion(
        self, 
        conversacion: Dict[str, Any], 
        tipo: str, 
        contenido: str, 
        intent: Optional[str] = None
    ):
        """Agrega un mensaje a la conversación."""
        mensaje = {
            "tipo": tipo,  # "usuario" o "bot"
            "contenido": contenido,
            "timestamp": datetime.now().isoformat(),
            "intent": intent
        }
        
        conversacion["mensajes"].append(mensaje)
        conversacion["metadata"]["num_mensajes"] = len(conversacion["mensajes"])
        conversacion["metadata"]["ultima_actividad"] = datetime.now().isoformat()
    
    def _guardar_conversacion_redis(self, user_id: str, conversacion: Dict[str, Any]) -> bool:
        """Guarda la conversación en Redis."""
        try:
            clave = f"chatbot:conversacion:{user_id}"
            self.redis.setex(
                clave,
                self.expiration_time,
                json.dumps(conversacion, ensure_ascii=False, default=str)
            )
            return True
        except Exception as e:
            print(f"❌ Error al guardar en Redis: {e}")
            return False
    
    def obtener_estadisticas_conversaciones_activas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de las conversaciones activas.
        
        Returns:
            Dict: Estadísticas de conversaciones activas
        """
        try:
            pattern = "chatbot:conversacion:*"
            claves = self.redis.keys(pattern)
            
            total_conversaciones = len(claves)
            total_mensajes = 0
            
            for clave in claves:
                conversacion_json = self.redis.get(clave)
                if conversacion_json:
                    conversacion = json.loads(conversacion_json)
                    total_mensajes += conversacion["metadata"]["num_mensajes"]
            
            return {
                "conversaciones_activas": total_conversaciones,
                "total_mensajes": total_mensajes,
                "promedio_mensajes": total_mensajes / total_conversaciones if total_conversaciones > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Error al obtener estadísticas: {e}")
            return {}
