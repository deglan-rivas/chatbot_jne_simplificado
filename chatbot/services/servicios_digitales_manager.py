import csv
from pathlib import Path
from typing import Dict, List
from google import genai

class ServiciosDigitalesManager:
    """Gestor de servicios digitales del JNE"""
    
    def __init__(self):
        self.servicios_digitales = {}
        self.servicios_busqueda = []
        self.client = genai.Client()
        self._cargar_servicios()
    
    def _cargar_servicios(self):
        """Carga todos los servicios al inicializar"""
        self.servicios_digitales = self._cargar_servicios_digitales()
        self.servicios_busqueda = self._cargar_servicios_busqueda()
    
    def _cargar_servicios_digitales(self) -> Dict[str, dict]:
        """Carga los servicios digitales principales desde el archivo CSV"""
        servicios = {}
        csv_path = Path("./RAG/PRINCIPALES.csv")
        
        try:
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file, delimiter=';')
                    for i, row in enumerate(reader, 1):
                        servicios[str(i)] = {
                            "nombre": row.get('TXNOMBRE', ''),
                            "descripcion": row.get('TXDESCRIPCIONCORTA', ''),
                            "enlace": row.get('TXENLACE', '')
                        }
                print(f"✅ Servicios digitales principales cargados: {len(servicios)} servicios")
            else:
                print(f"⚠️ Archivo CSV no encontrado en: {csv_path}")
        except Exception as e:
            print(f"❌ Error al cargar servicios digitales: {e}")
        
        return servicios
    
    def _cargar_servicios_busqueda(self) -> List[dict]:
        """Carga todos los servicios para búsqueda semántica"""
        servicios = []
        csv_path = Path("./RAG/SERVICIOS_DIGITALES.csv")
        
        try:
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file, delimiter=';')
                    for row in reader:
                        servicios.append({
                            "nombre": row.get('TXNOMBRE', ''),
                            "descripcion": row.get('TXDESCRIPCIONCORTA', ''),
                            "enlace": row.get('TXENLACE', '')
                        })
                print(f"Servicios para búsqueda cargados: {len(servicios)} servicios")
            else:
                print(f"Archivo CSV de búsqueda no encontrado en: {csv_path}")
        except Exception as e:
            print(f"Error al cargar servicios para búsqueda: {e}")
        
        return servicios
    
    def buscar_servicios_semanticamente(self, consulta_usuario: str, top_k: int = 5) -> List[dict]:
        """
        Busca servicios relevantes usando el LLM para análisis semántico
        """
        if not self.servicios_busqueda:
            return []
        
        # Crear prompt para el LLM
        servicios_texto = ""
        for i, servicio in enumerate(self.servicios_busqueda):
            servicios_texto += f"{i+1}. {servicio['nombre']}: {servicio['descripcion']}\n"
        
        prompt = f"""
        Eres un asistente experto en servicios digitales del JNE. 
        
        El usuario busca: "{consulta_usuario}"
        
        Analiza los siguientes servicios y selecciona los {top_k} más relevantes para la consulta del usuario.
        Responde SOLO con los números de los servicios más relevantes, separados por comas.
        
        Servicios disponibles:
        {servicios_texto}
        
        Números de servicios más relevantes:"""
        
        try:
            # Usar el LLM para encontrar servicios relevantes
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
                    if 0 <= numero < len(self.servicios_busqueda):
                        numeros.append(numero)
            
            # Obtener los servicios seleccionados
            servicios_seleccionados = []
            for numero in numeros[:top_k]:
                servicios_seleccionados.append(self.servicios_busqueda[numero])
            
            return servicios_seleccionados
            
        except Exception as e:
            print(f"Error en búsqueda semántica: {e}")
            # Fallback: devolver primeros servicios
            return self.servicios_busqueda[:top_k]
    
    def generar_menu_servicios_digitales(self) -> str:
        """Genera el texto del menú de servicios digitales principales"""
        if not self.servicios_digitales:
            return "No hay servicios digitales disponibles en este momento."
        
        menu_text = "Servicios digitales disponibles:\n"
        for opcion, servicio in self.servicios_digitales.items():
            nombre = servicio.get('nombre', 'Sin nombre')
            # Truncar nombre si es muy largo
            if len(nombre) > 50:
                nombre = nombre[:47] + "..."
            menu_text += f"{opcion}. {nombre}\n"
        
        menu_text += "\nElige un número para ver más detalles:"
        return menu_text
    
    def generar_opciones_servicios_digitales(self) -> Dict[str, str]:
        """Genera las opciones del menú de servicios digitales principales"""
        opciones = {}
        for opcion in self.servicios_digitales.keys():
            opciones[opcion] = f"servicio_{opcion}"
        return opciones
    
    def generar_menu_servicios_busqueda(self, servicios_encontrados: List[dict]) -> str:
        """Genera el menú de servicios encontrados por búsqueda semántica"""
        if not servicios_encontrados:
            return "No se encontraron servicios relevantes para tu consulta. Por favor, intenta con otros términos."
        
        menu_text = "Servicios encontrados para tu consulta:\n\n"
        for i, servicio in enumerate(servicios_encontrados, 1):
            nombre = servicio.get('nombre', 'Sin nombre')
            # Truncar nombre si es muy largo
            if len(nombre) > 60:
                nombre = nombre[:57] + "..."
            menu_text += f"{i}. {nombre}\n"
        
        menu_text += "\nElige un número para ver más detalles:"
        return menu_text
    
    def generar_opciones_servicios_busqueda(self, servicios_encontrados: List[dict]) -> Dict[str, str]:
        """Genera las opciones del menú de servicios encontrados"""
        opciones = {}
        for i in range(len(servicios_encontrados)):
            opciones[str(i + 1)] = f"busqueda_{i}"
        return opciones
    
    def obtener_servicio_principal(self, numero: str) -> dict:
        """Obtiene un servicio principal por número"""
        return self.servicios_digitales.get(numero, {})
    
    def obtener_servicio_busqueda(self, index: int) -> dict:
        """Obtiene un servicio de búsqueda por índice"""
        if 0 <= index < len(self.servicios_busqueda):
            return self.servicios_busqueda[index]
        return {}
    
    def recargar_servicios(self):
        """Recarga todos los servicios desde los archivos CSV"""
        self.servicios_digitales = self._cargar_servicios_digitales()
        self.servicios_busqueda = self._cargar_servicios_busqueda()
        print("Servicios recargados exitosamente")
    
    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas de los servicios cargados"""
        return {
            "servicios_principales": len(self.servicios_digitales),
            "servicios_busqueda": len(self.servicios_busqueda),
            "total": len(self.servicios_digitales) + len(self.servicios_busqueda)
        }
