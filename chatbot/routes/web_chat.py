from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import logging

from chatbot.services.chatbot_service import get_chatbot_service
from chatbot.platforms.web_adapter import WebAdapter
from chatbot.utils.message_utils import normalizar_input_web
from chatbot.utils.chatbot_core import menus
from chatbot.utils.response_builder import ResponseBuilder

logger = logging.getLogger(__name__)

# Zona horaria de Perú (America/Lima, UTC-5)
PERU_TIMEZONE = timezone(timedelta(hours=-5))

def get_current_timestamp() -> str:
    """
    Obtiene el timestamp actual en la zona horaria de Perú (America/Lima, UTC-5)
    Retorna formato ISO8601 con información de zona horaria
    """
    now = datetime.now(PERU_TIMEZONE)
    return now.isoformat()

router = APIRouter()

# Instancia global del adaptador web
web_adapter = WebAdapter()

# Opción 1: REST API (Simple - para compatibilidad)
@router.post("/message")
async def send_message_rest(req: Request):
    """
    Endpoint REST para enviar mensaje (alternativa a WebSocket)
    
    Body esperado:
    {
        "user_id": "string" o "session_id": "string",
        "message": "string",
        "metadata": dict (opcional)
    }
    """
    try:
        body = await req.json()
        
        # Normalizar input
        datos = normalizar_input_web(body)
        user_id = datos["chat_id"]
        message = datos["text"]
        
        if not message:
            return JSONResponse(
                status_code=400,
                content={"error": "El mensaje no puede estar vacío"}
            )
        
        # Procesar mensaje
        chatbot_service = get_chatbot_service()
        result = await chatbot_service.process_message(
            user_id=user_id,
            message=message,
            platform="web",
            metadata=datos.get("metadata")
        )
        
        response_data = {
            "response": result["response"],
            "state": result["state"],
            "menu_actual": result["menu_actual"],
            "conversation_active": result["conversation_active"],
            "should_finalize": result["should_finalize"],            
            "timestamp": get_current_timestamp()
        }
        # Agregar response_rich si existe
        if "response_rich" in result:
            response_data["response_rich"] = result["response_rich"]
        
        return response_data
    
    except Exception as e:
        logger.error(f"Error en send_message_rest: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor", "message": str(e)}
        )

