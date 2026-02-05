# Pasos Después de Cambios - Guía Rápida

## ✅ Estado Actual

Según los logs, **las conexiones ya están funcionando correctamente**:
- ✅ PostgreSQL: `postgres:5432/ELECCIA_CHATBOT`
- ✅ Redis: `redis:6379`
- ✅ Tablas creadas automáticamente

## 🔄 Pasos Siguientes

### Opción 1: Reinicio Simple (Recomendado)

Si solo cambiaste código Python (no Dockerfile ni dependencias):

```bash
# Reiniciar el contenedor (carga cambios automáticamente con --reload)
docker compose restart app

# Ver logs para verificar
docker logs -f chatbot_app
```

**Ventaja:** Rápido, uvicorn detecta cambios automáticamente con `--reload`

---

### Opción 2: Reconstrucción Completa (Si cambiaste Dockerfile o dependencias)

Si cambiaste el Dockerfile, pyproject.toml, o agregaste nuevas dependencias:

```bash
# 1. Detener contenedores
docker compose down

# 2. Reconstruir imagen
docker compose build app

# 3. Levantar todo
docker compose up -d

# 4. Ver logs
docker logs -f chatbot_app
```

**Cuándo usar:** Solo si cambiaste Dockerfile, dependencias, o estructura de archivos

---

## 🧪 Probar que Todo Funciona

### 1. Verificar Conexiones en Logs

Deberías ver:
```
✅ Conexión a PostgreSQL establecida correctamente en postgres:5432/ELECCIA_CHATBOT
✅ Conexión a Redis establecida correctamente en redis:6379
✅ Las tablas ya existen en PostgreSQL
```

### 2. Health Check
```bash
curl http://localhost:8001/health
```

**Respuesta esperada:**
```json
{"status": "ok"}
```

### 3. Probar REST API
```powershell
# En PowerShell
Invoke-RestMethod -Uri "http://localhost:8001/api/web/chat/message" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"user_id": "test123", "message": "Hola"}'
```

### 4. Probar WebSocket

Abre tu navegador en `http://localhost:8001` y ejecuta en la consola:

```javascript
const ws = new WebSocket('ws://localhost:8001/api/web/chat/ws?user_id=test123');
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    console.log('Bot:', data.content);
};
ws.onopen = () => {
    console.log('✅ Conectado!');
    ws.send(JSON.stringify({type: 'message', message: 'Hola'}));
};
```

---

## 📋 Checklist de Verificación

- [ ] Contenedor está corriendo: `docker ps | grep chatbot_app`
- [ ] Variables de entorno correctas: `docker exec chatbot_app printenv | findstr "DB_HOST REDIS_HOST"`
  - Debe mostrar: `DB_HOST=postgres` y `REDIS_HOST=redis`
- [ ] Logs muestran conexiones exitosas
- [ ] Health check responde: `curl http://localhost:8001/health`
- [ ] Endpoints web funcionan

---

## 🚨 Si Algo No Funciona

### Verificar Variables de Entorno
```bash
docker exec chatbot_app printenv | findstr "DB_HOST REDIS_HOST"
```

### Ver Logs Completos
```bash
docker logs chatbot_app --tail 100
```

### Reiniciar Todo
```bash
docker compose down
docker compose up -d
docker logs -f chatbot_app
```

---

## ✅ Resumen

**Para tu caso actual:** Solo necesitas **reiniciar** el contenedor:

```bash
docker compose restart app
docker logs -f chatbot_app
```

Los cambios en código Python se cargarán automáticamente gracias a `--reload` en uvicorn.

**No necesitas rebuild** a menos que hayas cambiado:
- Dockerfile
- pyproject.toml (dependencias)
- Estructura de archivos que se copian al contenedor
