# Chatbot JNE Simplificado

## Requisitos
- Python 3.10+
- uv (gestor de dependencias)
- Redis
- Base de datos (SQLite por defecto)

## Instalación
```bash
uv venv
uv pip install -r requirements.txt
```

## Variables de entorno
Copiar `.env.template` a `.env` y configurar las variables necesarias.

## Ejecución
```bash
source .venv/bin/activate
uvicorn chatbot.main:app  --host 0.0.0.0 --port 8000 --reload
```

## Estructura
- `routes/`: endpoints de Telegram y API Gateway
- `services/`: lógica de validación, enriquecimiento, ejecución LangGraph y logging en DB
- `config.py`: carga de configuración
