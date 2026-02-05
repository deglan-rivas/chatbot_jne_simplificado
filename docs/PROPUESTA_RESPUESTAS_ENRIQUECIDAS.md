# Propuesta: Respuestas Enriquecidas para Frontend Web

## Problema Actual

La respuesta actual es texto plano con markdown, adecuado para Telegram pero limitado para un frontend web moderno:

```json
{
  "response": "Menú principal:\n1. Procesos Electorales\n2. Organizaciones Políticas...",
  "state": {...},
  "menu_actual": "main"
}
```

**Limitaciones:**
- ❌ No permite renderizar botones interactivos
- ❌ No separa contenido de formato
- ❌ No permite diferentes tipos de mensajes (texto, botones, imágenes, etc.)
- ❌ El frontend debe parsear markdown manualmente
- ❌ No hay estructura para elementos UI complejos

---

## Solución Propuesta: Respuestas Estructuradas

### Opción 1: Respuesta Híbrida (Recomendada) ⭐

Mantener compatibilidad con Telegram/WhatsApp pero agregar estructura enriquecida para web.

**Estructura de Respuesta:**

```json
{
  "response": "Texto plano (compatible con Telegram/WhatsApp)",
  "response_rich": {
    "type": "menu" | "text" | "buttons" | "list" | "card",
    "content": {
      "text": "Texto principal del mensaje",
      "title": "Título opcional",
      "subtitle": "Subtítulo opcional"
    },
    "actions": [
      {
        "type": "button",
        "label": "Procesos Electorales",
        "value": "1",
        "style": "primary" | "secondary" | "danger"
      },
      {
        "type": "button",
        "label": "Organizaciones Políticas",
        "value": "2",
        "style": "primary"
      }
    ],
    "metadata": {
      "show_typing": true,
      "delay": 500
    }
  },
  "state": {...},
  "menu_actual": "main",
  "conversation_active": true,
  "should_finalize": false,
  "timestamp": "..."
}
```

**Ventajas:**
- ✅ Compatible con Telegram/WhatsApp (usan `response`)
- ✅ Frontend web usa `response_rich` para UI enriquecida
- ✅ No rompe funcionalidad existente
- ✅ Flexible y extensible

---

### Opción 2: Respuesta Completamente Estructurada

Solo estructura enriquecida, sin texto plano.

**Estructura:**

```json
{
  "message": {
    "type": "menu" | "text" | "buttons" | "list" | "card" | "form",
    "content": {
      "text": "Texto del mensaje",
      "title": "Título",
      "subtitle": "Subtítulo"
    },
    "interactive": {
      "type": "buttons",
      "options": [
        {
          "id": "1",
          "label": "Procesos Electorales",
          "action": "menu_option",
          "style": "primary"
        }
      ]
    },
    "metadata": {
      "show_typing": true,
      "delay": 500
    }
  },
  "state": {...},
  "conversation_active": true
}
```

**Ventajas:**
- ✅ Más limpio y estructurado
- ✅ Mejor para frontend moderno

**Desventajas:**
- ❌ Requiere cambios en Telegram/WhatsApp
- ❌ Más trabajo de refactorización

---

## Recomendación: Opción 1 (Híbrida)

### Tipos de Mensajes Soportados

#### 1. **Tipo: `text`** (Mensaje simple)
```json
{
  "type": "text",
  "content": {
    "text": "Respuesta simple de texto"
  }
}
```

#### 2. **Tipo: `menu`** (Menú con opciones)
```json
{
  "type": "menu",
  "content": {
    "text": "Menú principal:",
    "title": "🤖 ELECCIA - Menú Principal"
  },
  "actions": [
    {
      "type": "button",
      "label": "1. Procesos Electorales",
      "value": "1",
      "style": "primary"
    },
    {
      "type": "button",
      "label": "2. Organizaciones Políticas",
      "value": "2",
      "style": "primary"
    }
  ]
}
```

#### 3. **Tipo: `buttons`** (Botones de acción)
```json
{
  "type": "buttons",
  "content": {
    "text": "¿Qué deseas hacer?"
  },
  "actions": [
    {
      "type": "button",
      "label": "Sí, tengo otra consulta",
      "value": "si",
      "style": "primary"
    },
    {
      "type": "button",
      "label": "No, finalizar",
      "value": "no",
      "style": "secondary"
    }
  ]
}
```

#### 4. **Tipo: `list`** (Lista de items)
```json
{
  "type": "list",
  "content": {
    "text": "Servicios encontrados:",
    "title": "📋 Servicios Digitales"
  },
  "items": [
    {
      "id": "1",
      "title": "Consulta de Afiliación",
      "description": "Consulta tu afiliación a organizaciones políticas",
      "action": "select_service",
      "value": "1"
    }
  ]
}
```

#### 5. **Tipo: `card`** (Tarjeta con información)
```json
{
  "type": "card",
  "content": {
    "title": "👨‍⚖️ Presidente del JNE",
    "text": "Nombre: Dr. Jorge Luis Salas Arenas",
    "subtitle": "Descripción del cargo..."
  },
  "actions": [
    {
      "type": "button",
      "label": "Volver al menú",
      "value": "menu",
      "style": "secondary"
    }
  ]
}
```

#### 6. **Tipo: `form`** (Formulario de entrada)
```json
{
  "type": "form",
  "content": {
    "text": "Por favor, proporciona el nombre del político:",
    "title": "👤 Consulta tu Político"
  },
  "input": {
    "type": "text",
    "placeholder": "Ej: Juan Pérez García",
    "required": true
  }
}
```

---

## Estructura de Acciones (Actions)

