# API de Chat Web - Documentación

## Endpoints Disponibles

### 1. WebSocket (Tiempo Real) - Recomendado

**Endpoint:** `WS /api/web/chat/ws`

**Conexión:**
```javascript
// Opción 1: Con user_id en query params
const ws = new WebSocket('ws://localhost:8000/api/web/chat/ws?user_id=mi_usuario_123');

// Opción 2: Sin query params (se enviará en primer mensaje)
const ws = new WebSocket('ws://localhost:8000/api/web/chat/ws');
```

**Mensajes del Cliente:**

1. **Inicialización (si no se pasó user_id en query):**
```json
{
  "type": "init",
  "user_id": "mi_usuario_123"
}
```

2. **Enviar mensaje:**
```json
{
  "type": "message",
  "message": "Hola, quiero información sobre procesos electorales"
}
```

3. **Ping (mantener conexión viva):**
```json
{
  "type": "ping"
}
```

4. **Cerrar conexión:**
```json
{
  "type": "close"
}
```

**Respuestas del Servidor:**

1. **Mensaje del bot:**
```json
{
  "type": "message",
  "content": "Respuesta del bot...",
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

2. **Mensaje de sistema:**
```json
{
  "type": "system",
  "content": "Conexión restablecida...",
  "state": {...},
  "conversation_active": true,
  "timestamp": "2025-01-XXT..."
}
```

3. **Error:**
```json
{
  "type": "error",
  "content": "Mensaje de error",
  "timestamp": "2025-01-XXT..."
}
```

4. **Pong (respuesta a ping):**
```json
{
  "type": "pong",
  "timestamp": "2025-01-XXT..."
}
```

**Ejemplo de Uso (JavaScript):**

```javascript
const ws = new WebSocket('ws://localhost:8000/api/web/chat/ws?user_id=usuario_123');

ws.onopen = () => {
  console.log('Conectado al chat');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'message') {
    console.log('Bot:', data.content);
    // Mostrar mensaje en la interfaz
    displayMessage(data.content, 'bot');
  } else if (data.type === 'error') {
    console.error('Error:', data.content);
  }
};

ws.onerror = (error) => {
  console.error('Error WebSocket:', error);
};

ws.onclose = () => {
  console.log('Conexión cerrada');
};

// Enviar mensaje
function sendMessage(text) {
  ws.send(JSON.stringify({
    type: 'message',
    message: text
  }));
}

// Mantener conexión viva (cada 30 segundos)
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

---

### 2. REST API (Alternativa)

**Endpoint:** `POST /api/web/chat/message`

**Request:**
```json
{
  "user_id": "mi_usuario_123",
  "message": "Hola, quiero información sobre procesos electorales",
  "metadata": {
    "session_id": "session_abc123",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1"
  }
}
```

