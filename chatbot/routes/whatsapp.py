from fastapi import APIRouter, Request, Response
import os
from datetime import datetime

from chatbot.utils.message_utils import normalizar_input_whatsapp
from chatbot.utils.chatbot_core import ChatbotStateManager, get_chat_memory, menus, user_states
from chatbot.utils.chatbot_handlers import ResponseManager, MenuHandler, StateHandler

router = APIRouter()

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

@router.get("")
async def verify_webhook(request: Request):
    """
    Verificación del webhook (GET)
    """
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge")
    token = params.get("hub.verify_token")

    if mode == "subscribe" and token == WHATSAPP_ACCESS_TOKEN:
        print("WEBHOOK VERIFIED")
        return Response(content=challenge, status_code=200)
    else:
        return Response(status_code=403)

@router.post("")
async def receive_webhook(request: Request):
    """
    Endpoint principal del chatbot WhatsApp
    """
    try:
        body = await request.json()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n\nWhatsApp Webhook received {timestamp}\n")
        print(body)
        
        # Normalizar datos de WhatsApp
        datos = normalizar_input_whatsapp(body)
        
        chat_id = datos["chat_id"]
        text = datos["text"]
        
        # Si no hay chat_id o text válidos, retornar OK sin procesar
        if not chat_id or not text:
            return {"reply": "Mensaje no válido o vacío"}
        
        # Obtener instancia de ChatMemoryManager
        chat_memory = get_chat_memory()
        
        # Verificar si el usuario tiene una conversación activa
        conversacion_activa = chat_memory.obtener_conversacion_activa(str(chat_id))
        
        # Si no hay conversación activa o no existe estado del usuario, iniciar una nueva
        if not conversacion_activa or str(chat_id) not in user_states:
            state = ChatbotStateManager.initialize_user(chat_id)
            
            if not conversacion_activa:
                chat_memory.iniciar_conversacion(str(chat_id))
            
            # Mensaje de bienvenida amigable para ELECCIA
            mensaje_bienvenida = """🤖 **¡Hola! Soy ELECCIA, tu asistente virtual del JNE**

👋 **Bienvenido/a al Jurado Nacional de Elecciones**

¿En qué puedo ayudarte hoy?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""
            
            respuesta = mensaje_bienvenida + "\n\n" + menus["main"]["text"]
            await ResponseManager.send_response(chat_id, respuesta, state, "main", platform="whatsapp")
            return {"reply": respuesta}
        
        # Obtener el estado actual del usuario
        state = ChatbotStateManager.get_user_state(chat_id)
        
        if not state:
            state = ChatbotStateManager.initialize_user(chat_id)
        
        # Agregar mensaje del usuario a la conversación
        ResponseManager.log_user_message(
            chat_id, 
            text, 
            "navegacion_menu" if state["stage"] in menus else "consulta_informacion"
        )
        
        # Verificar comandos especiales
        if text.lower().strip() in ["menu"]:
            # Solo regresar al menú principal (sin reiniciar estado)
            mensaje_regreso = """🔄 **¡Perfecto! Volvamos al menú principal**

🤖 **ELECCIA** está aquí para ayudarte. ¿En qué más puedo asistirte?

💡 **Comandos útiles:**
• Escribe **'menu'** para volver al menú principal en cualquier momento
• Escribe **'adios'** para cerrar la conversación y finalizar"""
            
            respuesta = mensaje_regreso + "\n\n" + menus["main"]["text"]
            state["stage"] = "main"
            await ResponseManager.send_response(chat_id, respuesta, state, "main", platform="whatsapp")
            return {"reply": respuesta}
        
        elif text.lower().strip() in ["salir", "cancelar", "exit", "quit", "cancel", "volver", "adios", "adiós"]:
            # Finalizar conversación (comportamiento como "adios")
            chat_memory = get_chat_memory()
            chat_memory.finalizar_conversacion(
                user_id=str(chat_id),
                motivo="Usuario finalizó conversación con comando de salida"
            )
            ChatbotStateManager.reset_user(chat_id)
            
            mensaje_despedida = """🤖 **¡Ha sido un placer ayudarte!**

👋 **ELECCIA** se despide de ti

💡 Recuerda que siempre puedes volver cuando tengas más consultas sobre el JNE.

¡Que tengas un excelente día! 👋"""
            
            await ResponseManager.send_response(chat_id, mensaje_despedida, {"stage": "main", "flow": []}, "despedida", platform="whatsapp")
            return {"reply": mensaje_despedida}

        # Si el usuario está en un menú (excluyendo servicios_ciudadano y pleno que se manejan dinámicamente)
        if state["stage"] in menus and state["stage"] not in ["servicios_ciudadano", "pleno"]:
            respuesta, is_final = MenuHandler.handle_menu_selection(chat_id, text, state)
            
            if is_final:
                await ResponseManager.send_response(chat_id, respuesta, state, state.get("final_choice", "consulta_general"), platform="whatsapp")
            else:
                await ResponseManager.send_response(chat_id, respuesta, state, state["stage"], platform="whatsapp")
            
            return {"reply": respuesta}
        
        # Si el usuario está en un estado específico (incluyendo servicios_ciudadano)
        respuesta = await StateHandler.handle_state(chat_id, text, state)
        await ResponseManager.send_response(chat_id, respuesta, state, state.get("final_choice", "consulta_general"), platform="whatsapp")
        
        return {"reply": respuesta}
        
    except Exception as e:
        print(f"Error procesando webhook de WhatsApp: {e}")
        return {"reply": f"Error interno del servidor: {str(e)}"}