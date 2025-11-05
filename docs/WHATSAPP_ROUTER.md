# Documentación del Router de WhatsApp (`whatsapp.py`)

Este documento detalla la funcionalidad del módulo `whatsapp.py`, que sirve como el punto de entrada (webhook) para todas las interacciones del chatbot a través de la plataforma WhatsApp.

## Descripción General

El router de WhatsApp, construido con FastAPI, es responsable de dos tareas principales:
1.  **Verificación del Webhook**: Responde al desafío de verificación inicial de la API de WhatsApp para confirmar que el endpoint es válido.
2.  **Recepción de Mensajes**: Procesa los mensajes entrantes de los usuarios, orquesta la lógica del chatbot y envía las respuestas correspondientes.

---

## Endpoints

### `GET /`

-   **Propósito**: Verificación del Webhook.
-   **Funcionamiento**:
    -   Cuando se configura el webhook en la plataforma de Meta for Developers, WhatsApp envía una solicitud `GET` a este endpoint.
    -   La solicitud contiene los parámetros `hub.mode`, `hub.challenge` y `hub.verify_token`.
    -   El endpoint verifica que `hub.mode` sea `subscribe` y que `hub.verify_token` coincida con el token de acceso configurado en las variables de entorno (`WHATSAPP_ACCESS_TOKEN`).
    -   Si la verificación es exitosa, responde con el valor de `hub.challenge` y un código de estado `200`, completando el proceso de suscripción del webhook.
    -   Si falla, responde con un `403 Forbidden`.

### `POST /`

-   **Propósito**: Recepción y procesamiento de mensajes.
-   **Funcionamiento**: Este es el endpoint principal que maneja toda la lógica de la conversación en tiempo real.

---

## Flujo de Procesamiento de Mensajes (`POST /`)

El flujo de trabajo para cada mensaje recibido es el siguiente:

1.  **Recepción y Normalización**:
    -   El endpoint recibe una carga útil (payload) en formato JSON desde la API de WhatsApp.
    -   Llama a `normalizar_input_whatsapp` (de `message_utils.py`) para extraer de manera segura el `chat_id` del remitente y el `text` del mensaje.
    -   Si no se puede extraer un `chat_id` o un `text` válido, el proceso se detiene para evitar errores.

2.  **Gestión de la Conversación**:
    -   Se obtiene una instancia del `ChatMemoryManager` para interactuar con la memoria de la conversación en Redis.
    -   Se verifica si existe una conversación activa para el `chat_id`.

3.  **Inicio de Nueva Conversación**:
    -   Si no hay una conversación activa en Redis o no hay un estado en memoria para el usuario, se inicia una nueva sesión:
        -   Se llama a `ChatbotStateManager.initialize_user()` para crear un estado inicial en memoria.
        -   Se llama a `chat_memory.iniciar_conversacion()` para crear el registro de la conversación en Redis.
        -   Se envía un mensaje de bienvenida (`mensaje_bienvenida`) junto con el menú principal.

4.  **Procesamiento de Mensaje Existente**:
    -   Si ya existe una conversación, se recupera el estado actual del usuario con `ChatbotStateManager.get_user_state()`.
    -   El mensaje del usuario se registra en la memoria de la conversación usando `ResponseManager.log_user_message()`.

5.  **Manejo de Comandos Globales**:
    -   Se verifica si el texto del usuario coincide con comandos globales como `menu` (para volver al inicio) o `adios`, `salir`, etc. (para finalizar la conversación).
    -   Si es un comando de finalización, se llama a `chat_memory.finalizar_conversacion()` y se limpia el estado del usuario con `ChatbotStateManager.reset_user()`.

6.  **Enrutamiento Lógico**:
    -   **Si el usuario está en un menú estático**: La entrada se delega a `MenuHandler.handle_menu_selection()`, que determina la siguiente acción o submenú.
    -   **Si el usuario está en un estado de espera (`awaiting_*`)**: La entrada se delega a `StateHandler.handle_state()`, que procesa la información específica que el bot estaba esperando (ej. una consulta de búsqueda, la selección de una opción dinámica, etc.).

7.  **Envío de Respuesta**:
    -   La respuesta generada por el `MenuHandler` o `StateHandler` se envía al usuario.
    -   Se utiliza `ResponseManager.send_response()`, especificando `platform="whatsapp"` para asegurar que se use la función `enviar_mensaje_whatsapp`.

8.  **Manejo de Errores**:
    -   Todo el proceso está envuelto en un bloque `try...except` para capturar cualquier excepción inesperada, registrarla en la consola y evitar que el servidor se caiga.

---

## Dependencias Clave

-   `chatbot.utils.message_utils`: Para la función `normalizar_input_whatsapp`.
-   `chatbot.utils.chatbot_core`: Para acceder al `ChatbotStateManager`, los menús, el estado de los usuarios (`user_states`) y los gestores de servicios (`get_chat_memory`).
-   `chatbot.utils.chatbot_handlers`: Para utilizar `ResponseManager`, `MenuHandler` y `StateHandler`, que contienen la lógica central del flujo conversacional.
