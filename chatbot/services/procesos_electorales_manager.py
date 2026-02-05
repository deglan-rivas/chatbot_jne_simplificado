from chatbot.database.oracle_repository import OracleRepository
import logging
import os
from datetime import datetime
from google import genai

logger = logging.getLogger(__name__)

class ProcesosElectoralesManager:
    """Gestor de procesos electorales del JNE"""
    
    def __init__(self):
        self.oracle_repo = OracleRepository()
        # Inicializar cliente LLM
        self.client = genai.Client()
        self.MESES = {
            "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
            "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
            "SEPTIEMBRE": 9, "SETIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
        }
    
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
        Busca hitos electorales usando búsqueda semántica con LLM.
        Obtiene TODOS los hitos del proceso electoral y usa el LLM para seleccionar los más relevantes,
        pasando el texto completo de los hitos al contexto del LLM.
        """
        try:
            # Verificar si es un proceso específico válido
            procesos_especificos = ["EG.2026", "EMC.2025", "ERM.2022", "EG.2021"]
            if proceso_electoral not in procesos_especificos:
                return []
            
            # Obtener TODOS los hitos del proceso electoral (SIN filtro de texto, solo por proceso)
            todos_hitos = self.oracle_repo.obtener_todos_hitos_por_proceso(proceso_electoral)
            
            if not todos_hitos:
                return []
            
            # Si hay pocos hitos, devolver todos directamente
            if len(todos_hitos) <= top_k:
                return todos_hitos
            
            # Crear el texto de los hitos con su descripción completa
            hitos_texto = ""
            for i, hito in enumerate(todos_hitos):
                descripcion = hito.get('hito_electoral', '')
                hitos_texto += f"{i+1}. {descripcion}\n"
            
            prompt = (
                f"Eres un asistente del JNE. Selecciona los {top_k} hitos más relevantes.\n\n"
                f"FECHA ACTUAL: {datetime.now().strftime('%d/%m/%Y')}\n"
                f"CONSULTA: \"{consulta_usuario}\"\n\n"
                f"INSTRUCCIONES:\n"
                f"1. Analiza los hitos disponibles considerando la fecha actual\n"
                f"2. Prioriza hitos que estén por ocurrir o sean recientes\n"
                f"3. Selecciona los {top_k} más relevantes para la consulta\n"
                f"4. Responde SOLO con números separados por comas\n\n"
                f"HITOS ({len(todos_hitos)} disponibles):\n"
                f"{hitos_texto}\n\n"
                f"Respuesta (solo números):"
            )
            
            try:
                # Usar el LLM para encontrar hitos relevantes
                response = self.client.models.generate_content(
                    model="gemma-3-27b-it",
                    contents=prompt
                )
                
                # Parsear la respuesta del LLM
                numeros_texto = response.text.strip()
                numeros = []
                
                # Extraer números de la respuesta
                for parte in numeros_texto.split(','):
                    parte = parte.strip()
                    if parte.isdigit():
                        numero = int(parte) - 1  # Convertir a índice base 0
                        if 0 <= numero < len(todos_hitos):
                            numeros.append(numero)
                
                # Si el LLM devolvió números válidos, usarlos
                if numeros:
                    # Obtener los hitos seleccionados
                    hitos_seleccionados = []
                    for numero in numeros[:top_k]:
                        hitos_seleccionados.append(todos_hitos[numero])
                    
                    return hitos_seleccionados
                else:
                    raise Exception("LLM no devolvió números válidos")
                    
            except Exception as llm_error:
                # Fallback: búsqueda por texto en los hitos disponibles
                return self._busqueda_fallback_hitos(todos_hitos, consulta_usuario, top_k)
            
        except Exception as e:
            return []
    
    def _busqueda_fallback_hitos(self, todos_hitos: list, consulta_usuario: str, top_k: int) -> list:
        """
        Método de fallback para buscar hitos cuando el LLM falla
        """
        try:
            
            # Obtener fecha actual
            fecha_actual = datetime.now()
            
            # Normalizar consulta del usuario
            consulta_normalizada = consulta_usuario.lower().strip()
            palabras_clave = [palabra.strip() for palabra in consulta_normalizada.split() if len(palabra.strip()) > 2]
            
            # Si no hay palabras clave válidas, devolver primeros hitos
            if not palabras_clave:
                return todos_hitos[:top_k]
            
            # Calcular puntuación de relevancia para cada hito
            hitos_con_puntuacion = []
            
            for hito in todos_hitos:
                descripcion = hito.get('hito_electoral', '').lower()
                puntuacion = 0
                
                # Puntuación por palabras clave individuales
                for palabra in palabras_clave:
                    if palabra in descripcion:
                        puntuacion += 1
                        # Bonus por palabras más largas (más específicas)
                        if len(palabra) > 4:
                            puntuacion += 0.5
                
                # Puntuación extra por coincidencias exactas de la consulta completa
                if consulta_normalizada in descripcion:
                    puntuacion += 5
                
                # Puntuación por frases completas
                for i in range(len(palabras_clave) - 1):
                    frase = f"{palabras_clave[i]} {palabras_clave[i+1]}"
                    if frase in descripcion:
                        puntuacion += 2
                
                # Bonus por hitos con fechas específicas
                if hito.get('dia') and hito.get('mes') and hito.get('anio'):
                    puntuacion += 0.3
                    
                    # Bonus temporal: priorizar hitos futuros o recientes
                    try:
                        fecha_hito = datetime(hito['anio'], int(hito['mes']) if hito['mes'].isdigit() else 1, hito['dia'])
                        if fecha_hito > fecha_actual:
                            # Hito futuro - alta prioridad
                            puntuacion += 3
                        elif fecha_hito > fecha_actual.replace(year=fecha_actual.year - 1):
                            # Hito reciente (último año) - prioridad media
                            puntuacion += 1.5
                        else:
                            # Hito histórico - prioridad baja
                            puntuacion += 0.5
                    except:
                        # Si no se puede parsear la fecha, mantener puntuación base
                        pass
                
                hitos_con_puntuacion.append((hito, puntuacion))
            
            # Ordenar por puntuación (mayor a menor)
            hitos_con_puntuacion.sort(key=lambda x: x[1], reverse=True)
            
            # Tomar los top_k hitos con mayor puntuación
            hitos_seleccionados = [hito for hito, _ in hitos_con_puntuacion[:top_k]]
            
            return hitos_seleccionados
            
        except Exception as e:
            # Último recurso: devolver los primeros hitos
            return todos_hitos[:top_k]
    
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
        Genera el menú de hitos electorales encontrados - CONCISO para móviles
        """
        if not hitos:
            return "No se encontraron hitos electorales que coincidan con tu consulta."

        menu = f"📋 **Hitos Encontrados** ({len(hitos)})\n\n"
        menu += "Selecciona uno:\n\n"
        
        for i, hito in enumerate(hitos, 1):
            # Truncar descripción más agresivamente para móviles
            descripcion = hito['hito_electoral']
            if len(descripcion) > 60:  # Más corto para móviles
                descripcion = descripcion[:60] + "..."
            
            # Agregar fecha y contexto temporal de forma compacta
            fecha_info = ""
            contexto_temporal = ""
            
            if hito.get('dia') and hito.get('mes') and hito.get('anio'):
                fecha_info = f" ({hito['dia']}/{hito['mes']})"
                
                # Determinar contexto temporal
                try:
                    mes = None
                    if str(hito['mes']).isdigit():
                        mes = int(hito['mes'])
                    else:
                        mes = self.MESES.get(str(hito['mes']).upper(), 1)  # Default enero si no reconoce
                    
                    fecha_hito = datetime(
                        int(hito['anio']),
                        mes,
                        int(hito['dia'])
                    ).date()
                    fecha_actual = datetime.now().date()
                    
                    if fecha_hito < fecha_actual:
                        contexto_temporal = " ✅"
                    elif fecha_hito > fecha_actual:
                        contexto_temporal = " 🔜"
                    else:
                        contexto_temporal = " 🎯"
                except:
                    contexto_temporal = " 📅"
            
            menu += f"{i}. {descripcion}{fecha_info}{contexto_temporal}\n"
        
        menu += f"\n💡 Escribe el número o 'menu':"
        return menu
    
    def formatear_hito_electoral(self, hito: dict) -> str:
        """
        Formatea un hito electoral usando LLM para generar una respuesta amigable y concisa
        """
        try:
            # Obtener fecha actual
            fecha_actual = datetime.now().date()
            fecha_actual_str = datetime.now().strftime("%d/%m/%Y")
            
            # Construir fecha del hito
            if hito.get('dia') and hito.get('mes') and hito.get('anio'):
                fecha_hito = f"{hito['dia']}/{hito['mes']}/{hito['anio']}"
                
                # Determinar si el hito ya pasó o está por venir
                try:
                    if str(hito['mes']).isdigit():
                        mes = int(hito['mes'])
                    else:
                        mes = self.MESES.get(str(hito['mes']).upper(), 1)  # Default enero si no reconoce
                    
                    fecha_hito_obj = datetime(
                        int(hito['anio']),
                        mes,
                        int(hito['dia'])
                    ).date()
                    
                    if fecha_hito_obj < fecha_actual:
                        contexto_temporal = "ya ocurrió"
                    elif fecha_hito_obj > fecha_actual:
                        contexto_temporal = "está por ocurrir"
                    else:
                        contexto_temporal = "ocurre hoy"
                except:
                    contexto_temporal = "está programado"
            else:
                fecha_hito = "Fecha no especificada"
                contexto_temporal = "sin fecha específica"
            
            # Crear prompt para el LLM con contexto temporal
            prompt = f"""
            Eres un asistente del JNE. Genera una respuesta CONCISA y contextualizada para este hito electoral.
            
            FECHA ACTUAL: {fecha_actual_str}
            HITO: {hito['hito_electoral']}
            FECHA DEL HITO: {fecha_hito}
            PROCESO: {hito['proceso_electoral']}
            CONTEXTO TEMPORAL: Este hito {contexto_temporal}
            
            INSTRUCCIONES:
            - Máximo 3-4 líneas de texto
            - Explica QUÉ es el hito de forma simple
            - Menciona si YA OCURRIÓ o ESTÁ POR OCURRIR
            - Incluye 2-3 emojis relevantes
            - Sé directo y útil para ciudadanos
            - NO uses lenguaje técnico complejo
            
            Respuesta contextualizada:
            """
            
            try:
                # Usar el LLM para generar respuesta amigable
                response = self.client.models.generate_content(
                    model="gemma-3-27b-it",
                    contents=prompt
                )
                
                respuesta_llm = response.text.strip()
                
                # Agregar información esencial de forma compacta
                respuesta_completa = f"{respuesta_llm}\n\n"
                respuesta_completa += f"📅 {fecha_hito} | 🏛️ {hito['proceso_electoral']}\n\n"
                respuesta_completa += "¿Otra consulta? (si/no):"
                
                return respuesta_completa
                
            except Exception as llm_error:
                # Fallback: respuesta estándar CONCISA con contexto temporal
                respuesta = f"📅 **{hito['hito_electoral']}**\n\n"
                respuesta += f"🗓️ {fecha_hito} ({contexto_temporal}) | 🏛️ {hito['proceso_electoral']}\n\n"
                respuesta += "¿Otra consulta? (si/no):"
                
                return respuesta
            
        except Exception as e:
            return "Error al procesar el hito electoral."
    
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
            respuesta += "🔗 **Más Información:** <a href=\"https://infogob.jne.gob.pe/Politico\">https://infogob.jne.gob.pe/Politico</a>\n\n"
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
            respuesta += "<a href=\"https://portal.jne.gob.pe/portal/Pagina/Ver/991/page/Procesos-Electorales\">https://portal.jne.gob.pe/portal/Pagina/Ver/991/page/Procesos-Electorales</a>\n\n"
            respuesta += "En este portal encontrarás:\n"
            respuesta += "• Cronogramas detallados de todos los procesos\n"
            respuesta += "• Fechas importantes y hitos electorales\n"
            respuesta += "• Información actualizada sobre elecciones\n"
            respuesta += "• Documentación oficial del JNE\n\n"
            respuesta += "¿Tienes otra consulta? (responde 'si' o 'no'):"
            
            return respuesta
            
        except Exception as e:
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
    
    def parsear_nombre_completo(self, texto: str) -> dict:
        """
        Parsea un texto que puede contener nombres y apellidos de forma inteligente
        Maneja casos como: "Juan Carlos de la Torre García", "María José del Castillo"
        """
        try:
            # Normalizar el texto
            texto = texto.strip()
            palabras = texto.split()
            
            if len(palabras) < 2:
                return {"nombres": texto, "apellido_paterno": "", "apellido_materno": ""}
            
            # Preposiciones y artículos comunes en apellidos españoles
            preposiciones = {"de", "del", "la", "las", "los", "da", "di", "do", "du", "van", "von", "van der", "von der"}
            
            # Detectar nombres (generalmente las primeras 1-3 palabras)
            nombres = []
            apellidos = []
            i = 0
            
            # Procesar palabras para separar nombres de apellidos
            while i < len(palabras):
                palabra = palabras[i]
                
                # Si es la primera palabra, siempre es nombre
                if i == 0:
                    nombres.append(palabra)
                    i += 1
                    continue
                
                # Si es la segunda palabra, puede ser nombre o apellido
                if i == 1:
                    # Si hay más de 3 palabras totales, la segunda probablemente es nombre
                    if len(palabras) > 3:
                        nombres.append(palabra)
                    else:
                        # Si solo hay 2-3 palabras, la segunda es apellido
                        apellidos.append(palabra)
                    i += 1
                    continue
                
                # Para la tercera palabra en adelante
                if i == 2 and len(palabras) > 3:
                    # Si hay más de 3 palabras, la tercera puede ser nombre o apellido
                    if len(palabras) == 4:
                        # 4 palabras: "Juan Carlos de la Torre" -> nombres: ["Juan", "Carlos"], apellidos: ["de la", "Torre"]
                        nombres.append(palabra)
                    else:
                        # Más de 4 palabras, empezar a considerar apellidos
                        apellidos.append(palabra)
                else:
                    # Palabras restantes son apellidos
                    apellidos.append(palabra)
                
                i += 1
            
            # Procesar apellidos para manejar preposiciones
            apellidos_procesados = self._procesar_apellidos_compuestos(apellidos)
            
            # Construir resultado
            nombres_str = " ".join(nombres)
            apellido_paterno = apellidos_procesados[0] if len(apellidos_procesados) > 0 else ""
            apellido_materno = apellidos_procesados[1] if len(apellidos_procesados) > 1 else ""
            
            return {
                "nombres": nombres_str,
                "apellido_paterno": apellido_paterno,
                "apellido_materno": apellido_materno
            }
            
        except Exception as e:
            logger.error(f"❌ Error al parsear nombre completo: {e}")
            return {"nombres": texto, "apellido_paterno": "", "apellido_materno": ""}
    
    def _procesar_apellidos_compuestos(self, apellidos: list) -> list:
        """
        Procesa apellidos para manejar preposiciones y artículos
        """
        if not apellidos:
            return []
        
        # Preposiciones y artículos comunes
        preposiciones = {"de", "del", "la", "las", "los", "da", "di", "do", "du", "van", "von"}
        
        apellidos_procesados = []
        i = 0
        
        while i < len(apellidos):
            palabra = apellidos[i].lower()
            
            # Si es una preposición, combinarla con la siguiente palabra
            if palabra in preposiciones and i + 1 < len(apellidos):
                apellido_compuesto = f"{apellidos[i]} {apellidos[i + 1]}"
                apellidos_procesados.append(apellido_compuesto)
                i += 2  # Saltar la siguiente palabra
            else:
                # Palabra normal
                apellidos_procesados.append(apellidos[i])
                i += 1
        
        return apellidos_procesados
    
    def buscar_candidatos_inteligente(self, texto_entrada: str) -> list:
        """
        Busca candidatos de forma inteligente parseando el texto de entrada
        Maneja múltiples formatos: "Juan García", "Juan Carlos de la Torre García", etc.
        """
        try:
            logger.info(f"👤 Buscando candidatos inteligentemente: {texto_entrada}")
            
            # Parsear el texto de entrada
            parsed = self.parsear_nombre_completo(texto_entrada)
            
            nombres = parsed["nombres"]
            apellido_paterno = parsed["apellido_paterno"]
            apellido_materno = parsed["apellido_materno"]
            
            logger.info(f"📝 Parseado: nombres='{nombres}', paterno='{apellido_paterno}', materno='{apellido_materno}'")
            
            # Intentar diferentes estrategias de búsqueda
            candidatos = []
            
            # Estrategia 1: Búsqueda con ambos apellidos
            if apellido_paterno and apellido_materno:
                candidatos = self.oracle_repo.buscar_candidatos_por_apellidos_separados(nombres, apellido_paterno, apellido_materno)
                if candidatos:
                    logger.info(f"✅ Encontrados {len(candidatos)} candidatos con ambos apellidos")
                    return candidatos
            
            # Estrategia 2: Búsqueda solo con apellido paterno
            if apellido_paterno:
                candidatos = self.oracle_repo.buscar_candidatos_por_apellidos_separados(nombres, apellido_paterno, "")
                if candidatos:
                    logger.info(f"✅ Encontrados {len(candidatos)} candidatos con apellido paterno")
                    return candidatos
            
            # Estrategia 3: Búsqueda general con nombres y cualquier apellido
            if apellido_paterno or apellido_materno:
                apellidos_combinados = f"{apellido_paterno} {apellido_materno}".strip()
                candidatos = self.oracle_repo.buscar_candidatos_unicos(nombres, apellidos_combinados)
                if candidatos:
                    logger.info(f"✅ Encontrados {len(candidatos)} candidatos con búsqueda general")
                    return candidatos
            
            # Estrategia 4: Búsqueda solo por nombres
            candidatos = self.oracle_repo.buscar_candidatos_unicos(nombres, "")
            if candidatos:
                logger.info(f"✅ Encontrados {len(candidatos)} candidatos solo por nombres")
                return candidatos
            
            logger.warning(f"⚠️ No se encontraron candidatos para: {texto_entrada}")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda inteligente: {e}")
            return []
    
    def buscar_candidatos_por_apellidos_separados(self, nombres: str, apellido_paterno: str, apellido_materno: str) -> list:
        """
        Busca candidatos por nombres, apellido paterno y materno por separado
        """
        try:
            logger.info(f"👤 Buscando candidatos por apellidos separados: {nombres} {apellido_paterno} {apellido_materno}")
            candidatos = self.oracle_repo.buscar_candidatos_por_apellidos_separados(nombres, apellido_paterno, apellido_materno)
            logger.info(f"✅ Candidatos encontrados por apellidos separados: {len(candidatos)} candidatos")
            return candidatos
        except Exception as e:
            logger.error(f"❌ Error al buscar candidatos por apellidos separados: {e}")
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
