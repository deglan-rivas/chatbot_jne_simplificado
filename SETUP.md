# Instalacion y configuracion

## 1. Configurar variables de entorno

Copiar `.env.template` a `.env` y llenar las variables necesarias:

```bash
cp .env.template .env
```

Configurar como minimo:
- **`TELEGRAM_BOT_TOKEN`**: Crear un bot siguiendo las instrucciones de [BotFather](https://telegram.me/botfather).
- **`GEMINI_API_KEY`**: Generar una clave en [Google AI Studio](https://aistudio.google.com/api-keys).

## 2. Crear y activar el entorno virtual

```bash
uv venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate     # Windows (PowerShell)
uv sync
```

> Esto genera el archivo `uv.lock` necesario para construir la imagen Docker.

## 3. Levantar los contenedores

```bash
docker compose up -d
```

## 4. Inicializar la base de datos

Esto creara la tabla `conversaciones` en PostgreSQL:

```bash
python chatbot/database/init_db.py
```

## 5. Exponer el backend con Cloudflared (opcional, necesario para Telegram)

```bash
cloudflared tunnel --url http://localhost:8001
```

Esto devuelve un dominio con HTTPS, por ejemplo: `https://burner-toner-aging-declare.trycloudflare.com`

## 6. Configurar el webhook de Telegram

Setear el webhook (reemplazar `<TOKEN>` y `<DOMINIO_CLOUDFLARE>`):

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<DOMINIO_CLOUDFLARE>/webhook/telegram"
```

Verificar que se configuro correctamente:

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

## 7. Validar el funcionamiento

- Acceder al [Swagger del backend](http://localhost:8001/docs)
- Probar con cURL / Postman:

  ```bash
  curl --location 'http://localhost:8001/webhook/telegram' \
    --header 'Content-Type: application/json' \
    --data '{"chat_id": 12345, "text": "1"}'
  ```

- Interactuar directamente con el bot en Telegram (si se configuro el webhook)

## 8. Apagar todo

```bash
docker compose down
deactivate
```

## Ejecucion local (sin Docker)

Tambien se puede ejecutar localmente sin contenedores:

```bash
source .venv/bin/activate
uvicorn chatbot.main:app --host 0.0.0.0 --port 8001 --reload
# validar que los logs muestren una conexion exitosa a las bases de datos
```