**Response:**
```json
{
  "response": "Respuesta del bot...",
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

**Ejemplo de Uso (JavaScript):**

```javascript
async function sendMessage(userId, message) {
  const response = await fetch('http://localhost:8000/api/web/chat/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      message: message
    })
  });
  
  const data = await response.json();
  return data;
}
```

---

### 3. Iniciar Conversación

**Endpoint:** `POST /api/web/chat/start`

**Request:**
```json
{
  "user_id": "mi_usuario_123",
  "metadata": {
    "session_id": "session_abc123"
  }
}
```

**Response:**
```json
{
  "user_id": "mi_usuario_123",
  "welcome_message": "Mensaje de bienvenida completo...",
  "conversation_started": true,
  "timestamp": "2025-01-XXT..."
}
```

---

### 4. Obtener Historial

**Endpoint:** `GET /api/web/chat/history/{user_id}`

**Response:**
```json
{
  "conversation": {
    "user_id": "mi_usuario_123",
    "mensajes": [...],
    "estado_actual": {...},
    "metadata": {...}
  },
  "active": true,
  "timestamp": "2025-01-XXT..."
}
```

---

### 5. Estado de Conexión

**Endpoint:** `GET /api/web/chat/status/{user_id}`

**Response:**
```json
{
  "connected": true,
  "active_connections": 5,
  "timestamp": "2025-01-XXT..."
}
```

---

## Códigos de Cierre WebSocket

- `1000`: Cierre normal (conversación finalizada o cliente solicita cierre)
- `1008`: Error de validación (user_id requerido)
- `1011`: Error interno del servidor

---

## Manejo de Errores

### WebSocket
- Si la conexión se pierde, el cliente debe reconectar
- El servidor mantiene el estado de la conversación en Redis
- Al reconectar, se restablece la conversación automáticamente

### REST API
- Errores HTTP estándar (400, 500, etc.)
- Respuestas de error incluyen campo `error` con descripción

---

## Identificación de Usuarios

El sistema acepta:
- `user_id`: ID único del usuario (recomendado)
- `session_id`: ID de sesión (alternativa)

**Importante:** Si un usuario usa múltiples canales (Telegram, WhatsApp, Web), cada uno debe tener un `user_id` único para evitar conflictos de estado.

**Recomendación:** Usar prefijos:
- `telegram_123456789`
- `whatsapp_123456789`
- `web_abc123` o `web_session_xyz`

---

## Ejemplo Completo de Frontend

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot JNE</title>
    <style>
        #chat-container {
            max-width: 600px;
            margin: 0 auto;
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 20px;
        }
        #messages {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #eee;
            padding: 10px;
            margin-bottom: 10px;
        }
        .message {
            margin: 10px 0;
            padding: 8px;
            border-radius: 4px;
        }
        .user-message {
            background-color: #e3f2fd;
            text-align: right;
        }
        .bot-message {
            background-color: #f5f5f5;
        }
        #input-container {
            display: flex;
            gap: 10px;
        }
        #message-input {
            flex: 1;
            padding: 8px;
        }
        #send-button {
            padding: 8px 16px;
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <h1>Chatbot JNE - ELECCIA</h1>
        <div id="messages"></div>
        <div id="input-container">
            <input type="text" id="message-input" placeholder="Escribe tu mensaje...">
            <button id="send-button">Enviar</button>
        </div>
    </div>

    <script>
        // Generar user_id único para esta sesión
        const userId = 'web_' + Math.random().toString(36).substring(2, 15);
        const ws = new WebSocket(`ws://localhost:8000/api/web/chat/ws?user_id=${userId}`);
        
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        
        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        ws.onopen = () => {
            addMessage('Conectado al chat...', false);
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'message') {
                addMessage(data.content, false);
            } else if (data.type === 'system') {
                addMessage('ℹ️ ' + data.content, false);
            } else if (data.type === 'error') {
                addMessage('❌ Error: ' + data.content, false);
            }
        };
        
        ws.onerror = (error) => {
            addMessage('❌ Error de conexión', false);
        };
        
        ws.onclose = () => {
            addMessage('Conexión cerrada', false);
        };
        
        function sendMessage() {
            const message = messageInput.value.trim();
            if (message && ws.readyState === WebSocket.OPEN) {
                addMessage(message, true);
                ws.send(JSON.stringify({
                    type: 'message',
                    message: message
                }));
                messageInput.value = '';
            }
        }
        
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Mantener conexión viva
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    </script>
</body>
</html>
```

---

## Notas Importantes

1. **Estado Persistente:** El estado de la conversación se mantiene en Redis por 30 minutos de inactividad
2. **Reconexión:** Si se pierde la conexión WebSocket, el estado se mantiene y se puede reconectar
3. **Múltiples Conexiones:** Un usuario puede tener solo una conexión WebSocket activa a la vez
4. **Rate Limiting:** Considerar implementar rate limiting en producción
5. **Seguridad:** En producción, implementar autenticación y validación de user_id

---

**Documento creado:** Enero 2025