# Opción 2: WebSocket (Tiempo real - Recomendado)
@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    Endpoint WebSocket para chat en tiempo real
    
    Conexión:
    WS /api/web/chat/ws?user_id=xxx
    
    O enviar en primer mensaje:
    {
        "type": "init",
        "user_id": "string" o "session_id": "string"
    }
    
    Mensajes del cliente:
    {
        "type": "message",
        "message": "string"
    }
    
    Respuestas del servidor:
    {
        "type": "message" | "error" | "system",
        "content": "string",
        "state": dict,
        "conversation_active": bool,
        "timestamp": "ISO8601"
    }
    """
    await websocket.accept()
    
    user_id = None
    chatbot_service = get_chatbot_service()
    
    try:
        # Intentar obtener user_id de query params
        query_params = dict(websocket.query_params)
        user_id = query_params.get("user_id") or query_params.get("session_id")
        
        # Si no está en query params, esperar mensaje inicial
        if not user_id:
            initial_data = await websocket.receive_json()
            
            if initial_data.get("type") == "init":
                user_id = initial_data.get("user_id") or initial_data.get("session_id")
            else:
                # Si no es init, usar el mensaje como primer mensaje
                # Generar user_id temporal
                user_id = f"web_{uuid.uuid4().hex[:8]}"
                message = initial_data.get("message", "").strip()
                
                if message:
                    # Procesar primer mensaje
                    result = await chatbot_service.process_message(
                        user_id=user_id,
                        message=message,
                        platform="web"
                    )
                    
                    # Construir respuesta completa
                    response_data = {
                        "type": "message",
                        "content": result["response"],
                        "state": result["state"],
                        "conversation_active": result["conversation_active"],
                        "should_finalize": result["should_finalize"],
                        "timestamp": get_current_timestamp()
                    }
                    # Agregar menu_actual si existe
                    if "menu_actual" in result:
                        response_data["menu_actual"] = result["menu_actual"]
                    # Agregar response_rich si existe
                    if "response_rich" in result:
                        response_data["response_rich"] = result["response_rich"]
                    
                    await websocket.send_json(response_data)
                    
                    if result["should_finalize"]:
                        await websocket.close(code=1000, reason="Conversation ended")
                        return
        
        if not user_id:
            await websocket.send_json({
                "type": "error",
                "content": "user_id o session_id requerido",
                "timestamp": get_current_timestamp()
            })
            await websocket.close(code=1008, reason="user_id required")
            return
        
        # Normalizar user_id a string
        user_id = str(user_id)
        
        # Registrar conexión
        web_adapter.register_connection(user_id, websocket)
        
        # Verificar si hay conversación activa
        conversacion_activa = chatbot_service.chat_memory.obtener_conversacion_activa(user_id)
        
        # Enviar mensaje de bienvenida si es nueva conversación
        if not conversacion_activa:
            welcome = chatbot_service.get_welcome_message() + "\n\n" + menus["main"]["text"]
            welcome_response = {
                "type": "message",
                "content": welcome,
                "state": {"stage": "main", "flow": []},
                "conversation_active": True,
                "should_finalize": False,
                "timestamp": get_current_timestamp()
            }
            # Agregar response_rich para bienvenida
            welcome_rich = ResponseBuilder.build_response(
                welcome, {"stage": "main", "flow": []}, "main", False
            )
            if welcome_rich:
                welcome_response["response_rich"] = welcome_rich
            
            await websocket.send_json(welcome_response)
        else:
            # Enviar mensaje de reconexión
            await websocket.send_json({
                "type": "system",
                "content": "Conexión restablecida. Puedes continuar tu conversación.",
                "state": conversacion_activa.get("estado_actual", {}),
                "conversation_active": True,
                "timestamp": get_current_timestamp()
            })
        
        # Procesar mensajes en bucle
        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type", "message")
                
                if message_type == "ping":
                    # Responder a ping para mantener conexión viva
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": get_current_timestamp()
                    })
                    continue
                
                if message_type == "message":
                    message = data.get("message", "").strip()
                    
                    if not message:
                        await websocket.send_json({
                            "type": "error",
                            "content": "El mensaje no puede estar vacío",
                            "timestamp": get_current_timestamp()
                        })
                        continue
                    
                    # Procesar mensaje
                    result = await chatbot_service.process_message(
                        user_id=user_id,
                        message=message,
                        platform="web"
                    )
                    
                    # Enviar respuesta
                    response_data = {
                        "type": "message",
                        "content": result["response"],
                        "state": result["state"],
                        "menu_actual": result["menu_actual"],
                        "conversation_active": result["conversation_active"],
                        "should_finalize": result["should_finalize"],
                        "timestamp": get_current_timestamp()
                    }
                    # Agregar response_rich si existe
                    if "response_rich" in result:
                        response_data["response_rich"] = result["response_rich"]
                    
                    await websocket.send_json(response_data)
                    
                    # Si se finaliza, cerrar conexión
                    if result["should_finalize"]:
                        await websocket.close(code=1000, reason="Conversation ended")
                        break
                
                elif message_type == "close":
                    # Cliente solicita cerrar conexión
                    await websocket.close(code=1000, reason="Client requested close")
                    break
                
            except WebSocketDisconnect:
                # Cliente desconectado normalmente
                break
            except Exception as e:
                logger.error(f"Error procesando mensaje WebSocket: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "content": "Error al procesar el mensaje. Por favor, intenta de nuevo.",
                    "timestamp": get_current_timestamp()
                })
                
    except WebSocketDisconnect:
        # Cliente desconectado
        logger.info(f"Cliente WebSocket desconectado: {user_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "content": "Error interno del servidor",
                "timestamp": get_current_timestamp()
            })
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        # Limpiar conexión
        if user_id:
            web_adapter.unregister_connection(user_id)
            logger.info(f"Conexión WebSocket limpiada para usuario {user_id}")

# Endpoint para obtener historial de conversación (opcional)
@router.get("/history/{user_id}")
async def get_conversation_history(user_id: str):
    """
    Obtiene historial de conversación activa
    
    Returns:
        {
            "conversation": dict,
            "active": bool
        }
    """
    try:
        chatbot_service = get_chatbot_service()
        conversacion = chatbot_service.chat_memory.obtener_conversacion_activa(user_id)
        
        if conversacion:
            return {
                "conversation": conversacion,
                "active": True,
                "timestamp": get_current_timestamp()
            }
        else:
            return {
                "conversation": None,
                "active": False,
                "message": "No hay conversación activa para este usuario",
                "timestamp": get_current_timestamp()
            }
    
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial: {str(e)}"
        )

# Endpoint para obtener estado de conexión
@router.get("/status/{user_id}")
async def get_connection_status(user_id: str):
    """
    Obtiene estado de conexión WebSocket para un usuario
    
    Returns:
        {
            "connected": bool,
            "active_connections": int
        }
    """
    return {
        "connected": web_adapter.is_connected(user_id),
        "active_connections": web_adapter.get_active_connections_count(),
        "timestamp": get_current_timestamp()
    }

# Endpoint para iniciar nueva conversación
@router.post("/start")
async def start_conversation(req: Request):
    """
    Inicia una nueva conversación para un usuario
    
    Body esperado:
    {
        "user_id": "string" o "session_id": "string",
        "metadata": dict (opcional)
    }
    """
    try:
        # Intentar obtener body, pero manejar caso de body vacío
        try:
            body = await req.json()
        except Exception:
            # Si no hay body, usar query params o generar user_id
            body = {}
        
        user_id = body.get("user_id") or body.get("session_id")
        
        # Si no hay user_id en body, intentar obtener de query params
        if not user_id:
            query_params = dict(req.query_params)
            user_id = query_params.get("user_id") or query_params.get("session_id")
        
        # Si aún no hay user_id, generar uno temporal
        if not user_id:
            import uuid
            user_id = f"web_{uuid.uuid4().hex[:8]}"
        
        user_id = str(user_id)
        chatbot_service = get_chatbot_service()
        
        # Iniciar conversación
        chatbot_service.chat_memory.iniciar_conversacion(
            user_id,
            mensaje_inicial="Inicio de conversación",
            metadata=body.get("metadata")
        )
        
        # Obtener mensaje de bienvenida
        welcome = chatbot_service.get_welcome_message() + "\n\n" + menus["main"]["text"]
        
        return {
            "user_id": user_id,
            "welcome_message": welcome,
            "conversation_started": True,
            "timestamp": get_current_timestamp()
        }
    
    except Exception as e:
        logger.error(f"Error iniciando conversación: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Error al iniciar conversación", "message": str(e)}
        )
