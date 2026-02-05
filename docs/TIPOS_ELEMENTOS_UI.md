# Tipos de Elementos UI - Chatbot JNE

Este documento describe los tipos de elementos que el backend puede enviar al frontend a través de `response_rich`.

---

## 📋 Estructura General

Todas las respuestas enriquecidas (`response_rich`) tienen la siguiente estructura base:

```json
{
  "type": "menu" | "text" | "buttons" | "list" | "card",
  "content": {
    "text": "Texto principal del mensaje",
    "title": "Título opcional",
    "subtitle": "Subtítulo opcional"
  },
  ...
}
```

---

## 1. Tipo: `text` - Mensaje de Texto Simple

**Cuándo se usa:** Respuestas simples sin elementos interactivos.

**Estructura:**
```json
{
  "type": "text",
  "content": {
    "text": "Respuesta simple de texto del bot"
  }
}
```

**Ejemplo de uso:**
```json
{
  "type": "text",
  "content": {
    "text": "Gracias por tu consulta. ¿Hay algo más en lo que pueda ayudarte?"
  }
}
```

**Renderizado en frontend:**
- Mostrar el texto en un contenedor de mensaje del bot
- No requiere elementos interactivos adicionales

---

## 2. Tipo: `menu` - Menú con Opciones

**Cuándo se usa:** Cuando el usuario está navegando por menús del sistema.

