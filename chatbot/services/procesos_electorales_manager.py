from chatbot.database.oracle_repository import OracleRepository
import logging

logger = logging.getLogger(__name__)

class ProcesosElectoralesManager:
    """Gestor de procesos electorales del JNE"""
    
    def __init__(self):
        self.oracle_repo = OracleRepository()
    
    def obtener_tipos_organizaciones_politicas(self) -> str:
        """
        Obtiene el reporte de tipos de organizaciones políticas desde Oracle
        """
        try:
            logger.info("📊 Obteniendo estadísticas de organizaciones políticas...")
            reporte = self.oracle_repo.generar_reporte_organizaciones_politicas()
            
            if reporte:
                logger.info("✅ Reporte de organizaciones políticas generado exitosamente")
                return reporte
            else:
                logger.warning("⚠️ No se pudo generar el reporte de organizaciones políticas")
                return "No se pudo obtener información de organizaciones políticas en este momento."
                
        except Exception as e:
            logger.error(f"❌ Error al obtener tipos de organizaciones políticas: {e}")
            return "Error al obtener información de organizaciones políticas. Por favor, intente más tarde."
    
    def obtener_consulta_afiliacion(self) -> str:
        """
        Obtiene el enlace para consulta de afiliación
        """
        try:
            logger.info("🔍 Obteniendo enlace de consulta de afiliación...")
            return self.oracle_repo.obtener_enlace_consulta_afiliacion()
            
        except Exception as e:
            logger.error(f"❌ Error al obtener enlace de consulta de afiliación: {e}")
            return "Error al obtener información de consulta de afiliación."
    
    def generar_menu_cronograma_electoral(self) -> str:
        """
        Genera el menú de cronograma electoral con los procesos disponibles
        """
        try:
            logger.info("📅 Generando menú de cronograma electoral...")
            procesos = self.oracle_repo.obtener_procesos_electorales()
            
            if not procesos:
                return "No se encontraron procesos electorales disponibles en este momento."
            
            menu = "📅 **Cronograma Electoral**\n\nSelecciona el proceso electoral que deseas consultar:\n\n"
            
            for i, proceso in enumerate(procesos, 1):
                menu += f"{i}. {proceso}\n"
            
            return menu
            
        except Exception as e:
            logger.error(f"❌ Error al generar menú de cronograma electoral: {e}")
            return "Error al obtener procesos electorales. Por favor, intente más tarde."
    
    def obtener_procesos_electorales(self) -> list:
        """
        Obtiene la lista de procesos electorales
        """
        try:
            return self.oracle_repo.obtener_procesos_electorales()
        except Exception as e:
            logger.error(f"❌ Error al obtener procesos electorales: {e}")
            return []
    
    def buscar_hitos_electorales(self, proceso_electoral: str, consulta: str) -> list:
        """
        Busca hitos electorales por proceso electoral y consulta
        """
        try:
            logger.info(f"🔍 Buscando hitos electorales para {proceso_electoral} con consulta: {consulta}")
            return self.oracle_repo.buscar_hitos_electorales(proceso_electoral, consulta)
        except Exception as e:
            logger.error(f"❌ Error al buscar hitos electorales: {e}")
            return []
    
    def generar_menu_hitos(self, hitos: list) -> str:
        """
        Genera el menú de hitos electorales encontrados
        """
        if not hitos:
            return "No se encontraron hitos electorales que coincidan con tu consulta."
        
        menu = "📋 **Hitos Electorales Encontrados**\n\nSelecciona el hito que deseas consultar:\n\n"
        
        for i, hito in enumerate(hitos, 1):
            # Truncar descripción si es muy larga
            descripcion = hito['hito_electoral']
            if len(descripcion) > 80:
                descripcion = descripcion[:80] + "..."
            
            menu += f"{i}. {descripcion}\n"
        
        return menu
    
    def formatear_hito_electoral(self, hito: dict) -> str:
        """
        Formatea un hito electoral para mostrar al usuario
        """
        try:
            fecha = f"{hito['dia']} de {hito['mes']} del {hito['anio']}"
            
            respuesta = f"📅 **Hito Electoral**\n\n"
            respuesta += f"🗓️ **Fecha:** {fecha}\n\n"
            respuesta += f"📝 **Descripción:** {hito['hito_electoral']}\n\n"
            respuesta += f"🏛️ **Proceso Electoral:** {hito['proceso_electoral']}\n\n"
            respuesta += "¿Tienes otra consulta? (responde 'si' o 'no'):"
            
            return respuesta
            
        except Exception as e:
            logger.error(f"❌ Error al formatear hito electoral: {e}")
            return "Error al formatear la información del hito electoral."
    
    def buscar_politicos(self, nombres: str, apellidos: str = "") -> list:
        """
        Busca políticos por nombres y apellidos
        """
        try:
            logger.info(f"👤 Buscando políticos: {nombres} {apellidos}")
            return self.oracle_repo.buscar_politicos(nombres, apellidos)
        except Exception as e:
            logger.error(f"❌ Error al buscar políticos: {e}")
            return []
    
    def generar_menu_politicos(self, politicos: list) -> str:
        """
        Genera el menú de políticos encontrados
        """
        if not politicos:
            return "No se encontraron políticos que coincidan con tu búsqueda."
        
        if len(politicos) > 10:
            return f"Se encontraron {len(politicos)} políticos. Por favor, proporciona un segundo apellido para refinar la búsqueda."
        
        menu = "👥 **Políticos Encontrados**\n\nSelecciona el político que deseas consultar:\n\n"
        
        for i, politico in enumerate(politicos, 1):
            nombre_completo = f"{politico['nombres']} {politico['apellido_paterno']} {politico['apellido_materno']}"
            menu += f"{i}. {nombre_completo}\n"
        
        return menu
    
    def formatear_politico(self, politico: dict) -> str:
        """
        Formatea la información de un político para mostrar al usuario
        """
        try:
            respuesta = f"👤 **Información del Político**\n\n"
            respuesta += f"📛 **Nombres y Apellidos:** {politico['nombres']} {politico['apellido_paterno']} {politico['apellido_materno']}\n\n"
            respuesta += f"📍 **Ubicación:** {politico['region']}, {politico['provincia']}, {politico['distrito']}\n\n"
            respuesta += f"🏛️ **Organización Política:** {politico['organizacion_politica']}\n\n"
            respuesta += f"🗳️ **Elección:** {politico['eleccion']} ({politico['siglas']})\n\n"
            respuesta += f"📋 **Tipo de Elección:** {politico['tipo_eleccion']}\n\n"
            respuesta += f"🎯 **Cargo Postulado:** {politico['cargo_postulado']}\n\n"
            respuesta += f"🏆 **Cargo Electo:** {politico['cargo_electo']}\n\n"
            respuesta += "📌 Esta información es consultada desde el registro oficial del Jurado Nacional de Elecciones.\n\n"
            respuesta += "🔗 **Más Información:** https://infogob.jne.gob.pe/Politico\n\n"
            respuesta += "¿Tienes otra consulta? (responde 'si' o 'no'):"
            
            return respuesta
            
        except Exception as e:
            logger.error(f"❌ Error al formatear político: {e}")
            return "Error al formatear la información del político."
    
    def obtener_estadisticas(self) -> dict:
        """
        Obtiene estadísticas generales de procesos electorales
        """
        try:
            # Obtener estadísticas de Oracle
            stats_oracle = self.oracle_repo.obtener_estadisticas_organizaciones_politicas()
            
            # Calcular totales
            total_inscritos = sum(stats.get('inscritos', 0) for stats in stats_oracle.values())
            total_en_proceso = sum(stats.get('en_proceso', 0) for stats in stats_oracle.values())
            
            return {
                "total_organizaciones": total_inscritos + total_en_proceso,
                "inscritas": total_inscritos,
                "en_proceso": total_en_proceso,
                "tipos_disponibles": len(stats_oracle)
            }
            
        except Exception as e:
            logger.error(f"❌ Error al obtener estadísticas: {e}")
            return {
                "total_organizaciones": 0,
                "inscritas": 0,
                "en_proceso": 0,
                "tipos_disponibles": 0
            }
    
    def recargar_datos(self) -> str:
        """
        Recarga los datos desde Oracle
        """
        try:
            logger.info("🔄 Recargando datos de procesos electorales...")
            
            # Obtener estadísticas actualizadas
            stats = self.obtener_estadisticas()
            
            return f"✅ Datos recargados exitosamente. Total organizaciones: {stats['total_organizaciones']}"
                
        except Exception as e:
            logger.error(f"❌ Error al recargar datos: {e}")
            return f"Error al recargar datos: {str(e)}"
