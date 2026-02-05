# Solución de Problemas Docker - Chatbot JNE

## Problema: Conexión a localhost en lugar de nombres de servicio

### Síntomas
- Los logs muestran: `connection to server at "localhost" (::1), port 5432 failed`
- Error: `Error -5 connecting to redis_cache:6379. No address associated with hostname`

### Causa
El contenedor está usando valores de `.env` (localhost) en lugar de los nombres de servicio Docker.

### Solución

#### Paso 1: Detener y eliminar contenedores
```bash
docker compose down
```

#### Paso 2: Reconstruir la imagen (si cambiaste código)
```bash
docker compose build app
```

#### Paso 3: Levantar servicios
```bash
docker compose up -d
```

#### Paso 4: Verificar variables de entorno en el contenedor
```bash
# Verificar DB_HOST
docker exec chatbot_app printenv DB_HOST
# Debe mostrar: postgres

# Verificar REDIS_HOST
docker exec chatbot_app printenv REDIS_HOST
# Debe mostrar: redis
```

#### Paso 5: Ver logs
```bash
docker logs -f chatbot_app
```

### Verificación Esperada

Deberías ver en los logs:
```
🔧 Configuración de conexiones cargada:
   Docker detectado: True
   DB_HOST (env): postgres
   DB_HOST (final): postgres
   REDIS_HOST (env): redis
   REDIS_HOST (final): redis
   DB_NAME: ELECCIA_CHATBOT
🔌 Inicializando conexiones - DB_HOST: postgres, REDIS_HOST: redis
✅ Conexión a PostgreSQL establecida correctamente en postgres:5432/ELECCIA_CHATBOT
✅ Conexión a Redis establecida correctamente en redis:6379
✅ Las tablas ya existen en PostgreSQL (o se crean automáticamente)
```

### Si el problema persiste

#### Opción 1: Verificar que docker-compose.yml no tenga env_file activo
Asegúrate de que en `docker-compose.yml` esté comentado:
```yaml
# env_file:
#   - .env
```

#### Opción 2: Verificar variables directamente en el contenedor
```bash
docker exec chatbot_app python -c "import os; print('DB_HOST:', os.getenv('DB_HOST')); print('REDIS_HOST:', os.getenv('REDIS_HOST'))"
```

#### Opción 3: Forzar reinicio completo
```bash
docker compose down -v  # Elimina volúmenes también
docker compose build --no-cache app
docker compose up -d
```

---

## Cómo Probar los Endpoints

### 1. Health Check
```bash
curl http://localhost:8001/health
```

### 2. REST API - Enviar Mensaje
```bash
curl -X POST http://localhost:8001/api/web/chat/message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "message": "Hola"}'
```

### 3. REST API - Obtener Historial
```bash
curl http://localhost:8001/api/web/chat/history/test123
```

### 4. REST API - Estado de Conexión
```bash
curl http://localhost:8001/api/web/chat/status/test123
```

### 5. WebSocket (desde navegador)
Abre la consola del navegador y ejecuta:
```javascript
const ws = new WebSocket('ws://localhost:8001/api/web/chat/ws?user_id=test123');
ws.onmessage = (e) => console.log('Respuesta:', JSON.parse(e.data));
ws.onopen = () => ws.send(JSON.stringify({type: 'message', message: 'Hola'}));
```

---

## Notas Importantes

1. **En Docker**: Los servicios se comunican por nombre de servicio (`postgres`, `redis`)
2. **Localmente**: Usa `localhost` del archivo `.env`
3. **Variables de entorno**: Las de `docker-compose.yml` tienen prioridad sobre `.env`
4. **Reinicio necesario**: Después de cambiar `docker-compose.yml`, siempre reinicia con `docker compose down && docker compose up -d`
