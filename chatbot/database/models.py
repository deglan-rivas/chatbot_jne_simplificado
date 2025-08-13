from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Conversacion(Base):
    """Modelo para almacenar el historial completo de conversaciones del chatbot"""
    __tablename__ = "conversaciones"
    
    # Identificadores
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True, comment="ID del usuario en Telegram")
    
    # Información del usuario
    numero_telefono = Column(String(20), nullable=True, comment="Número de teléfono del usuario")
    usuario = Column(String(100), nullable=True, comment="Username del usuario en Telegram")
    
    # Flujo completo de la conversación (JSON)
    flujo = Column(Text, nullable=False, comment="Conversación completa con mensajes, menús y estado")
    
    # Timestamps
    fecha_inicio = Column(DateTime, default=func.now(), nullable=False, comment="Fecha y hora de inicio de la conversación")
    fecha_fin = Column(DateTime, nullable=True, comment="Fecha y hora de finalización de la conversación")
    
    # Contexto de la conversación
    canal = Column(String(20), default="telegram", nullable=False, comment="Canal de comunicación (telegram, etc.)")
    
    # Control de errores
    error = Column(Boolean, default=False, nullable=False, comment="Indica si hubo error en la conversación")
    mensaje_error = Column(Text, nullable=True, comment="Descripción del error si ocurrió")
    
    # Metadatos adicionales
    duracion_total = Column(Integer, nullable=True, comment="Duración total de la conversación en segundos")
    num_mensajes = Column(Integer, nullable=True, comment="Número total de mensajes en la conversación")
    
    def __repr__(self):
        return f"<Conversacion(id={self.id}, user_id={self.user_id}, fecha_inicio={self.fecha_inicio})>"
