from sqlalchemy import func
from chatbot.database.oracle_connection import get_db
from chatbot.database.oracle_models import OrganizacionPolitica, CronogramaElectoral, Politico
from datetime import datetime
import logging
import unicodedata

logger = logging.getLogger(__name__)

def eliminar_tildes(texto: str) -> str:
    """
    Elimina tildes y caracteres especiales de un texto
    """
    if not texto:
        return texto
    
    # Normalizar caracteres Unicode (NFD) y eliminar diacríticos
    texto_normalizado = unicodedata.normalize('NFD', texto)
    # Filtrar solo caracteres sin diacríticos
    texto_sin_tildes = ''.join(c for c in texto_normalizado if not unicodedata.combining(c))
    return texto_sin_tildes

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
        
        A la fecha 14/08/2025, el Registro de Organizaciones Políticas presenta el siguiente detalle:"""
            
            for cod_tipo, datos in estadisticas.items():
                descripcion = datos["descripcion"]
                inscritos = datos["inscritos"]
                en_proceso = datos["en_proceso"]
                
                reporte += f"\n\n• **{descripcion}**: Inscritos {inscritos} y en proceso de inscripción {en_proceso}"
            
            reporte += "\n\n🔗 **Más Información**: <a href=\"https://sroppublico.jne.gob.pe/Consulta/OrganizacionPolitica\">https://sroppublico.jne.gob.pe/Consulta/OrganizacionPolitica</a>"
            
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
        <a href="https://sroppublico.jne.gob.pe/Consulta/Afiliado">https://sroppublico.jne.gob.pe/Consulta/Afiliado</a>
        
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
    
    def obtener_hitos_electorales_por_proceso(self, proceso_electoral: str) -> list:
        """
        Obtiene todos los hitos electorales de un proceso específico
        """
        try:
            for session in get_db():
                result = session.query(CronogramaElectoral).filter(
                    CronogramaElectoral.PROCESO_ELECTORAL == proceso_electoral
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
                
                logger.info(f"✅ Hitos electorales obtenidos para {proceso_electoral}: {len(hitos)} hitos")
                return hitos
                
        except Exception as e:
            logger.error(f"❌ Error al obtener hitos electorales: {e}")
            return []
    
    def buscar_hitos_electorales(self, proceso_electoral: str, consulta: str) -> list:
        """
        Busca hitos electorales por proceso electoral y consulta del usuario
        (Método legacy - mantenido por compatibilidad)
        """
        try:
            for session in get_db():
                # Obtener TODOS los hitos del proceso electoral (sin filtro de texto)
                result = session.query(CronogramaElectoral).filter(
                    CronogramaElectoral.PROCESO_ELECTORAL == proceso_electoral
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
                
                logger.info(f"✅ Hitos electorales obtenidos para {proceso_electoral}: {len(hitos)} hitos")
                return hitos
                
        except Exception as e:
            logger.error(f"❌ Error al buscar hitos electorales: {e}")
            return []
    
    def obtener_todos_hitos_por_proceso(self, proceso_electoral: str) -> list:
        """
        Obtiene TODOS los hitos electorales de un proceso específico (sin filtro de texto)
        Para uso en búsqueda semántica
        """
        try:
            for session in get_db():
                # Obtener TODOS los hitos del proceso electoral (sin filtro de texto)
                result = session.query(CronogramaElectoral).filter(
                    CronogramaElectoral.PROCESO_ELECTORAL == proceso_electoral
                ).order_by(
                    CronogramaElectoral.ANIO,
                    CronogramaElectoral.MES,
                    CronogramaElectoral.DIA
                ).all()
                
                hitos = []
                for i, row in enumerate(result):
                    # Intentar obtener ID si existe, sino usar índice
                    try:
                        id_valor = row.ID if hasattr(row, 'ID') else i
                    except:
                        id_valor = i
                    
                    hitos.append({
                        "id": id_valor,
                        "proceso_electoral": row.PROCESO_ELECTORAL,
                        "anio": row.ANIO,
                        "mes": row.MES,
                        "dia": row.DIA,
                        "hito_electoral": row.HITO_ELECTORAL
                    })
                
                return hitos
                
        except Exception as e:
            logger.error(f"❌ Error al obtener todos los hitos por proceso: {e}")
            return []
    
    def buscar_politicos(self, nombres: str, apellidos: str = "") -> list:
        """
        Busca políticos por nombres y apellidos
        """
        try:
            for session in get_db():
                query = session.query(Politico)
                
                # Filtrar por nombres (eliminando tildes)
                if nombres:
                    nombres_sin_tildes = eliminar_tildes(nombres)
                    query = query.filter(Politico.TXNOMBRE.ilike(f"%{nombres_sin_tildes}%"))
                
                # Filtrar por apellidos si se proporcionan (eliminando tildes)
                if apellidos:
                    apellidos_sin_tildes = eliminar_tildes(apellidos)
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
    
    def obtener_elecciones_disponibles(self) -> list:
        """
        Obtiene la lista de elecciones disponibles para consulta de políticos
        """
        try:
            for session in get_db():
                result = session.query(
                    Politico.TXELECCION
                ).distinct().order_by(Politico.TXELECCION).all()
                
                elecciones = [row.TXELECCION for row in result if row.TXELECCION]
                logger.info(f"✅ Elecciones disponibles obtenidas: {len(elecciones)} elecciones")
                return elecciones
                
        except Exception as e:
            logger.error(f"❌ Error al obtener elecciones disponibles: {e}")
            return []
    
    def buscar_politicos_por_eleccion(self, eleccion: str, nombres: str = "", apellidos: str = "") -> list:
        """
        Busca políticos por elección específica y opcionalmente por nombres/apellidos
        """
        try:
            for session in get_db():
                query = session.query(Politico).filter(
                    Politico.TXELECCION == eleccion
                )
                
                # Filtrar por nombres si se proporcionan
                if nombres:
                    query = query.filter(Politico.TXNOMBRE.ilike(f"%{nombres}%"))
                
                # Filtrar por apellidos si se proporcionan
                if apellidos:
                    query = query.filter(
                        (Politico.TXAPEPAT.ilike(f"%{apellidos}%")) |
                        (Politico.TXAPEMAT.ilike(f"%{apellidos}%"))
                    )
                
                result = query.order_by(
                    Politico.TXNOMBRE,
                    Politico.TXAPEPAT,
                    Politico.TXAPEMAT
                ).all()
                
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
                
                logger.info(f"✅ Políticos encontrados por elección: {len(politicos)} políticos")
                return politicos
                
        except Exception as e:
            logger.error(f"❌ Error al buscar políticos por elección: {e}")
            return []
    
    def buscar_candidatos_unicos(self, nombres: str, apellidos: str = "") -> list:
        """
        Busca candidatos únicos por nombres y apellidos (sin repetir nombres)
        """
        try:
            for session in get_db():
                query = session.query(Politico)
                
                # Filtrar por nombres (eliminando tildes)
                if nombres:
                    nombres_sin_tildes = eliminar_tildes(nombres)
                    query = query.filter(Politico.TXNOMBRE.ilike(f"%{nombres_sin_tildes}%"))
                
                # Filtrar por apellidos si se proporcionan (eliminando tildes)
                if apellidos:
                    apellidos_sin_tildes = eliminar_tildes(apellidos)
                    query = query.filter(
                        (Politico.TXAPEPAT.ilike(f"%{apellidos_sin_tildes}%")) |
                        (Politico.TXAPEMAT.ilike(f"%{apellidos_sin_tildes}%"))
                    )
                
                # Obtener candidatos únicos (sin repetir nombres completos)
                result = session.query(
                    Politico.TXNOMBRE,
                    Politico.TXAPEPAT,
                    Politico.TXAPEMAT
                ).filter(
                    query.whereclause
                ).distinct().order_by(
                    Politico.TXNOMBRE,
                    Politico.TXAPEPAT,
                    Politico.TXAPEMAT
                ).all()
                
                candidatos = []
                for row in result:
                    candidatos.append({
                        "nombres": row.TXNOMBRE,
                        "apellido_paterno": row.TXAPEPAT,
                        "apellido_materno": row.TXAPEMAT,
                        "nombre_completo": f"{row.TXNOMBRE} {row.TXAPEPAT} {row.TXAPEMAT}".strip()
                    })
                
                logger.info(f"✅ Candidatos únicos encontrados: {len(candidatos)} candidatos")
                return candidatos
                
        except Exception as e:
            logger.error(f"❌ Error al buscar candidatos únicos: {e}")
            return []
    
    def buscar_candidatos_por_apellidos_separados(self, nombres: str, apellido_paterno: str, apellido_materno: str) -> list:
        """
        Busca candidatos por nombres, apellido paterno y materno por separado
        """
        try:
            for session in get_db():
                query = session.query(Politico)
                
                # Filtrar por nombres (eliminando tildes)
                if nombres:
                    nombres_sin_tildes = eliminar_tildes(nombres)
                    query = query.filter(Politico.TXNOMBRE.ilike(f"%{nombres_sin_tildes}%"))
                
                # Filtrar por apellido paterno (eliminando tildes)
                if apellido_paterno:
                    apellido_paterno_sin_tildes = eliminar_tildes(apellido_paterno)
                    query = query.filter(Politico.TXAPEPAT.ilike(f"%{apellido_paterno_sin_tildes}%"))
                
                # Filtrar por apellido materno (eliminando tildes)
                if apellido_materno:
                    apellido_materno_sin_tildes = eliminar_tildes(apellido_materno)
                    query = query.filter(Politico.TXAPEMAT.ilike(f"%{apellido_materno_sin_tildes}%"))
                
                # Obtener candidatos únicos (sin repetir nombres completos)
                result = session.query(
                    Politico.TXNOMBRE,
                    Politico.TXAPEPAT,
                    Politico.TXAPEMAT
                ).filter(
                    query.whereclause
                ).distinct().order_by(
                    Politico.TXNOMBRE,
                    Politico.TXAPEPAT,
                    Politico.TXAPEMAT
                ).all()
                
                candidatos = []
                for row in result:
                    candidatos.append({
                        "nombres": row.TXNOMBRE,
                        "apellido_paterno": row.TXAPEPAT,
                        "apellido_materno": row.TXAPEMAT,
                        "nombre_completo": f"{row.TXNOMBRE} {row.TXAPEPAT} {row.TXAPEMAT}".strip()
                    })
                
                logger.info(f"✅ Candidatos encontrados por apellidos separados: {len(candidatos)} candidatos")
                return candidatos
                
        except Exception as e:
            logger.error(f"❌ Error al buscar candidatos por apellidos separados: {e}")
            return []
    
    def obtener_elecciones_por_candidato(self, nombres: str, apellido_paterno: str, apellido_materno: str) -> list:
        """
        Obtiene todas las elecciones donde aparece un candidato específico
        """
        try:
            for session in get_db():
                result = session.query(
                    Politico.TXELECCION
                ).filter(
                    Politico.TXNOMBRE == nombres,
                    Politico.TXAPEPAT == apellido_paterno,
                    Politico.TXAPEMAT == apellido_materno
                ).distinct().order_by(Politico.TXELECCION).all()
                
                elecciones = [row.TXELECCION for row in result if row.TXELECCION]
                logger.info(f"✅ Elecciones encontradas para candidato: {len(elecciones)} elecciones")
                return elecciones
                
        except Exception as e:
            logger.error(f"❌ Error al obtener elecciones por candidato: {e}")
            return []
    
    def obtener_detalle_candidato_eleccion(self, nombres: str, apellido_paterno: str, apellido_materno: str, eleccion: str) -> dict:
        """
        Obtiene el detalle completo de un candidato en una elección específica
        """
        try:
            for session in get_db():
                result = session.query(Politico).filter(
                    Politico.TXNOMBRE == nombres,
                    Politico.TXAPEPAT == apellido_paterno,
                    Politico.TXAPEMAT == apellido_materno,
                    Politico.TXELECCION == eleccion
                ).first()
                
                if result:
                    detalle = {
                        "nombres": result.TXNOMBRE,
                        "apellido_paterno": result.TXAPEPAT,
                        "apellido_materno": result.TXAPEMAT,
                        "region": result.TXREGION,
                        "provincia": result.TXPROVINCIA,
                        "distrito": result.TXDISTRITO,
                        "organizacion_politica": result.TXORGPOL,
                        "eleccion": result.TXELECCION,
                        "siglas": result.TXSIGLAS,
                        "tipo_eleccion": result.TXTIPOELECCION,
                        "cargo_postulado": result.TXCARGO,
                        "cargo_electo": result.TXCARGOELECTO
                    }
                    
                    logger.info(f"✅ Detalle de candidato obtenido para {eleccion}")
                    return detalle
                else:
                    logger.warning(f"⚠️ No se encontró detalle para el candidato en {eleccion}")
                    return {}
                
        except Exception as e:
            logger.error(f"❌ Error al obtener detalle de candidato: {e}")
            return {}
    
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
