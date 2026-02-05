# Guía de Pruebas en Postman - Chatbot JNE

## Configuración Base

**Base URL:** `http://localhost:8001`

---

## 1. Health Check

### GET `/health`

**Configuración:**
- **Método:** `GET`
- **URL:** `http://localhost:8001/health`
- **Headers:** Ninguno necesario

**Respuesta esperada:**
```json
{
  "status": "ok"
}
```

---

## 2. REST API - Enviar Mensaje

### POST `/api/web/chat/message`

**Configuración:**
- **Método:** `POST`
- **URL:** `http://localhost:8001/api/web/chat/message`
- **Headers:**
  - `Content-Type: application/json`
- **Body (raw JSON):**
```json
{
  "user_id": "test_postman_123",
  "message": "Hola, quiero información sobre procesos electorales"
}
```

**Respuesta esperada:**
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

**Ejemplos de mensajes para probar:**
```json
// Menú principal
{"user_id": "test1", "message": "1"}

// Procesos electorales
{"user_id": "test2", "message": "Quiero información sobre elecciones generales 2026"}

// Consulta de político
{"user_id": "test3", "message": "Busco información sobre Juan Pérez"}

// Servicios digitales
{"user_id": "test4", "message": "Necesito información sobre multas electorales"}
```

---

## 3. Iniciar Conversación

### POST `/api/web/chat/start`

**Configuración:**
- **Método:** `POST`
- **URL:** `http://localhost:8001/api/web/chat/start`
- **Headers:**
  - `Content-Type: application/json`
- **Body (raw JSON):**
```json
{
  "user_id": "test_postman_123",
  "metadata": {
    "session_id": "session_abc123",
    "user_agent": "Postman/1.0"
  }
}
```

**O sin body (usa query params o genera user_id automáticamente):**
- **URL:** `http://localhost:8001/api/web/chat/start?user_id=test_postman_123`
- **Body:** Vacío o sin enviar

**Respuesta esperada:**
```json
{
  "user_id": "test_postman_123",
  "welcome_message": "🤖 **¡Hola! Soy ELECCIA...**\n\nMenú principal:\n1. Procesos Electorales...",
  "conversation_started": true,
  "timestamp": "2025-01-XXT..."
}
```

---

## 4. Obtener Historial de Conversación

### GET `/api/web/chat/history/{user_id}`

**Configuración:**
- **Método:** `GET`
- **URL:** `http://localhost:8001/api/web/chat/history/test_postman_123`
- **Headers:** Ninguno necesario

**Respuesta esperada (si hay conversación activa):**
```json
{
  "conversation": {
    "user_id": "test_postman_123",
    "mensajes": [...],
    "estado_actual": {...},
    "metadata": {...}
  },
  "active": true,
  "timestamp": "2025-01-XXT..."
}
```

**Respuesta esperada (si no hay conversación activa):**
```json
{
  "conversation": null,
  "active": false,
  "message": "No hay conversación activa para este usuario",
  "timestamp": "2025-01-XXT..."
}
```

---

## 5. Estado de Conexión WebSocket

### GET `/api/web/chat/status/{user_id}`

**Configuración:**
- **Método:** `GET`
- **URL:** `http://localhost:8001/api/web/chat/status/test_postman_123`
- **Headers:** Ninguno necesario

**Respuesta esperada:**
```json
{
  "connected": false,
  "active_connections": 0,
  "timestamp": "2025-01-XXT..."
}
```

---

## 6. WebSocket (No disponible en Postman)

**Nota:** Postman no soporta WebSocket directamente. Para probar WebSocket:

