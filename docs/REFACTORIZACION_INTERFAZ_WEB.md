# Refactorización para Interfaz Web de Chat
## Análisis y Plan de Implementación

**Fecha:** Enero 2025  
**Objetivo:** Agregar interfaz web de chat sin romper funcionalidad existente (Telegram/WhatsApp)

---

## 📋 ÍNDICE

1. [Análisis de la Estructura Actual](#1-análisis-de-la-estructura-actual)
2. [Impacto de Agregar Interfaz Web](#2-impacto-de-agregar-interfaz-web)
3. [Refactorizaciones Necesarias](#3-refactorizaciones-necesarias)
4. [Plan de Implementación Priorizado](#4-plan-de-implementación-priorizado)
5. [Código de Ejemplo](#5-código-de-ejemplo)

---

## 1. ANÁLISIS DE LA ESTRUCTURA ACTUAL

### 1.1 Arquitectura Actual

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Routes                        │
├─────────────────┬─────────────────┬─────────────────────┤
│  Telegram Route │  WhatsApp Route │  API Gateway Route   │
│  (telegram.py)  │  (whatsapp.py)  │  (api_gateway.py)   │
└────────┬────────┴────────┬────────┴──────────┬──────────┘
         │                  │                   │
         └──────────────────┼───────────────────┘
                            │
         ┌──────────────────▼──────────────────┐
         │    Chatbot Handlers (compartido)    │
         │  - MenuHandler                       │
         │  - StateHandler                      │
         │  - ResponseManager                   │
         └──────────────────┬──────────────────┘
                            │
         ┌──────────────────▼──────────────────┐
         │      Chatbot Core (compartido)       │
         │  - ChatbotStateManager               │
         │  - ChatMemoryManager                  │
         │  - Managers (servicios, procesos, etc)│
         └──────────────────┬──────────────────┘
                            │
         ┌──────────────────▼──────────────────┐
         │         Bases de Datos              │
         │  - Redis (estado activo)            │
         │  - PostgreSQL (persistencia)        │
         │  - Oracle (datos electorales)       │
         └─────────────────────────────────────┘
```

### 1.2 Puntos de Acoplamiento Actuales

#### ✅ **Bien Diseñado (Reutilizable):**
1. **Lógica de Negocio Centralizada:**
   - `MenuHandler`, `StateHandler` → Independientes del canal
   - `ChatMemoryManager` → Funciona con cualquier canal
   - Managers de servicios → No dependen del canal

2. **ResponseManager con Soporte Multi-plataforma:**
   ```python
   # chatbot/utils/chatbot_handlers.py
   async def send_response(chat_id, text: str, state: dict, 
                          menu_actual: str = "main", 
                          platform: str = "telegram"):
   ```
   - Ya tiene parámetro `platform` para diferenciar canales

#### ⚠️ **Problemas Identificados:**

1. **Duplicación de Código en Rutas:**
   - `telegram.py` y `whatsapp.py` tienen ~90% de código duplicado
   - Solo cambian: normalización de input y envío de respuesta

2. **Estado en Memoria (`user_states`):**
   - Compartido entre Telegram y WhatsApp
   - Puede causar conflictos si mismo usuario usa múltiples canales
   - No escalable (problema ya identificado en análisis anterior)

3. **Normalización de Input Duplicada:**
   - `normalizar_input_telegram()` en `telegram.py`
   - `normalizar_input_whatsapp()` en `whatsapp.py`
   - Necesitaremos `normalizar_input_web()` para la nueva interfaz

4. **Envío de Respuestas Específico por Canal:**
   - Telegram: `enviar_mensaje_telegram()`
   - WhatsApp: `enviar_mensaje_whatsapp()`
   - Web: Necesitaremos `enviar_mensaje_web()` o WebSocket

---

## 2. IMPACTO DE AGREGAR INTERFAZ WEB

### 2.1 Cambios Mínimos Necesarios

**Buenas Noticias:** ✅ La estructura actual está **bien preparada** para agregar un nuevo canal.

**Razones:**
1. La lógica de negocio está separada de las rutas
2. `ResponseManager` ya soporta múltiples plataformas
3. `ChatMemoryManager` es agnóstico al canal`

### 2.2 Cambios Específicos Necesarios

#### 🔴 **CRÍTICO - Debe Hacerse Primero:**

1. **Crear Servicio Centralizado de Chatbot**
   - Extraer lógica común de `telegram.py` y `whatsapp.py`
   - Crear `ChatbotService` que maneje cualquier canal
   - Las rutas solo normalizan input y envían respuesta

#### 🟡 **IMPORTANTE - Hacer en Paralelo:**

2. **Crear Normalizador de Input para Web**
   - `normalizar_input_web()` similar a Telegram/WhatsApp

3. **Crear Sistema de Respuesta para Web**
   - Opción A: REST API (polling)
   - Opción B: WebSocket (tiempo real) ← **Recomendado**

4. **Actualizar ResponseManager**
   - Agregar caso `platform="web"` en `send_response()`

#### 🟢 **MEJORAS - Opcional pero Recomendado:**

5. **Refactorizar Rutas Existentes**
   - Usar el nuevo `ChatbotService` en Telegram/WhatsApp
   - Eliminar duplicación de código

6. **Manejo de Sesiones Web**
   - Identificar usuarios web (session_id, user_id, etc.)
   - Compatible con sistema de estado actual

---

## 3. REFACTORIZACIONES NECESARIAS

### 3.1 Refactorización 1: Servicio Centralizado de Chatbot (CRÍTICA)

**Objetivo:** Extraer lógica común a un servicio reutilizable

**Estructura Propuesta:**

```python
# chatbot/services/chatbot_service.py
class ChatbotService:
    """Servicio centralizado que maneja la lógica del chatbot"""
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        platform: str = "web",
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Procesa un mensaje del usuario y retorna la respuesta
        
        Returns:
            {
                "response": str,
                "state": dict,
                "menu_actual": str,
                "should_finalize": bool
            }
        """
```

**Beneficios:**
- ✅ Una sola implementación de la lógica
- ✅ Fácil agregar nuevos canales
- ✅ Testing más simple
- ✅ Menos bugs por duplicación

### 3.2 Refactorización 2: Abstracción de Plataformas (IMPORTANTE)

**Objetivo:** Crear interfaz común para envío de mensajes

**Estructura Propuesta:**

```python
# chatbot/platforms/base.py
class PlatformAdapter(ABC):
    """Interfaz base para adaptadores de plataforma"""
    
    @abstractmethod
    async def send_message(self, user_id: str, message: str) -> bool:
        """Envía mensaje al usuario"""
        pass
    
    @abstractmethod
    def normalize_input(self, raw_input: dict) -> dict:
        """Normaliza input de la plataforma"""
        pass

# chatbot/platforms/telegram_adapter.py
class TelegramAdapter(PlatformAdapter):
    ...

# chatbot/platforms/whatsapp_adapter.py
class WhatsAppAdapter(PlatformAdapter):
    ...

# chatbot/platforms/web_adapter.py
class WebAdapter(PlatformAdapter):
    ...
```

**Beneficios:**
- ✅ Código más limpio y mantenible
- ✅ Fácil agregar nuevas plataformas
- ✅ Testing aislado por plataforma

### 3.3 Refactorización 3: Sistema de Respuesta Web (IMPORTANTE)

**Opciones:**

#### Opción A: REST API (Simple)
```python
# Frontend hace polling cada X segundos
GET /api/web/chat/messages?user_id=xxx&last_message_id=yyy
```

**Pros:**
- ✅ Simple de implementar
- ✅ Funciona con cualquier frontend
- ✅ No requiere WebSocket

**Contras:**
- ❌ Latencia (polling)
- ❌ Mayor carga en servidor
- ❌ No tiempo real

#### Opción B: WebSocket (Recomendado)
```python
# Conexión WebSocket persistente
WS /api/web/chat/ws?user_id=xxx
```

**Pros:**
- ✅ Tiempo real
- ✅ Menor latencia
- ✅ Menor carga (sin polling)

**Contras:**
- ⚠️ Más complejo
- ⚠️ Requiere manejo de reconexión

**Recomendación:** WebSocket para mejor UX

---

## 4. PLAN DE IMPLEMENTACIÓN PRIORIZADO

### Fase 1: Preparación (Sin Romper Nada) - 1-2 días

#### ✅ Paso 1.1: Crear ChatbotService
- Crear `chatbot/services/chatbot_service.py`
- Extraer lógica común de `telegram.py` y `whatsapp.py`
- **NO modificar rutas existentes todavía**

#### ✅ Paso 1.2: Crear Normalizador Web
- Crear `normalizar_input_web()` en `message_utils.py`
- Similar a Telegram/WhatsApp pero para formato web

#### ✅ Paso 1.3: Crear WebAdapter
- Crear `chatbot/platforms/web_adapter.py`
- Implementar `PlatformAdapter` para web
- Soporte para WebSocket o REST según decisión

**Resultado:** Código nuevo listo, sin cambios a código existente

---

### Fase 2: Implementar Interfaz Web (Sin Tocar Telegram/WhatsApp) - 2-3 días

#### ✅ Paso 2.1: Crear Rutas Web
- Crear `chatbot/routes/web_chat.py`
- Usar `ChatbotService` y `WebAdapter`
- Endpoints:
  - `POST /api/web/chat/message` (REST)
  - `WS /api/web/chat/ws` (WebSocket)

#### ✅ Paso 2.2: Actualizar ResponseManager
- Agregar caso `platform="web"` en `send_response()`
- Integrar con `WebAdapter`

#### ✅ Paso 2.3: Frontend Básico (Opcional)
- HTML/JS simple para probar
- O integrar con frontend existente

**Resultado:** Interfaz web funcionando independientemente

---

### Fase 3: Refactorizar Rutas Existentes (Opcional pero Recomendado) - 1-2 días

#### ✅ Paso 3.1: Refactorizar Telegram
- Modificar `telegram.py` para usar `ChatbotService`
- Eliminar código duplicado
- **Probar que sigue funcionando igual**

#### ✅ Paso 3.2: Refactorizar WhatsApp
- Modificar `whatsapp.py` para usar `ChatbotService`
- Eliminar código duplicado
- **Probar que sigue funcionando igual**

**Resultado:** Código más limpio, menos duplicación

---

## 5. CÓDIGO DE EJEMPLO

### 5.1 ChatbotService (Nuevo)

```python
# chatbot/services/chatbot_service.py
from typing import Optional, Dict, Any
from chatbot.utils.chatbot_core import (
    ChatbotStateManager, get_chat_memory, menus
)
from chatbot.utils.chatbot_handlers import (
    ResponseManager, MenuHandler, StateHandler
)

class ChatbotService:
    """Servicio centralizado para procesar mensajes del chatbot"""
    
    def __init__(self):
        self.chat_memory = get_chat_memory()
        self.state_manager = ChatbotStateManager()
        self.response_manager = ResponseManager()
        self.menu_handler = MenuHandler()
        self.state_handler = StateHandler()
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        platform: str = "web",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario
        
        Args:
            user_id: ID único del usuario
            message: Mensaje del usuario
            platform: Plataforma (telegram, whatsapp, web)
            metadata: Metadatos adicionales (opcional)
        
        Returns:
            {
                "response": str,
                "state": dict,
                "menu_actual": str,
                "should_finalize": bool,
                "conversation_active": bool
            }
        """
        # Normalizar user_id a string
        user_id_str = str(user_id)
        
        # Obtener conversación activa
        conversacion_activa = self.chat_memory.obtener_conversacion_activa(user_id_str)
        
        # Inicializar si no hay conversación activa
        if not conversacion_activa:
            self.chat_memory.iniciar_conversacion(
                user_id_str,
                mensaje_inicial="Inicio de conversación",
                numero_telefono=metadata.get("numero_telefono") if metadata else None,
                usuario=metadata.get("usuario") if metadata else None
            )
            conversacion_activa = self.chat_memory.obtener_conversacion_activa(user_id_str)
        
        # Obtener o inicializar estado
        state = self.state_manager.get_user_state(user_id_str)
        if not state:
            state = self.state_manager.initialize_user(user_id_str)
        
        # Registrar mensaje del usuario
        self.response_manager.log_user_message(
            user_id_str,
            message,
            "navegacion_menu" if state["stage"] in menus else "consulta_informacion"
        )
        
        # Procesar comandos especiales
        if message.lower().strip() in ["menu"]:
            state["stage"] = "main"
            respuesta = self._get_menu_message() + "\n\n" + menus["main"]["text"]
            await self.response_manager.send_response(
                user_id_str, respuesta, state, "main", platform=platform
            )
            return {
                "response": respuesta,
                "state": state,
                "menu_actual": "main",
                "should_finalize": False,
                "conversation_active": True
            }
        
        elif message.lower().strip() in ["salir", "cancelar", "exit", "quit", 
                                         "cancel", "volver", "adios", "adiós"]:
            self.chat_memory.finalizar_conversacion(
                user_id_str,
                motivo="Usuario finalizó conversación con comando de salida"
            )
            self.state_manager.reset_user(user_id_str)
            respuesta = self._get_farewell_message()
            return {
                "response": respuesta,
                "state": {"stage": "main", "flow": []},
                "menu_actual": "despedida",
                "should_finalize": True,
                "conversation_active": False
            }
        
        # Procesar según estado actual
        if state["stage"] in menus and state["stage"] not in ["servicios_ciudadano", "pleno"]:
            # Manejar selección de menú
            respuesta, is_final = self.menu_handler.handle_menu_selection(
                user_id_str, message, state
            )
            menu_actual = state.get("final_choice", state["stage"]) if is_final else state["stage"]
            await self.response_manager.send_response(
                user_id_str, respuesta, state, menu_actual, platform=platform
            )
            return {
                "response": respuesta,
                "state": state,
                "menu_actual": menu_actual,
                "should_finalize": is_final,
                "conversation_active": True
            }
        else:
            # Manejar estado específico
            respuesta = await self.state_handler.handle_state(user_id_str, message, state)
            menu_actual = state.get("final_choice", "consulta_general")
            await self.response_manager.send_response(
                user_id_str, respuesta, state, menu_actual, platform=platform
            )
            
            # Verificar si se debe finalizar
            should_finalize = "adiós" in respuesta.lower() or "despedida" in menu_actual
            
            return {
                "response": respuesta,
                "state": state,
                "menu_actual": menu_actual,
                "should_finalize": should_finalize,
                "conversation_active": not should_finalize
            }
    
    def _get_menu_message(self) -> str:
        """Retorna mensaje de regreso al menú"""
        return """🔄 **¡Perfecto! Volvamos al menú principal**

🤖 **ELECCIA** está aquí para ayudarte. ¿En qué más puedo asistirte?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""
    
    def _get_farewell_message(self) -> str:
        """Retorna mensaje de despedida"""
        return """🤖 **¡Ha sido un placer ayudarte!**

👋 **ELECCIA** se despide de ti

💡 Recuerda que siempre puedes volver cuando tengas más consultas sobre el JNE.

¡Que tengas un excelente día! 👋"""
    
    def get_welcome_message(self) -> str:
        """Retorna mensaje de bienvenida"""
        return """🤖 **¡Hola! Soy ELECCIA, tu asistente virtual del JNE**

👋 **Bienvenido/a al Jurado Nacional de Elecciones**

¿En qué puedo ayudarte hoy?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""


# Instancia global
_chatbot_service = None

def get_chatbot_service() -> ChatbotService:
    """Obtiene instancia singleton del servicio"""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service
```

### 5.2 WebAdapter (Nuevo)

```python
# chatbot/platforms/web_adapter.py
from typing import Dict, Any
from chatbot.platforms.base import PlatformAdapter

class WebAdapter(PlatformAdapter):
    """Adaptador para interfaz web"""
    
    def __init__(self):
        # Aquí podrías tener un diccionario de conexiones WebSocket activas
        self.active_connections: Dict[str, Any] = {}
    
    async def send_message(self, user_id: str, message: str) -> bool:
        """
        Envía mensaje al usuario web
        
        Opción 1: WebSocket (tiempo real)
        Opción 2: Almacenar en cola para polling
        """
        # Implementación WebSocket
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json({
                "type": "message",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            return True
        return False
    
    def normalize_input(self, raw_input: dict) -> dict:
        """
        Normaliza input de la interfaz web
        
        Esperado:
        {
            "user_id": "string",
            "message": "string",
            "session_id": "string" (opcional)
        }
        """
        return {
            "chat_id": raw_input.get("user_id", raw_input.get("session_id", "unknown")),
            "text": raw_input.get("message", "").strip(),
            "metadata": {
                "session_id": raw_input.get("session_id"),
                "user_agent": raw_input.get("user_agent"),
                "ip_address": raw_input.get("ip_address")
            }
        }
    
    def register_connection(self, user_id: str, websocket):
        """Registra una conexión WebSocket"""
        self.active_connections[user_id] = websocket
    
    def unregister_connection(self, user_id: str):
        """Elimina una conexión WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
```

### 5.3 Rutas Web (Nuevo)

```python
# chatbot/routes/web_chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from chatbot.services.chatbot_service import get_chatbot_service
from chatbot.platforms.web_adapter import WebAdapter
from chatbot.utils.message_utils import normalizar_input_web

router = APIRouter()
web_adapter = WebAdapter()

# Opción 1: REST API (Simple)
@router.post("/message")
async def send_message_rest(req: Request):
    """Endpoint REST para enviar mensaje"""
    body = await req.json()
    
    # Normalizar input
    datos = normalizar_input_web(body)
    user_id = datos["chat_id"]
    message = datos["text"]
    
    # Procesar mensaje
    chatbot_service = get_chatbot_service()
    result = await chatbot_service.process_message(
        user_id=user_id,
        message=message,
        platform="web",
        metadata=datos.get("metadata")
    )
    
    return {
        "response": result["response"],
        "state": result["state"],
        "conversation_active": result["conversation_active"]
    }

# Opción 2: WebSocket (Tiempo real - Recomendado)
@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """Endpoint WebSocket para chat en tiempo real"""
    await websocket.accept()
    
    # Obtener user_id de query params o primer mensaje
    user_id = None
    
    try:
        # Primer mensaje debe contener user_id
        initial_data = await websocket.receive_json()
        user_id = initial_data.get("user_id") or initial_data.get("session_id")
        
        if not user_id:
            await websocket.close(code=1008, reason="user_id required")
            return
        
        # Registrar conexión
        web_adapter.register_connection(user_id, websocket)
        
        # Enviar mensaje de bienvenida si es nueva conversación
        chatbot_service = get_chatbot_service()
        conversacion_activa = chatbot_service.chat_memory.obtener_conversacion_activa(str(user_id))
        
        if not conversacion_activa:
            welcome = chatbot_service.get_welcome_message() + "\n\n" + menus["main"]["text"]
            await websocket.send_json({
                "type": "message",
                "content": welcome,
                "timestamp": datetime.now().isoformat()
            })
        
        # Procesar mensajes
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            
            if not message:
                continue
            
            # Procesar mensaje
            result = await chatbot_service.process_message(
                user_id=user_id,
                message=message,
                platform="web"
            )
            
            # Enviar respuesta
            await websocket.send_json({
                "type": "message",
                "content": result["response"],
                "state": result["state"],
                "conversation_active": result["conversation_active"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Si se finaliza, cerrar conexión
            if result["should_finalize"]:
                await websocket.close(code=1000, reason="Conversation ended")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if user_id:
            web_adapter.unregister_connection(user_id)

# Endpoint para obtener historial (opcional)
@router.get("/history/{user_id}")
async def get_conversation_history(user_id: str):
    """Obtiene historial de conversación"""
    chatbot_service = get_chatbot_service()
    conversacion = chatbot_service.chat_memory.obtener_conversacion_activa(user_id)
    
    if conversacion:
        return {
            "conversation": conversacion,
            "active": True
        }
    else:
        # Buscar en PostgreSQL si está finalizada
        # (implementar según necesidad)
        return {
            "conversation": None,
            "active": False
        }
```

### 5.4 Actualizar ResponseManager

```python
# chatbot/utils/chatbot_handlers.py
# Modificar send_response para soportar web

@staticmethod
async def send_response(chat_id, text: str, state: dict, 
                       menu_actual: str = "main", 
                       platform: str = "telegram"):
    """Envía respuesta y la registra en la conversación"""
    
    # Enviar según plataforma
    if platform == "telegram":
        from chatbot.utils.message_utils import enviar_mensaje_telegram
        await enviar_mensaje_telegram({"chat_id": chat_id, "text": text})
    elif platform == "whatsapp":
        from chatbot.utils.message_utils import enviar_mensaje_whatsapp
        await enviar_mensaje_whatsapp({"chat_id": str(chat_id), "text": text})
    elif platform == "web":
        # Para web, el envío se maneja en el WebSocket o REST response
        # No necesitamos hacer nada aquí, ya se envió en la ruta
        pass
    
    # Registrar en conversación (siempre)
    chat_memory = get_chat_memory()
    chat_memory.agregar_respuesta_bot(
        user_id=str(chat_id),
        respuesta=text,
        menu_actual=menu_actual,
        estado_actual=state.copy()
    )
```

### 5.5 Actualizar main.py

```python
# chatbot/main.py
from chatbot.routes import telegram, api_gateway, whatsapp, web_chat

# ... código existente ...

# Routers
app.include_router(telegram.router, prefix="/webhook/telegram", tags=["Telegram"])
app.include_router(whatsapp.router, prefix="/webhook/whatsapp", tags=["WhatsApp"])
app.include_router(api_gateway.router, prefix="/api", tags=["API Gateway"])
app.include_router(web_chat.router, prefix="/api/web/chat", tags=["Web Chat"])  # NUEVO
```

---

## RESUMEN DE PRIORIDADES

### 🔴 **CRÍTICO - Hacer Primero (Sin Romper Nada):**
1. ✅ Crear `ChatbotService` (extraer lógica común)
2. ✅ Crear `normalizar_input_web()`
3. ✅ Crear `WebAdapter`

### 🟡 **IMPORTANTE - Hacer Después:**
4. ✅ Crear rutas web (`web_chat.py`)
5. ✅ Actualizar `ResponseManager` para web
6. ✅ Integrar en `main.py`

### 🟢 **OPCIONAL - Mejoras Futuras:**
7. ⚪ Refactorizar `telegram.py` para usar `ChatbotService`
8. ⚪ Refactorizar `whatsapp.py` para usar `ChatbotService`
9. ⚪ Agregar tests para nueva funcionalidad

---

## VENTAJAS DE ESTE ENFOQUE

1. ✅ **No Rompe Nada:** Telegram y WhatsApp siguen funcionando igual
2. ✅ **Código Reutilizable:** Lógica centralizada en `ChatbotService`
3. ✅ **Fácil Mantenimiento:** Un solo lugar para lógica de negocio
4. ✅ **Escalable:** Fácil agregar más canales en el futuro
5. ✅ **Testing:** Más fácil testear lógica centralizada

---

## RIESGOS Y MITIGACIONES

### Riesgo 1: Estado Compartido entre Canales
**Problema:** Mismo usuario en Telegram y Web podría tener conflictos

**Mitigación:**
- Usar `user_id` único por canal: `telegram_123`, `web_123`
- O usar namespace en Redis: `chatbot:conversacion:web:123`

### Riesgo 2: WebSocket Connections
**Problema:** Muchas conexiones WebSocket pueden agotar recursos

**Mitigación:**
- Implementar límite de conexiones
- Timeout automático de conexiones inactivas
- Usar Redis para compartir conexiones entre workers (si escalas)

### Riesgo 3: Testing
**Problema:** Cambios pueden romper funcionalidad existente

**Mitigación:**
- Probar Telegram y WhatsApp después de cada cambio
- Mantener rutas existentes sin modificar hasta que web funcione
- Tests automatizados (ideal)

---

**Documento creado:** Enero 2025  
**Próximos pasos:** Implementar Fase 1 (ChatbotService)