**Estructura:**
```json
{
  "type": "menu",
  "content": {
    "text": "Texto introductorio del menú",
    "title": "Título del menú (opcional)"
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

**Ejemplo completo:**
```json
{
  "type": "menu",
  "content": {
    "text": "🤖 ELECCIA está aquí para ayudarte. ¿En qué más puedo asistirte?",
    "title": "Menú Principal"
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
    },
    {
      "type": "button",
      "label": "3. Información Institucional",
      "value": "3",
      "style": "primary"
    },
    {
      "type": "button",
      "label": "4. Servicios Digitales",
      "value": "4",
      "style": "primary"
    }
  ]
}
```

**Renderizado en frontend:**
1. Mostrar `title` (si existe) como encabezado
2. Mostrar `text` como descripción
3. Renderizar cada `action` como un botón
4. Al hacer clic en un botón, enviar el `value` como mensaje al backend

**Ejemplo de código frontend:**
```javascript
if (response_rich.type === 'menu') {
  // Mostrar título
  if (response_rich.content.title) {
    displayTitle(response_rich.content.title);
  }
  
  // Mostrar texto
  displayText(response_rich.content.text);
  
  // Renderizar botones
  response_rich.actions.forEach(action => {
    const button = createButton({
      label: action.label,
      value: action.value,
      style: action.style,
      onClick: () => sendMessage(action.value)
    });
    container.appendChild(button);
  });
}
```

---

## 3. Tipo: `buttons` - Botones de Acción

**Cuándo se usa:** Cuando se requiere una respuesta de sí/no o elección binaria.

**Estructura:**
```json
{
  "type": "buttons",
  "content": {
    "text": "¿Tienes otra consulta?"
  },
  "actions": [
    {
      "type": "button",
      "label": "Sí",
      "value": "si",
      "style": "primary"
    },
    {
      "type": "button",
      "label": "No",
      "value": "no",
      "style": "secondary"
    }
  ]
}
```

**Ejemplo completo:**
```json
{
  "type": "buttons",
  "content": {
    "text": "¿Deseas realizar otra consulta?"
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

**Renderizado en frontend:**
- Mostrar `content.text` como descripción
- Similar a `menu`, pero típicamente con 2 botones
- Los botones pueden tener diferentes estilos (`primary`, `secondary`)

**Ejemplo de código frontend:**
```javascript
if (response_rich.type === 'buttons') {
  displayText(response_rich.content.text);
  
  const buttonsContainer = createButtonsContainer();
  response_rich.actions.forEach(action => {
    const button = createButton({
      label: action.label,
      value: action.value,
      style: action.style,
      onClick: () => sendMessage(action.value)
    });
    buttonsContainer.appendChild(button);
  });
  container.appendChild(buttonsContainer);
}
```

---

## 4. Tipo: `list` - Lista de Items

**Cuándo se usa:** Para mostrar listas de servicios, hitos, candidatos, etc.

**Estructura:**
```json
{
  "type": "list",
  "content": {
    "text": "Servicios encontrados:",
    "title": "📋 Servicios Digitales (opcional)"
  },
  "items": [
    {
      "id": "1",
      "title": "Consulta de Afiliación",
      "description": "Consulta tu afiliación a organizaciones políticas",
      "value": "1"
    },
    {
      "id": "2",
      "title": "Consulta de Multas",
      "description": "Consulta multas electorales pendientes",
      "value": "2"
    }
  ]
}
```

**Ejemplo completo:**
```json
{
  "type": "list",
  "content": {
    "text": "Servicios más utilizados por la ciudadanía:",
    "title": "📋 Servicios Digitales"
  },
  "items": [
    {
      "id": "1",
      "title": "Consulta de Afiliación",
      "description": "Consulta tu afiliación a organizaciones políticas",
      "value": "1"
    },
    {
      "id": "2",
      "title": "Consulta de Multas Electorales",
      "description": "Consulta multas electorales pendientes de pago",
      "value": "2"
    },
    {
      "id": "3",
      "title": "Consulta de Candidatos",
      "description": "Consulta información sobre candidatos",
      "value": "3"
    }
  ]
}
```

**Renderizado en frontend:**
- Mostrar `content.title` (si existe) como encabezado
- Mostrar `content.text` como descripción
- Renderizar cada `item` como un elemento de lista clickeable
- Al hacer clic en un item, enviar el `value` como mensaje

**Ejemplo de código frontend:**
```javascript
if (response_rich.type === 'list') {
  if (response_rich.content.title) {
    displayTitle(response_rich.content.title);
  }
  displayText(response_rich.content.text);
  
  const listContainer = createListContainer();
  response_rich.items.forEach(item => {
    const listItem = createListItem({
      title: item.title,
      description: item.description,
      onClick: () => sendMessage(item.value)
    });
    listContainer.appendChild(listItem);
  });
  container.appendChild(listContainer);
}
```

---

## 5. Tipo: `card` - Tarjeta de Información

**Cuándo se usa:** Para mostrar información detallada de un item (político, funcionario, servicio, etc.).

**Estructura:**
```json
{
  "type": "card",
  "content": {
    "title": "👨‍⚖️ Presidente del JNE",
    "text": "Nombre: Dr. Jorge Luis Salas Arenas",
    "subtitle": "Descripción del cargo y funciones (opcional)"
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

**Ejemplo completo:**
```json
{
  "type": "card",
  "content": {
    "title": "👨‍⚖️ Presidente del JNE",
    "text": "Nombre: Dr. Jorge Luis Salas Arenas\nCargo: Presidente del Jurado Nacional de Elecciones",
    "subtitle": "Elegido para el período 2020-2025"
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

**Renderizado en frontend:**
- Mostrar `content.title` como encabezado de la tarjeta
- Mostrar `content.text` como contenido principal
- Mostrar `content.subtitle` (si existe) como información adicional
- Renderizar `actions` como botones al final de la tarjeta

**Ejemplo de código frontend:**
```javascript
if (response_rich.type === 'card') {
  const card = createCard();
  
  const title = createCardTitle(response_rich.content.title);
  card.appendChild(title);
  
  const text = createCardText(response_rich.content.text);
  card.appendChild(text);
  
  if (response_rich.content.subtitle) {
    const subtitle = createCardSubtitle(response_rich.content.subtitle);
    card.appendChild(subtitle);
  }
  
  if (response_rich.actions) {
    const actionsContainer = createActionsContainer();
    response_rich.actions.forEach(action => {
      const button = createButton({
        label: action.label,
        value: action.value,
        style: action.style,
        onClick: () => sendMessage(action.value)
      });
      actionsContainer.appendChild(button);
    });
    card.appendChild(actionsContainer);
  }
  
  container.appendChild(card);
}
```

---

## 🎨 Estilos de Botones

Los botones pueden tener diferentes estilos:

- **`primary`**: Botón principal (azul, destacado)
- **`secondary`**: Botón secundario (gris, menos destacado)
- **`danger`**: Botón de acción destructiva (rojo) - *No usado actualmente*
- **`success`**: Botón de éxito (verde) - *No usado actualmente*

**Ejemplo de estilos CSS:**
```css
.btn-primary {
  background: #667eea;
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-success {
  background: #4caf50;
  color: white;
}
```

---

## 📤 Formato de Respuesta Completa

Cuando el backend envía una respuesta, incluye tanto `response` (texto plano) como `response_rich` (estructurado):

```json
{
  "type": "message",
  "content": "Menú principal:\n1. Procesos Electorales\n2. Organizaciones Políticas...",
  "response_rich": {
    "type": "menu",
    "content": {
      "text": "🤖 ELECCIA está aquí para ayudarte",
      "title": "Menú Principal"
    },
    "actions": [
      {
        "type": "button",
        "label": "1. Procesos Electorales",
        "value": "1",
        "style": "primary"
      }
    ]
  },
  "state": {...},
  "menu_actual": "main",
  "conversation_active": true,
  "should_finalize": false,
  "timestamp": "2025-01-21T22:25:29.361159"
}
```

---

## 🔄 Flujo de Interacción

1. **Usuario envía mensaje** → Frontend envía `{"type": "message", "message": "1"}`
2. **Backend procesa** → Genera `response` (texto) y `response_rich` (estructurado)
3. **Backend envía respuesta** → Frontend recibe ambos formatos
4. **Frontend renderiza** → Usa `response_rich` si existe, sino usa `content`
5. **Usuario interactúa** → Hace clic en botón/item → Envía `value` como mensaje
6. **Ciclo se repite**

---

## ✅ Checklist de Implementación Frontend

- [ ] Detectar tipo de `response_rich`
- [ ] Renderizar `content.text` en todos los tipos
- [ ] Renderizar `content.title` cuando exista
- [ ] Renderizar `content.subtitle` cuando exista (para `card`)
- [ ] Renderizar botones para `menu` y `buttons`
- [ ] Renderizar lista para `list`
- [ ] Renderizar tarjeta para `card`
- [ ] Manejar clics en botones/items (enviar `value` como mensaje)
- [ ] Aplicar estilos según `style` de cada botón
- [ ] Fallback a `content` si `response_rich` no existe

---

## 🐛 Troubleshooting

### No recibo `response_rich`
- Verifica que `platform="web"` en el backend
- Verifica que el estado actual permita generar `response_rich`
- Usa `content` como fallback

### Los botones no funcionan
- Verifica que estés enviando el `value` correcto
- Verifica que el WebSocket esté conectado
- Revisa la consola del navegador para errores

### El tipo no coincide
- Verifica que estés usando el `type` correcto del objeto
- Algunos tipos pueden no estar implementados aún

---

## 📝 Notas Adicionales

- **Compatibilidad:** Si `response_rich` es `null` o no existe, siempre usar `content` (texto plano)
- **Extensibilidad:** Se pueden agregar nuevos tipos en el futuro sin romper compatibilidad
- **Performance:** El frontend puede cachear estilos y componentes para mejor rendimiento
