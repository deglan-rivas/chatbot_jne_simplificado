"""
ResponseBuilder: Construye respuestas enriquecidas para frontend web
"""
from typing import Dict, Any, List, Optional
from chatbot.utils.chatbot_core import menus
import logging

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """Construye respuestas enriquecidas para frontend web"""
    
    @staticmethod
    def build_response(
        response_text: str,
        state: Dict[str, Any],
        menu_actual: str,
        should_finalize: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Construye respuesta enriquecida basada en el estado y menú actual
        
        Args:
            response_text: Texto de respuesta plano
            state: Estado actual del chatbot
            menu_actual: Menú actual
            should_finalize: Si la conversación debe finalizar
            
        Returns:
            Dict con estructura response_rich o None si no se puede construir
        """
        try:
            # Determinar el stage correcto: priorizar menu_actual si es válido, sino usar state
            stage = None
            if menu_actual and menu_actual in menus:
                stage = menu_actual
            else:
                stage = state.get("stage", "main")
            
            # Si está en un menú con opciones
            if stage in menus and stage not in ["servicios_ciudadano", "pleno"]:
                menu_data = menus.get(stage, {})
                menu_options = menu_data.get("options", {})
                
                if menu_options:
                    return ResponseBuilder._build_menu_response(
                        response_text, stage, menu_options
                    )
            
            # Si está finalizando
            if should_finalize:
                return ResponseBuilder._build_text_response(response_text)
            
            # Detectar preguntas sí/no (incluyendo "¿Otra consulta?")
            if ResponseBuilder._has_yes_no_question(response_text):
                return ResponseBuilder._build_buttons_response(
                    response_text,
                    [
                        {"label": "Sí", "value": "si", "style": "primary"},
                        {"label": "No", "value": "no", "style": "secondary"}
                    ]
                )
            
            # Detectar listas numeradas (hitos, procesos electorales, etc.)
            numbered_list = ResponseBuilder._extract_numbered_list(response_text)
            if numbered_list:
                # Si es una lista de hitos (contiene "Hitos Encontrados" o tiene muchos items)
                if "hitos encontrados" in response_text.lower() or len(numbered_list) > 3:
                    return ResponseBuilder._build_list_from_numbered_items(
                        response_text, numbered_list
                    )
                # Si es un menú corto (procesos electorales, etc.)
                else:
                    return ResponseBuilder._build_menu_from_numbered_items(
                        response_text, numbered_list
                    )
            
            # Por defecto, texto simple
            return ResponseBuilder._build_text_response(response_text)
            
        except Exception as e:
            logger.error(f"Error construyendo response_rich: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _build_menu_response(
        text: str,
        menu_key: str,
        menu_options: Dict[str, str]
    ) -> Dict[str, Any]:
        """Construye respuesta de tipo menú"""
        # Extraer título del menú si existe
        menu_data = menus.get(menu_key, {})
        menu_title = menu_data.get("text", "").split("\n")[0] if menu_data.get("text") else None
        
        # Limpiar texto de respuesta (remover el texto del menú si está duplicado)
        clean_text = text
        if menu_data.get("text") and menu_data["text"] in text:
            # Intentar extraer solo el texto antes del menú
            parts = text.split(menu_data["text"])
            if parts:
                clean_text = parts[0].strip()
        
        # Construir acciones (botones)
        actions = []
        for value, option_key in menu_options.items():
            # Extraer label del texto del menú
            label = None
            if menu_data.get("text"):
                lines = menu_data["text"].split("\n")
                for line in lines:
                    if line.strip().startswith(f"{value}."):
                        label = line.strip()
                        break
            
            # Si no se encontró label, usar el valor
            if not label:
                label = f"{value}. {option_key.replace('_', ' ').title()}"
            
            actions.append({
                "type": "button",
                "label": label,
                "value": value,
                "style": "primary"
            })
        
        result = {
            "type": "menu",
            "content": {
                "text": clean_text or "Selecciona una opción:"
            },
            "actions": actions
        }
        
        if menu_title:
            result["content"]["title"] = menu_title
        
        return result
    
    @staticmethod
    def _build_buttons_response(
        text: str,
        buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Construye respuesta con botones de acción"""
        actions = []
        for btn in buttons:
            actions.append({
                "type": "button",
                "label": btn["label"],
                "value": btn["value"],
                "style": btn.get("style", "primary")
            })
        
        return {
            "type": "buttons",
            "content": {
                "text": text
            },
            "actions": actions
        }
    
    @staticmethod
    def _build_text_response(text: str) -> Dict[str, Any]:
        """Construye respuesta de tipo texto simple"""
        return {
            "type": "text",
            "content": {
                "text": text
            }
        }
    
    @staticmethod
    def build_list_response(
        text: str,
        items: List[Dict[str, Any]],
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Construye respuesta de tipo lista"""
        formatted_items = []
        for idx, item in enumerate(items, 1):
            formatted_items.append({
                "id": str(idx),
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "value": item.get("value", str(idx))
            })
        
        result = {
            "type": "list",
            "content": {
                "text": text
            },
            "items": formatted_items
        }
        
        if title:
            result["content"]["title"] = title
        
        return result
    
    @staticmethod
    def build_card_response(
        title: str,
        text: str,
        subtitle: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Construye respuesta de tipo tarjeta"""
        result = {
            "type": "card",
            "content": {
                "title": title,
                "text": text
            }
        }
        
        if subtitle:
            result["content"]["subtitle"] = subtitle
        
        if actions:
            result["actions"] = [
                {
                    "type": "button",
                    "label": action["label"],
                    "value": action["value"],
                    "style": action.get("style", "secondary")
                }
                for action in actions
            ]
        
        return result
    
    @staticmethod
    def _has_yes_no_question(text: str) -> bool:
        """Detecta si el texto contiene una pregunta sí/no"""
        text_lower = text.lower()
        yes_no_patterns = [
            "¿otra consulta",
            "¿tienes",
            "¿deseas",
            "¿quieres",
            "¿tiene",
            "¿desea",
            "¿quiere",
            "(si/no)",
            "(sí/no)",
            "si/no:",
            "sí/no:"
        ]
        return any(pattern in text_lower for pattern in yes_no_patterns)
    
    @staticmethod
    def _extract_numbered_list(text: str) -> List[Dict[str, str]]:
        """
        Extrae items numerados del texto (ej: "1. EG.2026", "2. EMC.2025")
        Retorna lista de dicts con 'number', 'label', 'value'
        """
        import re
        items = []
        lines = text.split('\n')
        
        for line in lines:
            # Buscar patrones como "1. Texto" o "1) Texto"
            match = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
            if match:
                number = match.group(1)
                label = match.group(2).strip()
                # Limpiar emojis y caracteres especiales del label para el value
                value = number
                items.append({
                    "number": number,
                    "label": label,
                    "value": value
                })
        
        return items
    
    @staticmethod
    def _build_list_from_numbered_items(
        text: str,
        items: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Construye respuesta de tipo lista desde items numerados"""
        # Extraer título si existe (ej: "📋 **Hitos Encontrados** (5)")
        title = None
        text_lines = text.split('\n')
        for line in text_lines[:3]:  # Buscar en las primeras 3 líneas
            if "hitos encontrados" in line.lower() or "cronograma" in line.lower():
                # Limpiar markdown
                title = line.replace('**', '').replace('*', '').strip()
                break
        
        # Limpiar el texto de respuesta (remover la lista numerada y líneas de ayuda)
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            line_stripped = line.strip()
            # Omitir líneas que sean items numerados
            if any(line_stripped.startswith(f"{item['number']}.") for item in items):
                continue
            # Omitir líneas de ayuda
            if line_stripped.startswith('💡') or line_stripped.startswith('Escribe el número'):
                continue
            # Incluir otras líneas
            if line_stripped:
                clean_lines.append(line)
        
        clean_text = '\n'.join(clean_lines).strip()
        
        # Si no hay texto limpio, usar un texto por defecto
        if not clean_text:
            clean_text = "Selecciona una opción:"
        
        # Construir items para la lista
        list_items = []
        for item in items:
            list_items.append({
                "title": item["label"],
                "description": "",  # Los hitos no tienen descripción adicional
                "value": item["value"]
            })
        
        return ResponseBuilder.build_list_response(
            clean_text,
            list_items,
            title=title
        )
    
    @staticmethod
    def _build_menu_from_numbered_items(
        text: str,
        items: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Construye respuesta de tipo menú desde items numerados"""
        # Extraer título si existe
        title = None
        text_lines = text.split('\n')
        for line in text_lines[:3]:
            if "cronograma" in line.lower() or "selecciona" in line.lower():
                title = line.replace('**', '').replace('*', '').strip()
                break
        
        # Limpiar el texto de respuesta (remover la lista numerada y líneas de ayuda)
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            line_stripped = line.strip()
            # Omitir líneas que sean items numerados
            if any(line_stripped.startswith(f"{item['number']}.") for item in items):
                continue
            # Omitir líneas de ayuda
            if line_stripped.startswith('💡') or line_stripped.startswith('Escribe el número'):
                continue
            # Incluir otras líneas
            if line_stripped:
                clean_lines.append(line)
        
        clean_text = '\n'.join(clean_lines).strip()
        
        # Si no hay texto limpio, usar un texto por defecto
        if not clean_text:
            clean_text = "Selecciona una opción:"
        
        # Construir acciones (botones)
        actions = []
        for item in items:
            actions.append({
                "type": "button",
                "label": f"{item['number']}. {item['label']}",
                "value": item["value"],
                "style": "primary"
            })
        
        result = {
            "type": "menu",
            "content": {
                "text": clean_text
            },
            "actions": actions
        }
        
        if title:
            result["content"]["title"] = title
        
        return result
