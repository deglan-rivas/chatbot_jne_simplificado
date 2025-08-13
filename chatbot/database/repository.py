import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from chatbot.database.models import Conversacion, Base
from chatbot.database.connection import obtener_session_db, obtener_cliente_redis

class RepositorioConversaciones:
    """Repositorio para gestionar las conversaciones en PostgreSQL"""
    
    def __init__(self):
        self.db: Optional[Session] = None
    
    def __enter__(self):
        self.db = obtener_session_db()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()
    
    def guardar_conversacion(
        self,
        user_id: str,
        mensaje_entrada: str,
        mensaje_salida: str,
        numero_telefono: Optional[str] = None,
        usuario: Optional[str] = None,
        menu_principal: Optional[str] = None,
        canal: str = "telegram",
        flujo: Optional[Dict] = None,
        intent: Optional[str] = None,
        error: bool = False,
        mensaje_error: Optional[str] = None,
        duracion_procesamiento: Optional[int] = None
    ) -> Conversacion:
        """Guarda una nueva conversación en la base de datos"""
        try:
            fecha_hora_entrada = datetime.now()
            fecha_hora_salida = datetime.now()
            
            conversacion = Conversacion(
                user_id=user_id,
                numero_telefono=numero_telefono,
                usuario=usuario,
                mensaje_entrada=mensaje_entrada,
                mensaje_salida=mensaje_salida,
                fecha_hora_entrada=fecha_hora_entrada,
                fecha_hora_salida=fecha_hora_salida,
                menu_principal=menu_principal,
                canal=canal,
                flujo=json.dumps(flujo) if flujo else None,
                intent=intent,
                error=error,
                mensaje_error=mensaje_error,
                duracion_procesamiento=duracion_procesamiento
            )
            
            self.db.add(conversacion)
            self.db.commit()
            self.db.refresh(conversacion)
            
            return conversacion
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error al guardar conversación: {e}")
    
    def obtener_conversaciones_usuario(
        self, 
        user_id: str, 
        limite: int = 10
    ) -> List[Conversacion]:
        """Obtiene las últimas conversaciones de un usuario"""
        try:
            conversaciones = (
                self.db.query(Conversacion)
                .filter(Conversacion.user_id == user_id)
                .order_by(desc(Conversacion.fecha_hora_entrada))
                .limit(limite)
                .all()
            )
            return conversaciones
        except Exception as e:
            raise Exception(f"Error al obtener conversaciones: {e}")
    
    def obtener_estadisticas_abandono(self) -> Dict[str, Any]:
        """Obtiene estadísticas sobre el abandono de conversaciones"""
        try:
            # Conversaciones que terminaron en error
            errores = self.db.query(Conversacion).filter(Conversacion.error == True).count()
            
            # Total de conversaciones
            total = self.db.query(Conversacion).count()
            
            # Conversaciones por menú principal
            conversaciones_por_menu = (
                self.db.query(Conversacion.menu_principal, self.db.func.count(Conversacion.id))
                .filter(Conversacion.menu_principal.isnot(None))
                .group_by(Conversacion.menu_principal)
                .all()
            )
            
            return {
                "total_conversaciones": total,
                "conversaciones_con_error": errores,
                "tasa_abandono": (errores / total * 100) if total > 0 else 0,
                "conversaciones_por_menu": dict(conversaciones_por_menu)
            }
        except Exception as e:
            raise Exception(f"Error al obtener estadísticas: {e}")

class GestorChatMemory:
    """Gestor para el chat memory en Redis"""
    
    def __init__(self):
        self.redis = obtener_cliente_redis()
    
    def guardar_estado_usuario(
        self, 
        user_id: str, 
        estado: Dict[str, Any], 
        tiempo_expiracion: int = 3600
    ) -> bool:
        """Guarda el estado del usuario en Redis con tiempo de expiración"""
        try:
            clave = f"chatbot:usuario:{user_id}:estado"
            self.redis.setex(
                clave, 
                tiempo_expiracion, 
                json.dumps(estado, ensure_ascii=False)
            )
            return True
        except Exception as e:
            print(f"Error al guardar estado en Redis: {e}")
            return False
    
    def obtener_estado_usuario(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado del usuario desde Redis"""
        try:
            clave = f"chatbot:usuario:{user_id}:estado"
            estado_json = self.redis.get(clave)
            if estado_json:
                return json.loads(estado_json)
            return None
        except Exception as e:
            print(f"Error al obtener estado de Redis: {e}")
            return None
    
    def eliminar_estado_usuario(self, user_id: str) -> bool:
        """Elimina el estado del usuario de Redis"""
        try:
            clave = f"chatbot:usuario:{user_id}:estado"
            self.redis.delete(clave)
            return True
        except Exception as e:
            print(f"Error al eliminar estado de Redis: {e}")
            return False
    
    def guardar_historial_mensajes(
        self, 
        user_id: str, 
        mensaje: str, 
        es_usuario: bool = True,
        max_mensajes: int = 10
    ) -> bool:
        """Guarda mensajes en el historial del usuario"""
        try:
            clave = f"chatbot:usuario:{user_id}:historial"
            timestamp = datetime.now().isoformat()
            
            mensaje_data = {
                "texto": mensaje,
                "es_usuario": es_usuario,
                "timestamp": timestamp
            }
            
            # Agregar mensaje al inicio de la lista
            self.redis.lpush(clave, json.dumps(mensaje_data, ensure_ascii=False))
            
            # Mantener solo los últimos N mensajes
            self.redis.ltrim(clave, 0, max_mensajes - 1)
            
            # Establecer tiempo de expiración (1 hora)
            self.redis.expire(clave, 3600)
            
            return True
        except Exception as e:
            print(f"Error al guardar historial en Redis: {e}")
            return False
    
    def obtener_historial_mensajes(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtiene el historial de mensajes del usuario"""
        try:
            clave = f"chatbot:usuario:{user_id}:historial"
            mensajes_json = self.redis.lrange(clave, 0, -1)
            
            historial = []
            for mensaje_json in mensajes_json:
                historial.append(json.loads(mensaje_json))
            
            return historial
        except Exception as e:
            print(f"Error al obtener historial de Redis: {e}")
            return []