### Opción A: Usar herramienta WebSocket
- **Herramientas recomendadas:**
  - [WebSocket King](https://websocketking.com/)
  - [WebSocket.org Echo Test](https://www.websocket.org/echo.html)
  - Extensión de Chrome: "WebSocket King Client"

**Configuración:**
- **URL:** `ws://localhost:8001/api/web/chat/ws?user_id=test123`
- **Mensaje inicial (opcional):**
```json
{
  "type": "init",
  "user_id": "test123"
}
```
- **Enviar mensaje:**
```json
{
  "type": "message",
  "message": "Hola"
}
```

### Opción B: Usar navegador
Abre la consola del navegador en `http://localhost:8001` y ejecuta:
```javascript
const ws = new WebSocket('ws://localhost:8001/api/web/chat/ws?user_id=test123');
ws.onmessage = (e) => console.log('Bot:', JSON.parse(e.data).content);
ws.onopen = () => ws.send(JSON.stringify({type: 'message', message: 'Hola'}));
```

---

## Colección de Postman

### Importar Colección

Crea una nueva colección en Postman llamada "Chatbot JNE" y agrega estas requests:

#### 1. Health Check
```
GET http://localhost:8001/health
```

#### 2. Enviar Mensaje
```
POST http://localhost:8001/api/web/chat/message
Content-Type: application/json

{
  "user_id": "{{user_id}}",
  "message": "{{message}}"
}
```

#### 3. Iniciar Conversación
```
POST http://localhost:8001/api/web/chat/start
Content-Type: application/json

{
  "user_id": "{{user_id}}"
}
```

#### 4. Obtener Historial
```
GET http://localhost:8001/api/web/chat/history/{{user_id}}
```

#### 5. Estado de Conexión
```
GET http://localhost:8001/api/web/chat/status/{{user_id}}
```

### Variables de Colección

Crea variables en la colección:
- `base_url`: `http://localhost:8001`
- `user_id`: `test_postman_123`
- `message`: `Hola`

---

## Flujo de Prueba Recomendado

### Paso 1: Verificar que el servidor está funcionando
```
GET /health
```
✅ Debe retornar `{"status": "ok"}`

### Paso 2: Iniciar una conversación
```
POST /api/web/chat/start
Body: {"user_id": "test_postman_123"}
```
✅ Debe retornar mensaje de bienvenida

### Paso 3: Enviar un mensaje
```
POST /api/web/chat/message
Body: {
  "user_id": "test_postman_123",
  "message": "1"
}
```
✅ Debe retornar el menú de procesos electorales

### Paso 4: Continuar la conversación
```
POST /api/web/chat/message
Body: {
  "user_id": "test_postman_123",
  "message": "1"
}
```
✅ Debe retornar el cronograma electoral

### Paso 5: Verificar historial
```
GET /api/web/chat/history/test_postman_123
```
✅ Debe mostrar la conversación completa

---

## Ejemplos de Conversaciones Completas

### Ejemplo 1: Consulta de Procesos Electorales

**Request 1:**
```json
POST /api/web/chat/message
{
  "user_id": "test1",
  "message": "1"
}
```
**Respuesta:** Menú de Procesos Electorales

**Request 2:**
```json
POST /api/web/chat/message
{
  "user_id": "test1",
  "message": "1"
}
```
**Respuesta:** Menú de Cronograma Electoral

**Request 3:**
```json
POST /api/web/chat/message
{
  "user_id": "test1",
  "message": "EG.2026"
}
```
**Respuesta:** Pide consulta sobre hitos

**Request 4:**
```json
POST /api/web/chat/message
{
  "user_id": "test1",
  "message": "¿Cuándo son las elecciones generales?"
}
```
**Respuesta:** Lista de hitos relevantes

---

### Ejemplo 2: Consulta de Político

**Request 1:**
```json
POST /api/web/chat/message
{
  "user_id": "test2",
  "message": "1"
}
```
**Respuesta:** Menú principal

**Request 2:**
```json
POST /api/web/chat/message
{
  "user_id": "test2",
  "message": "2"
}
```
**Respuesta:** Menú de Consulta tu Político

**Request 3:**
```json
POST /api/web/chat/message
{
  "user_id": "test2",
  "message": "Juan Pérez García"
}
```
**Respuesta:** Lista de candidatos encontrados

---

## Códigos de Estado HTTP

- **200 OK:** Request exitoso
- **400 Bad Request:** Body inválido o faltante
- **404 Not Found:** Endpoint no existe
- **500 Internal Server Error:** Error del servidor

---

## Troubleshooting en Postman

### Error: "Connection refused"
- Verifica que el contenedor esté corriendo: `docker ps`
- Verifica que el puerto 8001 esté expuesto

### Error: "JSON decode error"
- Verifica que el Content-Type sea `application/json`
- Verifica que el JSON esté bien formateado
- Usa el formato "raw" y selecciona "JSON" en Postman

### Error: "500 Internal Server Error"
- Revisa los logs: `docker logs chatbot_app`
- Verifica que las bases de datos estén conectadas

### No recibo respuesta
- Verifica que el servidor esté funcionando: `/health`
- Revisa los logs del contenedor
- Verifica que el `user_id` sea consistente en todas las requests

---

## Tips para Postman

1. **Usa Variables:** Crea variables `{{user_id}}` y `{{base_url}}` para reutilizar
2. **Guarda Requests:** Guarda las requests exitosas en una colección
3. **Tests Automáticos:** Agrega tests en Postman para validar respuestas
4. **Environments:** Crea environments para desarrollo/producción

### Ejemplo de Test en Postman:
```javascript
// En la pestaña "Tests" de Postman
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has response field", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('response');
});
```

---

**Última actualización:** Enero 2025