```typescript
interface Action {
  type: "button" | "link" | "quick_reply";
  label: string;           // Texto visible
  value: string;           // Valor a enviar cuando se selecciona
  style?: "primary" | "secondary" | "danger" | "success";
  icon?: string;           // Emoji o icono opcional
  action?: string;          // Tipo de acción (menu_option, command, etc.)
}
```

---

## Implementación Propuesta

### 1. Crear `ResponseBuilder` para Web

```python
# chatbot/utils/response_builder.py
class ResponseBuilder:
    """Construye respuestas enriquecidas para frontend web"""
    
    @staticmethod
    def build_menu_response(text: str, menu_options: dict, title: str = None):
        """Construye respuesta de tipo menú"""
        actions = []
        for value, label in menu_options.items():
            actions.append({
                "type": "button",
                "label": label,
                "value": value,
                "style": "primary",
                "action": "menu_option"
            })
        
        return {
            "type": "menu",
            "content": {
                "text": text,
                "title": title
            },
            "actions": actions
        }
    
    @staticmethod
    def build_text_response(text: str):
        """Construye respuesta de tipo texto simple"""
        return {
            "type": "text",
            "content": {
                "text": text
            }
        }
    
    @staticmethod
    def build_list_response(text: str, items: list, title: str = None):
        """Construye respuesta de tipo lista"""
        return {
            "type": "list",
            "content": {
                "text": text,
                "title": title
            },
            "items": items
        }
```

### 2. Modificar `ChatbotService` para generar `response_rich`

```python
# En chatbot_service.py
async def process_message(...) -> Dict[str, Any]:
    # ... lógica existente ...
    
    # Generar respuesta enriquecida solo para web
    response_rich = None
    if platform == "web":
        response_rich = ResponseBuilder.build_response(
            response_text=respuesta,
            state=state,
            menu_actual=menu_actual
        )
    
    return {
        "response": respuesta,  # Texto plano (compatible)
        "response_rich": response_rich,  # Estructura enriquecida (solo web)
        "state": state,
        "menu_actual": menu_actual,
        ...
    }
```

### 3. Detectar tipo de respuesta automáticamente

El `ResponseBuilder` debe analizar el estado y el menú actual para determinar el tipo:

- Si `state["stage"]` está en `menus` → tipo `menu`
- Si hay opciones de sí/no → tipo `buttons`
- Si hay lista de servicios/hitos → tipo `list`
- Si es información de un item → tipo `card`
- Por defecto → tipo `text`

---

## Ejemplo de Respuesta Completa

### Request:
```json
POST /api/web/chat/message
{
  "user_id": "test123",
  "message": "1"
}
```

### Response (Opción 1 - Híbrida):
```json
{
  "response": "Menú principal:\n1. Procesos Electorales\n2. Organizaciones Políticas\n3. Información Institucional\n4. Servicios Digitales",
  "response_rich": {
    "type": "menu",
    "content": {
      "text": "🤖 **ELECCIA** está aquí para ayudarte. ¿En qué más puedo asistirte?",
      "title": "Menú Principal"
    },
    "actions": [
      {
        "type": "button",
        "label": "1. Procesos Electorales",
        "value": "1",
        "style": "primary",
        "action": "menu_option"
      },
      {
        "type": "button",
        "label": "2. Organizaciones Políticas",
        "value": "2",
        "style": "primary",
        "action": "menu_option"
      },
      {
        "type": "button",
        "label": "3. Información Institucional",
        "value": "3",
        "style": "primary",
        "action": "menu_option"
      },
      {
        "type": "button",
        "label": "4. Servicios Digitales",
        "value": "4",
        "style": "primary",
        "action": "menu_option"
      }
    ],
    "metadata": {
      "show_typing": false,
      "delay": 0
    }
  },
  "state": {
    "stage": "main",
    "flow": []
  },
  "menu_actual": "main",
  "conversation_active": true,
  "should_finalize": false,
  "timestamp": "2025-01-XXT..."
}
```

---

## Ventajas de esta Solución

1. ✅ **No rompe funcionalidad existente:** Telegram/WhatsApp siguen usando `response`
2. ✅ **Frontend flexible:** Puede elegir usar `response` (texto) o `response_rich` (estructurado)
3. ✅ **Extensible:** Fácil agregar nuevos tipos de mensajes
4. ✅ **Progresivo:** Se puede implementar gradualmente
5. ✅ **Backward compatible:** Si `response_rich` es null, usar `response`

---

## Consideraciones Adicionales

### 1. Parsing de Markdown
- El frontend puede usar `response` y parsear markdown
- O usar `response_rich` que ya está estructurado

### 2. Comandos Especiales
- `menu` → Botón de "Volver al menú"
- `adios` → Botón de "Finalizar conversación"

### 3. Estados Especiales
- `awaiting_input` → Mostrar campo de entrada
- `awaiting_selection` → Mostrar lista/botones
- `showing_info` → Mostrar tarjeta con información

---

## Preguntas para Decidir

1. **¿Quieres mantener compatibilidad con Telegram/WhatsApp?**
   - ✅ Sí → Opción 1 (Híbrida)
   - ❌ No → Opción 2 (Solo estructurada)

2. **¿Qué tipos de UI necesitas en el frontend?**
   - Botones simples
   - Listas scrollables
   - Tarjetas de información
   - Formularios de entrada
   - Imágenes/archivos

3. **¿Prefieres que el backend determine el tipo o el frontend?**
   - Backend determina → Más control, menos flexibilidad
   - Frontend determina → Más flexibilidad, más trabajo en frontend

---

## Recomendación Final

**Opción 1 (Híbrida)** porque:
- ✅ No rompe nada existente
- ✅ Permite migración gradual
- ✅ Frontend puede elegir qué usar
- ✅ Fácil de implementar
- ✅ Extensible para futuras necesidades

¿Te parece bien esta propuesta? ¿Quieres que ajuste algo antes de implementar?
