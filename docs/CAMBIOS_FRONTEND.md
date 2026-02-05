# Cambios en la Comunicación Frontend ↔ Backend

## ✅ Lo que NO cambia (Frontend → Backend)

### Request del Frontend (Sigue igual)

#### REST API:
```javascript
// El frontend sigue enviando exactamente lo mismo
POST /api/web/chat/message
{
  "user_id": "test123",
  "message": "Hola"
}
```

#### WebSocket:
```javascript
// El frontend sigue enviando exactamente lo mismo
ws.send(JSON.stringify({
  type: "message",
  message: "Hola"
}));
```

**✅ NO necesitas cambiar NADA en el código que envía requests**

---

## 🔄 Lo que SÍ cambia (Backend → Frontend)

### Response del Backend (Ahora incluye `response_rich`)

#### Antes (Solo texto):
```json
{
  "response": "Menú principal:\n1. Procesos Electorales...",
  "state": {...},
  "menu_actual": "main",
  "conversation_active": true,
  "should_finalize": false,
  "timestamp": "..."
}
```

#### Ahora (Híbrido - Texto + Estructurado):
```json
{
  "response": "Menú principal:\n1. Procesos Electorales...",  // ← Sigue igual (compatible)
  "response_rich": {  // ← NUEVO: Estructura enriquecida
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
  "timestamp": "..."
}
```

---

## 📝 Cambios Necesarios en el Frontend

### Opción 1: Usar `response_rich` (Recomendado)

```javascript
// Ejemplo: React/Vue/Angular
async function sendMessage(userId, message) {
  const response = await fetch('/api/web/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message })
  });
  
  const data = await response.json();
  
  // ✅ Usar response_rich si existe, sino usar response
  if (data.response_rich) {
    renderRichMessage(data.response_rich);
  } else {
    renderTextMessage(data.response); // Fallback
  }
}

function renderRichMessage(rich) {
  switch(rich.type) {
    case 'menu':
      // Renderizar botones
      rich.actions.forEach(action => {
        createButton(action.label, action.value);
      });
      break;
      
    case 'text':
      // Renderizar texto simple
      displayText(rich.content.text);
      break;
      
    case 'list':
      // Renderizar lista scrollable
      rich.items.forEach(item => {
        createListItem(item);
      });
      break;
      
    case 'buttons':
      // Renderizar botones de acción
      rich.actions.forEach(action => {
        createActionButton(action);
      });
      break;
      
    case 'card':
      // Renderizar tarjeta de información
      createCard(rich.content);
      break;
      
    case 'form':
      // Mostrar campo de entrada
      showInputField(rich.input);
      break;
  }
}
```

### Opción 2: Seguir usando `response` (Sin cambios)

```javascript
// Si prefieres no cambiar nada todavía
async function sendMessage(userId, message) {
  const response = await fetch('/api/web/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message })
  });
  
  const data = await response.json();
  
  // ✅ Seguir usando response (texto plano)
  displayMessage(data.response); // Funciona igual que antes
}
```

---

## 🔌 WebSocket - Cambios

### Lo que envías (NO cambia):
```javascript
// ✅ Sigue igual
ws.send(JSON.stringify({
  type: "message",
  message: "Hola"
}));
```

### Lo que recibes (SÍ cambia):
```javascript
// Antes
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content); // Solo texto
};

// Ahora
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // ✅ Puedes usar response_rich si existe
  if (data.response_rich) {
    renderRichMessage(data.response_rich);
  } else {
    displayMessage(data.content); // Fallback a texto
  }
};
```

---

## 📋 Resumen

| Aspecto | Cambia | No Cambia |
|--------|--------|-----------|
| **Request del Frontend** | ❌ | ✅ |
| **Response del Backend** | ✅ (agrega `response_rich`) | ✅ (mantiene `response`) |
| **Código de envío** | ❌ | ✅ |
| **Código de recepción** | ✅ (opcional usar `response_rich`) | ✅ (puede seguir usando `response`) |

---

## 🎯 Recomendación

1. **Fase 1 (Sin cambios):** Seguir usando `response` como antes
2. **Fase 2 (Progresivo):** Agregar soporte para `response_rich` cuando exista
3. **Fase 3 (Completo):** Usar solo `response_rich` y `response` como fallback

**Ejemplo de implementación progresiva:**

```javascript
function handleResponse(data) {
  // Priorizar response_rich, fallback a response
  if (data.response_rich) {
    try {
      renderRichMessage(data.response_rich);
    } catch (e) {
      // Si falla, usar texto plano
      console.warn('Error renderizando rich, usando texto:', e);
      displayTextMessage(data.response);
    }
  } else {
    // Compatibilidad con versiones anteriores
    displayTextMessage(data.response);
  }
}
```

---

## ✅ Conclusión

**El frontend NO necesita cambiar nada para seguir funcionando**, pero **puede aprovechar `response_rich`** para mejorar la UI cuando esté listo.

Es una migración **progresiva y opcional**.
