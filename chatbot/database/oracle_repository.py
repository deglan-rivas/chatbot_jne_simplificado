from sqlalchemy import func
from chatbot.database.oracle_connection import get_db
from chatbot.database.oracle_models import OrganizacionPolitica, CronogramaElectoral, Politico
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class OracleRepository:
    """Repositorio para consultas a Oracle Database usando modelos SQLAlchemy"""
    
    def obtener_estadisticas_organizaciones_politicas(self) -> dict:
        """
        Obtiene estadísticas de organizaciones políticas usando el modelo SQLAlchemy
        """
        try:
            # Usar la nueva función get_db() para obtener la sesión
            for session in get_db():
                # Usar el modelo SQLAlchemy para la consulta
                result = session.query(
                    OrganizacionPolitica.COD_TIPO_OP,
                    OrganizacionPolitica.DES_TIPO,
                    OrganizacionPolitica.FLG_ESTADO_OP,
                    OrganizacionPolitica.ESTADO_OP,
                    func.count(OrganizacionPolitica.COD_TIPO_OP).label('cantidad')
                ).group_by(
                    OrganizacionPolitica.COD_TIPO_OP,
                    OrganizacionPolitica.DES_TIPO,
                    OrganizacionPolitica.FLG_ESTADO_OP,
                    OrganizacionPolitica.ESTADO_OP
                ).order_by(
                    OrganizacionPolitica.COD_TIPO_OP,
                    OrganizacionPolitica.FLG_ESTADO_OP
                ).all()
                
                # Procesar resultados
                estadisticas = {}
                
                for row in result:
                    cod_tipo = row.COD_TIPO_OP
                    des_tipo = row.DES_TIPO
                    flg_estado = row.FLG_ESTADO_OP
                    estado_op = row.ESTADO_OP
                    cantidad = row.cantidad
                    
                    if cod_tipo not in estadisticas:
                        estadisticas[cod_tipo] = {
                            "descripcion": des_tipo,
                            "inscritos": 0,
                            "en_proceso": 0
                        }
                    
                    if flg_estado == 2:  # Inscrito
                        estadisticas[cod_tipo]["inscritos"] = cantidad
                    elif flg_estado == 1:  # En proceso
                        estadisticas[cod_tipo]["en_proceso"] = cantidad
                
                logger.info("✅ Estadísticas de organizaciones políticas obtenidas exitosamente")
                return estadisticas
                
        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas de organizaciones políticas: {e}")
            return {}
                
    def generar_reporte_organizaciones_politicas(self) -> str:
        """
        Genera el reporte de organizaciones políticas con formato específico
        """
        try:
            estadisticas = self.obtener_estadisticas_organizaciones_politicas()
            
            if not estadisticas:
                return "No se pudo obtener información de organizaciones políticas en este momento."
            
            # Obtener fecha actual
            fecha_actual = datetime.now().strftime("%d/%m/%Y")
            
            # Generar reporte usando los datos de la base de datos
            reporte = f"""📊 **Registro de Organizaciones Políticas**
        
        A la fecha {fecha_actual}, el Registro de Organizaciones Políticas presenta el siguiente detalle:"""
            
            for cod_tipo, datos in estadisticas.items():
                descripcion = datos["descripcion"]
                inscritos = datos["inscritos"]
                en_proceso = datos["en_proceso"]
                
                reporte += f"\n\n• **{descripcion}**: Inscritos {inscritos} y en proceso de inscripción {en_proceso}"
            
            reporte += "\n\n🔗 **Más Información**: https://sroppublico.jne.gob.pe/Consulta/OrganizacionPolitica"
            
            return reporte
            
        except Exception as e:
            logger.error(f"❌ Error al generar reporte de organizaciones políticas: {e}")
            return "Error al generar el reporte de organizaciones políticas."
    
    def obtener_enlace_consulta_afiliacion(self) -> str:
        """
        Retorna el enlace para consulta de afiliación
        """
        return """🔍 **Consulta de Afiliación**
        
        Para consultar tu afiliación a organizaciones políticas, visita:
        
        🔗 **Portal de Consulta de Afiliación:**
        https://sroppublico.jne.gob.pe/Consulta/Afiliado
        
        En este portal podrás:
        • Verificar tu afiliación actual
        • Consultar historial de afiliaciones
        • Ver estado de tu membresía
        • Acceder a certificados de afiliación"""
    
    def obtener_procesos_electorales(self) -> list:
        """
        Obtiene la lista de procesos electorales disponibles
        """
        try:
            for session in get_db():
                result = session.query(
                    CronogramaElectoral.PROCESO_ELECTORAL
                ).distinct().all()
                
                procesos = [row.PROCESO_ELECTORAL for row in result]
                logger.info(f"✅ Procesos electorales obtenidos: {len(procesos)} procesos")
                return procesos
                
        except Exception as e:
            logger.error(f"❌ Error al obtener procesos electorales: {e}")
            return []
    
    def buscar_hitos_electorales(self, proceso_electoral: str, consulta: str) -> list:
        """
        Busca hitos electorales por proceso electoral y consulta del usuario
        """
        try:
            for session in get_db():
                # Buscar hitos que contengan la consulta del usuario
                result = session.query(CronogramaElectoral).filter(
                    CronogramaElectoral.PROCESO_ELECTORAL == proceso_electoral,
                    CronogramaElectoral.HITO_ELECTORAL.ilike(f"%{consulta}%")
                ).order_by(
                    CronogramaElectoral.ANIO,
                    CronogramaElectoral.MES,
                    CronogramaElectoral.DIA
                ).all()
                
                hitos = []
                for row in result:
                    hitos.append({
                        "proceso_electoral": row.PROCESO_ELECTORAL,
                        "anio": row.ANIO,
                        "mes": row.MES,
                        "dia": row.DIA,
                        "hito_electoral": row.HITO_ELECTORAL
                    })
                
                logger.info(f"✅ Hitos electorales encontrados: {len(hitos)} hitos")
                return hitos
                
        except Exception as e:
            logger.error(f"❌ Error al buscar hitos electorales: {e}")
            return []
    
    def buscar_politicos(self, nombres: str, apellidos: str = "") -> list:
        """
        Busca políticos por nombres y apellidos
        """
        try:
            for session in get_db():
                query = session.query(Politico)
                
                # Filtrar por nombres
                if nombres:
                    query = query.filter(Politico.TXNOMBRE.ilike(f"%{nombres}%"))
                
                # Filtrar por apellidos si se proporcionan
                if apellidos:
                    # Buscar en apellido paterno o materno
                    query = query.filter(
                        (Politico.TXAPEPAT.ilike(f"%{apellidos}%")) |
                        (Politico.TXAPEMAT.ilike(f"%{apellidos}%"))
                    )
                
                result = query.all()
                
                politicos = []
                for row in result:
                    politicos.append({
                        "nombres": row.TXNOMBRE,
                        "apellido_paterno": row.TXAPEPAT,
                        "apellido_materno": row.TXAPEMAT,
                        "region": row.TXREGION,
                        "provincia": row.TXPROVINCIA,
                        "distrito": row.TXDISTRITO,
                        "organizacion_politica": row.TXORGPOL,
                        "eleccion": row.TXELECCION,
                        "siglas": row.TXSIGLAS,
                        "tipo_eleccion": row.TXTIPOELECCION,
                        "cargo_postulado": row.TXCARGO,
                        "cargo_electo": row.TXCARGOELECTO
                    })
                
                logger.info(f"✅ Políticos encontrados: {len(politicos)} políticos")
                return politicos
                
        except Exception as e:
            logger.error(f"❌ Error al buscar políticos: {e}")
            return []
    
    def probar_conexion(self) -> bool:
        """
        Prueba la conexión a Oracle usando el modelo
        """
        try:
            # Usar la nueva función get_db() para obtener la sesión
            for session in get_db():
                # Usar el modelo para contar registros
                count = session.query(OrganizacionPolitica).count()
                logger.info(f"✅ Conexión a Oracle exitosa. Registros en tabla: {count}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error al probar conexión a Oracle: {e}")
            return False
