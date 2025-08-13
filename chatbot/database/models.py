from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Conversacion(Base):
    """Modelo para almacenar el registro de conversaciones del chatbot"""
    __tablename__ = "conversaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True, comment="ID del usuario")    
    numero_telefono = Column(String(20), nullable=True, comment="Número de teléfono del usuario")
    usuario = Column(String(100), nullable=True, comment="Username del usuario")    
    mensaje_entrada = Column(Text, nullable=False, comment="Mensaje que envió el usuario")
    mensaje_salida = Column(Text, nullable=False, comment="Respuesta del chatbot")    
    fecha_hora_entrada = Column(DateTime, default=func.now(), nullable=False, comment="Fecha y hora del mensaje de entrada")
    fecha_hora_salida = Column(DateTime, default=func.now(), nullable=False, comment="Fecha y hora del mensaje de salida")    
    menu_principal = Column(String(50), nullable=True, comment="Menú principal donde se encuentra el usuario")
    canal = Column(String(20), default="telegram", nullable=False, comment="Canal de comunicación (telegram, etc.)")
    flujo = Column(Text, nullable=True, comment="Estado del flujo de conversación (JSON)")    
    error = Column(Boolean, default=False, nullable=False, comment="Indica si hubo error en la conversación")
    mensaje_error = Column(Text, nullable=True, comment="Descripción del error si ocurrió")    
    intent = Column(String(100), nullable=True, comment="Intención detectada del mensaje")
    duracion_procesamiento = Column(Integer, nullable=True, comment="Tiempo de procesamiento en milisegundos")
    
    def __repr__(self):
        return f"<Conversacion(id={self.id}, user_id={self.user_id}, fecha={self.fecha_hora_entrada})>"
