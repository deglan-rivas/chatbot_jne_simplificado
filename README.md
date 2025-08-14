# Chatbot JNE Simplificado

## Requisitos
- Python 3.10+
- uv (gestor de dependencias)
- Redis
- Base de datos (PostgreSQL)
- Docker
- LLM (OpenAI o Google Gemini)
- Telegram

## Instalación y configuración
1. **Levantar los contenedores**

   ```bash
   docker compose up -d
   ```

2. **Crear el entorno virtual con `uv`**

   ```bash
   uv venv
   uv sync
   ```

3. **Activar el entorno virtual**

   * **Linux / macOS**

     ```bash
     source .venv/bin/activate
     ```
   * **Windows (PowerShell)**

     ```powershell
     .venv\Scripts\activate
     ```

4. **Inicializar la base de datos**
   Esto creará la tabla `conversaciones` en PostgreSQL:

   ```bash
   python chatbot/database/init_db.py
   ```

5. **Desactivar el entorno virtual**

   ```bash
   deactivate
   ```

## Variables de entorno
Copiar `.env.template` a `.env` y configurar las variables necesarias.

* **Bot de Telegram**:
  Crea un bot siguiendo las instrucciones de [**BotFather**](https://telegram.me/botfather).

* **API Key para el LLM**:
  Genera una clave para el proveedor de LLM. En este proyecto se usa **Gemini** por su mejor tiempo de respuesta.

## Ejecución
```bash
source .venv/bin/activate
uvicorn chatbot.main:app  --host 0.0.0.0 --port 8000 --reload
# validar que los logs muestren una conexión exitosa a las bases de datos
```

## Estructura
- `routes/`: endpoints de Telegram y API Gateway
- `services/`: lógica de validación, enriquecimiento, ejecución LangGraph y logging en DB
- `config.py`: carga de configuración
