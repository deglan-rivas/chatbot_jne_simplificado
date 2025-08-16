from chatbot.database.oracle_repository import OracleRepository
import logging
import os
from google import genai

logger = logging.getLogger(__name__)

class ProcesosElectoralesManager:
    """Gestor de procesos electorales del JNE"""
    
    def __init__(self):
        self.oracle_repo = OracleRepository()
        # Inicializar cliente LLM
        self.client = genai.Client()
    
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
        Genera el menú de cronograma electoral con procesos específicos
        """
        try:
            logger.info("📅 Generando menú de cronograma electoral...")
            
            # Procesos específicos que siempre se muestran
            procesos_especificos = [
                "EG.2026",
                "EMC.2025", 
                "ERM.2022",
                "EG.2021"
            ]
            
            # Obtener todos los procesos de la base de datos
            todos_procesos = self.oracle_repo.obtener_procesos_electorales()
            
            # Filtrar procesos que no están en la lista específica
            otros_procesos = []
            if todos_procesos:
                otros_procesos = [p for p in todos_procesos if p not in procesos_especificos]
            
            # Generar menú con procesos específicos
            menu = "📅 **Cronograma Electoral**\n\nSelecciona el proceso electoral que deseas consultar:\n\n"
            
            # Agregar procesos específicos
            for i, proceso in enumerate(procesos_especificos, 1):
                menu += f"{i}. {proceso}\n"
            
            # Agregar opción de otros procesos
            menu += f"{len(procesos_especificos) + 1}. Otros procesos electorales"
            
            # Mostrar cuántos otros procesos hay disponibles
            if otros_procesos:
                menu += f" ({len(otros_procesos)} procesos adicionales)"
            
            menu += "\n"
            
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
    
    def buscar_hitos_electorales_semanticamente(self, proceso_electoral: str, consulta_usuario: str, top_k: int = 5) -> list:
        """
        Busca hitos electorales usando búsqueda semántica con LLM (similar a servicios digitales)
        """
        try:
            logger.info(f"🔍 Buscando hitos electorales semánticamente para {proceso_electoral} con consulta: {consulta_usuario}")
            
            # Obtener todos los hitos del proceso electoral
            todos_hitos = self.oracle_repo.obtener_hitos_electorales_por_proceso(proceso_electoral)
            
            if not todos_hitos:
                logger.warning(f"No se encontraron hitos para el proceso: {proceso_electoral}")
                return []
            
            # Crear prompt para el LLM (exactamente como servicios digitales)
            hitos_texto = ""
            for i, hito in enumerate(todos_hitos):
                hitos_texto += f"{i+1}. {hito['hito_electoral']}\n"
            
            prompt = f"""
            Eres un asistente experto en procesos electorales del JNE. 
            
            El usuario busca: "{consulta_usuario}"
            
            IMPORTANTE: Solo hay {len(todos_hitos)} hitos electorales disponibles (numerados del 1 al {len(todos_hitos)}).
            
            Analiza los siguientes hitos electorales y selecciona los {top_k} más relevantes para la consulta del usuario.
            Responde SOLO con los números de los hitos más relevantes, separados por comas.
            
            Hitos electorales disponibles:
            {hitos_texto}
            
            Números de hitos más relevantes (solo números del 1 al {len(todos_hitos)}):"""
            
            # Usar el LLM para encontrar hitos relevantes
            response = self.client.models.generate_content(
                model="gemma-3-27b-it",
                contents=prompt
            )
            
            # Parsear la respuesta del LLM
            numeros_texto = response.text.strip()
            logger.info(f"🤖 Respuesta del LLM: '{numeros_texto}'")
            numeros = []
            
            # Extraer números de la respuesta
            for parte in numeros_texto.split(','):
                parte = parte.strip()
                if parte.isdigit():
                    numero = int(parte) - 1  # Convertir a índice base 0
                    if 0 <= numero < len(todos_hitos):
                        numeros.append(numero)
                    else:
                        logger.warning(f"⚠️ Número fuera de rango: {numero} (rango: 0-{len(todos_hitos)-1})")
                else:
                    logger.warning(f"⚠️ Parte no numérica: '{parte}'")
            
            logger.info(f"📊 Números extraídos: {numeros}")
            
            # Obtener los hitos seleccionados
            hitos_seleccionados = []
            for numero in numeros[:top_k]:
                hitos_seleccionados.append(todos_hitos[numero])
            
            logger.info(f"✅ Hitos seleccionados semánticamente: {len(hitos_seleccionados)} hitos")
            return hitos_seleccionados
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda semántica de hitos: {e}")
            # Fallback: devolver primeros hitos
            return todos_hitos[:top_k] if todos_hitos else []
    
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
            fecha = f"14/08/2025"
            
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

    def obtener_otros_procesos_electorales(self) -> str:
        """
        Obtiene información sobre otros procesos electorales
        """
        try:
            respuesta = "📋 **Otros Procesos Electorales**\n\n"
            respuesta += "Para obtener información completa sobre todos los procesos electorales, "
            respuesta += "incluyendo cronogramas, fechas importantes y detalles específicos, "
            respuesta += "visita el portal oficial del JNE:\n\n"
            respuesta += "🔗 **Portal de Procesos Electorales:**\n"
            respuesta += "https://portal.jne.gob.pe/portal/Pagina/Ver/991/page/Procesos-Electorales\n\n"
            respuesta += "En este portal encontrarás:\n"
            respuesta += "• Cronogramas detallados de todos los procesos\n"
            respuesta += "• Fechas importantes y hitos electorales\n"
            respuesta += "• Información actualizada sobre elecciones\n"
            respuesta += "• Documentación oficial del JNE\n\n"
            respuesta += "¿Tienes otra consulta? (responde 'si' o 'no'):"
            
            return respuesta
            
        except Exception as e:
            logger.error(f"❌ Error al obtener otros procesos electorales: {e}")
            return "Error al obtener información de otros procesos electorales. Por favor, intente más tarde."

    def obtener_elecciones_disponibles(self) -> list:
        """
        Obtiene la lista de elecciones disponibles para consulta de políticos
        """
        try:
            logger.info("🗳️ Obteniendo elecciones disponibles...")
            elecciones = self.oracle_repo.obtener_elecciones_disponibles()
            logger.info(f"✅ Elecciones obtenidas: {len(elecciones)} elecciones")
            return elecciones
        except Exception as e:
            logger.error(f"❌ Error al obtener elecciones: {e}")
            return []
    
    def generar_menu_elecciones(self) -> str:
        """
        Genera el menú de elecciones disponibles
        """
        try:
            elecciones = self.obtener_elecciones_disponibles()
            
            if not elecciones:
                return "No se encontraron elecciones disponibles en este momento."
            
            menu = "🗳️ **Elecciones Disponibles**\n\nSelecciona la elección para consultar políticos:\n\n"
            
            for i, eleccion in enumerate(elecciones, 1):
                menu += f"{i}. {eleccion}\n"
            
            return menu
            
        except Exception as e:
            logger.error(f"❌ Error al generar menú de elecciones: {e}")
            return "Error al obtener elecciones disponibles. Por favor, intente más tarde."
    
    def buscar_politicos_por_eleccion(self, eleccion: str, nombres: str = "", apellidos: str = "") -> list:
        """
        Busca políticos por elección específica y opcionalmente por nombres/apellidos
        """
        try:
            logger.info(f"👤 Buscando políticos por elección: {eleccion}")
            politicos = self.oracle_repo.buscar_politicos_por_eleccion(eleccion, nombres, apellidos)
            logger.info(f"✅ Políticos encontrados: {len(politicos)} políticos")
            return politicos
        except Exception as e:
            logger.error(f"❌ Error al buscar políticos por elección: {e}")
            return []

    def buscar_candidatos_unicos(self, nombres: str, apellidos: str = "") -> list:
        """
        Busca candidatos únicos por nombres y apellidos (sin repetir nombres)
        """
        try:
            logger.info(f"👤 Buscando candidatos únicos: {nombres} {apellidos}")
            candidatos = self.oracle_repo.buscar_candidatos_unicos(nombres, apellidos)
            logger.info(f"✅ Candidatos únicos encontrados: {len(candidatos)} candidatos")
            return candidatos
        except Exception as e:
            logger.error(f"❌ Error al buscar candidatos únicos: {e}")
            return []
    
    def generar_menu_candidatos(self, candidatos: list) -> str:
        """
        Genera el menú de candidatos únicos encontrados
        """
        if not candidatos:
            return "No se encontraron candidatos que coincidan con tu búsqueda."
        
        menu = "👥 **Candidatos Encontrados**\n\nSelecciona el candidato que deseas consultar:\n\n"
        
        for i, candidato in enumerate(candidatos, 1):
            menu += f"{i}. {candidato['nombre_completo']}\n"
        
        return menu
    
    def obtener_elecciones_por_candidato(self, nombres: str, apellido_paterno: str, apellido_materno: str) -> list:
        """
        Obtiene todas las elecciones donde aparece un candidato específico
        """
        try:
            logger.info(f"🗳️ Obteniendo elecciones para candidato: {nombres} {apellido_paterno} {apellido_materno}")
            elecciones = self.oracle_repo.obtener_elecciones_por_candidato(nombres, apellido_paterno, apellido_materno)
            logger.info(f"✅ Elecciones encontradas: {len(elecciones)} elecciones")
            return elecciones
        except Exception as e:
            logger.error(f"❌ Error al obtener elecciones por candidato: {e}")
            return []
    
    def generar_menu_elecciones_candidato(self, elecciones: list, nombre_candidato: str) -> str:
        """
        Genera el menú de elecciones donde aparece un candidato
        """
        if not elecciones:
            return f"No se encontraron elecciones para {nombre_candidato}."
        
        menu = f"🗳️ **Elecciones de {nombre_candidato}**\n\nSelecciona la elección para ver el detalle:\n\n"
        
        for i, eleccion in enumerate(elecciones, 1):
            menu += f"{i}. {eleccion}\n"
        
        return menu
    
    def obtener_detalle_candidato_eleccion(self, nombres: str, apellido_paterno: str, apellido_materno: str, eleccion: str) -> dict:
        """
        Obtiene el detalle completo de un candidato en una elección específica
        """
        try:
            logger.info(f"📋 Obteniendo detalle de candidato en elección: {eleccion}")
            detalle = self.oracle_repo.obtener_detalle_candidato_eleccion(nombres, apellido_paterno, apellido_materno, eleccion)
            logger.info(f"✅ Detalle obtenido: {'Sí' if detalle else 'No'}")
            return detalle
        except Exception as e:
            logger.error(f"❌ Error al obtener detalle de candidato: {e}")
            return {}
