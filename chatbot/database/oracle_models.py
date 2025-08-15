from sqlalchemy import Column, String, Integer, DateTime, Text, Numeric
from chatbot.database.oracle_connection import OracleBase

class OrganizacionPolitica(OracleBase):
    """Modelo para la tabla CBOX_TBL_ORGANIZACION_POLITICA de Oracle"""
    __tablename__ = "CBOX_TBL_ORGANIZACION_POLITICA"
    __table_args__ = {'schema': 'ELECCIA'}
    
    # Columnas principales - tipos exactos de la BD
    COD_TIPO_OP = Column(String(2), primary_key=True, comment="Código del tipo de organización política")
    DES_TIPO = Column(String(40), comment="Descripción del tipo de organización política")
    FLG_ESTADO_OP = Column(Numeric(1, 0), comment="Flag de estado de la organización política (1 o 2)")
    ESTADO_OP = Column(String(200), comment="Descripción del estado de la organización política")
    
    def __repr__(self):
        return f"<OrganizacionPolitica(COD_TIPO_OP={self.COD_TIPO_OP}, DES_TIPO={self.DES_TIPO}, ESTADO_OP={self.ESTADO_OP})>"

class CronogramaElectoral(OracleBase):
    """Modelo para la tabla CBOX_TBL_TRF_CRONOGRAMA_ELECTORAL de Oracle"""
    __tablename__ = "CBOX_TBL_TRF_CRONOGRAMA_ELECTORAL"
    __table_args__ = {'schema': 'ELECCIA'}
    
    # Columnas principales - tipos exactos de la BD
    PROCESO_ELECTORAL = Column(String(200), primary_key=True, comment="Proceso electoral")
    ANIO = Column(Integer, comment="Año del hito electoral")
    MES = Column(String(200), comment="Mes del hito electoral")
    DIA = Column(Integer, comment="Día del hito electoral")
    HITO_ELECTORAL = Column(String(2000), comment="Descripción del hito electoral")
    
    def __repr__(self):
        return f"<CronogramaElectoral(PROCESO_ELECTORAL={self.PROCESO_ELECTORAL}, HITO_ELECTORAL={self.HITO_ELECTORAL[:50]}...)>"

class Politico(OracleBase):
    """Modelo para la tabla CBOX_TBL_IGOB_POLITICOS de Oracle"""
    __tablename__ = "CBOX_TBL_IGOB_POLITICOS"
    __table_args__ = {'schema': 'ELECCIA'}
    
    # Clave primaria
    IDPERSONA = Column(Integer, primary_key=True, comment="ID único de la persona")
    
    # Columnas principales - tipos exactos de la BD
    TXNOMBRE = Column(String(80), comment="Nombres del político")
    TXAPEPAT = Column(String(40), comment="Apellido paterno")
    TXAPEMAT = Column(String(40), comment="Apellido materno")
    TXREGION = Column(String(50), comment="Región")
    TXPROVINCIA = Column(String(50), comment="Provincia")
    TXDISTRITO = Column(String(50), comment="Distrito")
    TXORGPOL = Column(String(100), comment="Organización política")
    TXELECCION = Column(String(100), comment="Elección")
    TXSIGLAS = Column(String(24), comment="Siglas")
    TXTIPOELECCION = Column(String(100), comment="Tipo de elección")
    TXCARGO = Column(String(50), comment="Cargo postulado")
    TXCARGOELECTO = Column(String(60), comment="Cargo electo")
    
    def __repr__(self):
        return f"<Politico(IDPERSONA={self.IDPERSONA}, TXNOMBRE={self.TXNOMBRE}, TXAPEPAT={self.TXAPEPAT}, TXAPEMAT={self.TXAPEMAT})>"
