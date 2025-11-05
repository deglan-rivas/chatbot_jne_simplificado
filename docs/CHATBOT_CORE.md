# Documentación de Chatbot Core (`chatbot_core.py`)

Este documento detalla la estructura y funcionalidad del módulo `chatbot_core.py`, que actúa como el núcleo central para la gestión de estado, la inicialización de servicios y la configuración principal del chatbot.

## Descripción General

El módulo `chatbot_core.py` es responsable de:
-   Inicializar y proporcionar acceso a los gestores de servicios (`managers`) mediante un patrón de carga perezosa (lazy loading).
-   Gestionar el estado de la conversación de cada usuario en memoria.
-   Definir la estructura de los menús de navegación.
-   Centralizar la interacción con el modelo de lenguaje (LLM).

---

## Gestores de Servicios (Lazy Loading)

Para optimizar el uso de recursos, los gestores de servicios se inicializan solo cuando se necesitan por primera vez. Esto se logra a través de funciones `get_*`.

### `get_chat_memory() -> ChatMemoryManager`

-   **Propósito**: Obtiene una instancia singleton del `ChatMemoryManager`.
-   **Responsabilidad del Manager**: Gestionar la memoria de las conversaciones, manteniendo las sesiones activas en Redis y persistiendo las conversaciones finalizadas en PostgreSQL.

### `get_servicios_manager() -> ServiciosDigitalesManager`

-   **Propósito**: Obtiene una instancia singleton del `ServiciosDigitalesManager`.
-   **Responsabilidad del Manager**: Gestionar la información sobre los servicios digitales del JNE, cargada desde archivos CSV, y realizar búsquedas semánticas.

### `get_info_institucional_manager() -> InformacionInstitucionalManager`

-   **Propósito**: Obtiene una instancia singleton del `InformacionInstitucionalManager`.
-   **Responsabilidad del Manager**: Gestionar la información institucional estática, como los miembros del Pleno, funcionarios y sedes.

### `get_procesos_electorales_manager() -> ProcesosElectoralesManager`

-   **Propósito**: Obtiene una instancia singleton del `ProcesosElectoralesManager`.
-   **Responsabilidad del Manager**: Interactuar con la base de datos Oracle para obtener información dinámica sobre procesos electorales, hitos y candidatos.

---

## Definición de Menús

La variable global `menus` define la estructura de navegación del chatbot.

### Estructura

Cada entrada en el diccionario `menus` representa una pantalla o un submenú y sigue esta estructura:

```python
"nombre_menu": {
    "text": "Texto a mostrar al usuario.",
    "options": {
        "1": "clave_opcion_1",
        "2": "clave_opcion_2"
    }
}
```

-   `text`: El mensaje que se envía al usuario cuando llega a este menú.
-   `options`: Un diccionario que mapea la entrada del usuario (ej. "1") a una clave de acción o submenú.

### Menús Principales

-   `main`: Menú de bienvenida.
-   `procesos_electorales`: Opciones sobre cronogramas y políticos.
-   `organizaciones_politicas`: Opciones sobre tipos de organizaciones y afiliación.
-   `informacion_institucional`: Opciones sobre el Pleno, funcionarios, etc.
-   `servicios_digitales`: Opciones sobre servicios y trámites.
-   `servicios_ciudadano` y `pleno`: Menús dinámicos cuyo contenido se genera en tiempo de ejecución.

---

## `ChatbotStateManager`

Esta clase es responsable de gestionar el estado de la conversación de cada usuario. Utiliza un diccionario en memoria (`user_states`) para rastrear la etapa (`stage`) y el flujo (`flow`) de cada `chat_id`.

### Métodos Estáticos

#### `initialize_user(chat_id) -> dict`

Crea una nueva entrada en `user_states` para un nuevo usuario, inicializando su estado en el menú principal (`stage: "main"`). El `chat_id` se convierte a `str` para mantener la consistencia de las claves.

#### `reset_user(chat_id)`

Elimina el estado de un usuario del diccionario `user_states`, típicamente al finalizar una conversación.

#### `get_user_state(chat_id) -> Optional[dict]`

Recupera el estado actual de un usuario a partir de su `chat_id`.

#### `update_user_state(chat_id, **kwargs)`

Actualiza el estado de un usuario existente con nuevos valores (ej. cambiando el `stage`).

---

## Interacción con el LLM

### `context_map`

Es un diccionario que mapea claves de opciones de menú a cadenas de texto con contexto específico. Este contexto se añade al prompt enviado al LLM para enriquecer la consulta y obtener respuestas más precisas.

**Ejemplo**:
```python
"cronograma_electoral": "Las elecciones internas se realizarán el 15 de septiembre y la campaña oficial inicia el 1 de octubre."
```

### `send_to_llm(user_input: str, extra_context: str) -> str`

-   **Propósito**: Centraliza las llamadas al modelo de lenguaje (Gemini).
-   **Funcionamiento**:
    1.  Construye un `prompt` combinando el `extra_context` del `context_map` con la pregunta del usuario (`user_input`).
    2.  Llama al modelo `gemma-3-27b-it` a través del cliente de `genai`.
    3.  Retorna la respuesta de texto generada por el LLM.
    4.  Incluye un manejo de excepciones básico para capturar errores durante la llamada a la API.
