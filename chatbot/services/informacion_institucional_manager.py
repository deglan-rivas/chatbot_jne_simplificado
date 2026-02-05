import csv
from pathlib import Path
from typing import Dict, List

class InformacionInstitucionalManager:
    """Gestor de información institucional del JNE"""
    
    def __init__(self):
        self.pleno_miembros = {}
        self._cargar_pleno()
    
    def _cargar_pleno(self):
        """Carga los miembros del pleno desde el archivo CSV"""
        csv_path = Path("./RAG/PLENO.csv")
        
        try:
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file, delimiter=';')
                    for i, row in enumerate(reader, 1):
                        self.pleno_miembros[str(i)] = {
                            "cargo": row.get('TXCARGO', ''),
                            "nombre": row.get('TXNOMBRE', ''),
                            "descripcion": row.get('TXDESCRIPCION', '')
                        }
                print(f"✅ Miembros del pleno cargados: {len(self.pleno_miembros)} miembros")
            else:
                print(f"⚠️ Archivo CSV del pleno no encontrado en: {csv_path}")
        except Exception as e:
            print(f"❌ Error al cargar miembros del pleno: {e}")
    
    def generar_menu_pleno(self) -> str:
        """Genera el menú del pleno con cargos disponibles"""
        if not self.pleno_miembros:
            return "No hay información del pleno disponible en este momento."
        
        menu_text = "Miembros del Pleno del JNE:\n\n"
        for opcion, miembro in self.pleno_miembros.items():
            cargo = miembro.get('cargo', 'Sin cargo')
            # Truncar cargo si es muy largo
            if len(cargo) > 50:
                cargo = cargo[:47] + "..."
            menu_text += f"{opcion}. {cargo}\n"
        
        menu_text += "\nElige un número para ver más detalles:"
        return menu_text
    
    def generar_opciones_pleno(self) -> Dict[str, str]:
        """Genera las opciones del menú del pleno"""
        opciones = {}
        for opcion in self.pleno_miembros.keys():
            opciones[opcion] = f"pleno_{opcion}"
        return opciones
    
    def obtener_miembro_pleno(self, numero: str) -> dict:
        """Obtiene un miembro del pleno por número"""
        return self.pleno_miembros.get(numero, {})
    
    def obtener_info_funcionarios(self) -> str:
        """Retorna la información de funcionarios con enlace"""
        return """📋 **Funcionarios del JNE**

Para consultar información detallada sobre los funcionarios del JNE, visita:

🔗 **Portal de Funcionarios:**
<a href="https://portal.jne.gob.pe/portal/Pagina/Ver/426/page/Funcionarios">https://portal.jne.gob.pe/portal/Pagina/Ver/426/page/Funcionarios</a>

En este portal encontrarás:
• Directorio de funcionarios
• Organigrama institucional
• Información de contacto
• Estructura organizacional"""
    
    def obtener_info_jee(self) -> str:
        """Retorna la información de Jurados Electorales Especiales"""
        return """🏛️ **Jurados Electorales Especiales (JEE)**

Para consultar información sobre los JEE y su ubicación, visita:

🔗 **Plataforma Electoral - JEE:**
<a href="https://plataformaelectoral.jne.gob.pe/conformaciones/jurado-electoral/buscar">https://plataformaelectoral.jne.gob.pe/conformaciones/jurado-electoral/buscar</a>

En esta plataforma podrás:
• Buscar JEE por ubicación
• Consultar conformación de jurados
• Ver información de personeros
• Acceder a expedientes electorales"""
    
    def obtener_info_sedes(self) -> str:
        """Retorna la información de sedes del JNE"""
        return """🏢 **Sedes del JNE**

**Sede Central**
📍 Dirección: Av. Nicolás de Piérola 1070 - Lima, Perú

**Sede Cusco**
📍 Dirección: Jr. Cusco 653 – Cercado de Lima, Perú
🕐 Horario de atención: De lunes a viernes de 8:00 a 16:00 horas

**Sede Nazca**
📍 Dirección: Jr. Nazca 598 - Jesús María - Lima, Perú

**Museo Electoral**
📍 Dirección: Av. Nicolás de Piérola 1070 - Lima, Perú
🕐 Horario de atención: De lunes a viernes de 8:00 a 16:00 horas

**Oficinas Desconcentradas**
🔗 Más información: <a href="https://portal.jne.gob.pe/portal/Pagina/Ver/902/page/Oficinas-Desconcentradas">https://portal.jne.gob.pe/portal/Pagina/Ver/902/page/Oficinas-Desconcentradas</a>

**Información de Contacto General**
📧 consultas@jne.gob.pe
📞 (511) 311-1717
🕐 Lunes a Viernes de 8:00 a 16:00 horas"""
    
    def recargar_pleno(self):
        """Recarga los miembros del pleno desde el archivo CSV"""
        self._cargar_pleno()
        print("✅ Información del pleno recargada exitosamente")
    
    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas de la información institucional"""
        return {
            "miembros_pleno": len(self.pleno_miembros),
            "sedes_disponibles": 4,  # Sede Central, Cusco, Nazca, Museo Electoral
            "enlaces_externos": 2  # Funcionarios y JEE
        }
