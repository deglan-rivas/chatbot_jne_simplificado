# DATABASE STRUCTURE DOCUMENTATION

## Chatbot JNE Simplificado - Database Architecture

**Proyecto:** Chatbot del Jurado Nacional de Elecciones (JNE)  
**Versión:** 1.0  
**Fecha:** Octubre 2025  
**Autores:** deglan-rivas, odt013 (Rhonal Erick Sinche Martinez)

---

## OVERVIEW

El sistema del chatbot utiliza una arquitectura híbrida de bases de datos para optimizar el rendimiento y la gestión de conversaciones:

- **Redis**: Almacenamiento temporal de conversaciones activas y cache de sesiones
- **PostgreSQL**: Persistencia de conversaciones finalizadas y datos históricos
- **Oracle**: Fuente de datos electorales (conexión externa al sistema SIJE)

---

## REDIS DATABASE

### Descripción General
Redis se utiliza como sistema de cache temporal para mantener las conversaciones activas del chatbot. Las conversaciones se almacenan en formato JSON con expiración automática.

### Configuración
- **Puerto:** 6379 (configuración estándar)
- **Expiración por defecto:** 1800 segundos (30 minutos)
- **Encoding:** UTF-8 con `ensure_ascii=False`

### Estructura de Claves

#### Patrón de Claves
```
chatbot:conversacion:<user_id>
```

**Ejemplos:**
- `chatbot:conversacion:123456789`
- `chatbot:conversacion:987654321`

#### Comandos Redis Útiles
```bash
# Obtener conversación específica
GET chatbot:conversacion:123456789

# Listar todas las conversaciones activas
KEYS chatbot:conversacion:*

# Verificar tiempo de expiración
TTL chatbot:conversacion:123456789

# Eliminar conversación específica
DEL chatbot:conversacion:123456789
```

### Estructura de Datos JSON

#### Schema de Conversación
```json
{
  "user_id": "string",              // ID único del usuario (Telegram ID)
  "numero_telefono": "string|null", // Número de teléfono (opcional)
  "usuario": "string|null",         // Username de Telegram (opcional)
  "fecha_inicio": "ISO8601",        // Timestamp de inicio de conversación
  "mensajes": [],                   // Array de mensajes de la conversación
  "estado_actual": {},              // Estado actual del flujo de conversación
  "metadata": {}                    // Metadatos de la conversación
}
```

#### Estructura de Mensaje
```json
{
  "tipo": "bot|usuario",            // Tipo de mensaje
  "contenido": "string",            // Contenido del mensaje
  "timestamp": "ISO8601",           // Timestamp del mensaje
  "intent": "string|null"           // Intención detectada (opcional)
}
```

#### Estado Actual
```json
{
  "stage": "string",                // Etapa actual del flujo
  "flow": ["string"],               // Historial de navegación
  "menu_actual": "string"           // Menú donde se encuentra el usuario
}
```

#### Metadata
```json
{
  "num_mensajes": "integer",        // Contador de mensajes
  "ultima_actividad": "ISO8601",    // Timestamp de última actividad
  "duracion_total": "integer"       // Duración en segundos (solo al finalizar)
}
```

### Ejemplo Completo de Conversación en Redis
```json
{
  "user_id": "123456789",
  "numero_telefono": null,
  "usuario": null,
  "fecha_inicio": "2025-10-17T10:41:19.248141",
  "mensajes": [
    {
      "tipo": "bot",
      "contenido": "Inicio de conversación",
      "timestamp": "2025-10-17T10:41:19.248158",
      "intent": null
    },
    {
      "tipo": "bot",
      "contenido": "🤖 **¡Hola! Soy ELECCIA, tu asistente virtual del JNE**\n\n👋 **Bienvenido/a al Jurado Nacional de Elecciones**\n\n¿En qué puedo ayudarte hoy?\n\n💡 **Comandos útiles:**\n• Escribe **'menu'** para volver al menú principal en cualquier momento\n• Escribe **'adios'** para cerrar la conversación y finalizar\n\nMenú principal:\n1. Procesos Electorales\n2. Organizaciones Políticas\n3. Información Institucional\n4. Servicios Digitales",
      "timestamp": "2025-10-17T10:41:19.960989",
      "intent": null
    }
  ],
  "estado_actual": {
    "stage": "main",
    "flow": [],
    "menu_actual": "main"
  },
  "metadata": {
    "num_mensajes": 2,
    "ultima_actividad": "2025-10-17T10:41:19.960999"
  }
}
```

### Gestión de Expiración
- **Tiempo de vida:** 30 minutos por defecto
- **Renovación automática:** Se renueva con cada interacción del usuario
- **Limpieza automática:** Conversaciones con menos de 5 minutos restantes se finalizan automáticamente
- **Método de limpieza:** Función `verificar_expiracion_conversaciones()` en `ChatMemoryManager`

---

## POSTGRESQL DATABASE

### Descripción General
PostgreSQL almacena las conversaciones finalizadas para análisis histórico y registro de actividad del chatbot.

### Configuración
- **Base de datos:** `chatbot_db` (configuración estándar)
- **Schema:** `public`
- **Puerto:** 5432 (configuración estándar)

### Tabla: conversaciones

#### Esquema de la Tabla
```sql
CREATE TABLE public.conversaciones (
    id                  SERIAL PRIMARY KEY,
    user_id             VARCHAR NOT NULL,
    numero_telefono     VARCHAR NULL,
    usuario             VARCHAR NULL,
    flujo               TEXT NOT NULL,
    fecha_inicio        TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    fecha_fin           TIMESTAMP WITHOUT TIME ZONE NULL,
    canal               VARCHAR NOT NULL,
    error               BOOLEAN NOT NULL DEFAULT FALSE,
    mensaje_error       TEXT NULL,
    duracion_total      INTEGER NULL,
    num_mensajes        INTEGER NULL
);
```

#### Descripción de Columnas

| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| `id` | `SERIAL` | NO | Clave primaria autoincremental |
| `user_id` | `VARCHAR` | NO | ID del usuario (Telegram ID) |
| `numero_telefono` | `VARCHAR` | YES | Número de teléfono del usuario |
| `usuario` | `VARCHAR` | YES | Username de Telegram |
| `flujo` | `TEXT` | NO | JSON completo de la conversación |
| `fecha_inicio` | `TIMESTAMP` | NO | Fecha y hora de inicio |
| `fecha_fin` | `TIMESTAMP` | YES | Fecha y hora de finalización |
| `canal` | `VARCHAR` | NO | Canal de comunicación (telegram, whatsapp) |
| `error` | `BOOLEAN` | NO | Indica si hubo errores |
| `mensaje_error` | `TEXT` | YES | Descripción del error |
| `duracion_total` | `INTEGER` | YES | Duración en segundos |
| `num_mensajes` | `INTEGER` | YES | Total de mensajes intercambiados |

#### Índices Recomendados
```sql
-- Índice para búsquedas por usuario
CREATE INDEX idx_conversaciones_user_id ON conversaciones(user_id);

-- Índice para búsquedas por fecha
CREATE INDEX idx_conversaciones_fecha_inicio ON conversaciones(fecha_inicio);

-- Índice para búsquedas por canal
CREATE INDEX idx_conversaciones_canal ON conversaciones(canal);

-- Índice compuesto para análisis de errores
CREATE INDEX idx_conversaciones_error ON conversaciones(error, fecha_inicio);
```

#### Ejemplo de Registro
```sql
INSERT INTO conversaciones VALUES (
    1,
    '123456789',
    NULL,
    NULL,
    '{"user_id": "123456789", "numero_telefono": null, "usuario": null, "fecha_inicio": "2025-08-13T23:55:16.693083", "mensajes": [{"tipo": "bot", "contenido": "Inicio de conversación", "timestamp": "2025-08-13T23:55:16.693111", "intent": null}], "estado_actual": {"stage": "awaiting_another_question", "flow": ["servicios_digitales", "administrativos"], "menu_actual": "finalizacion", "final_choice": "administrativos"}, "metadata": {"num_mensajes": 33, "ultima_actividad": "2025-08-14T00:41:00.896352", "duracion_total": 2744}, "fecha_fin": "2025-08-14T00:41:00.896748", "motivo_finalizacion": "Usuario confirmó que no tiene más consultas"}',
    '2025-08-13 23:55:16.693083',
    '2025-08-14 00:41:00.896748',
    'telegram',
    false,
    NULL,
    2744,
    33
);
```

### Consultas Útiles

#### Análisis de Conversaciones
```sql
-- Estadísticas generales
SELECT 
    COUNT(*) as total_conversaciones,
    AVG(duracion_total) as duracion_promedio,
    AVG(num_mensajes) as mensajes_promedio,
    COUNT(CASE WHEN error = true THEN 1 END) as conversaciones_con_error
FROM conversaciones;

-- Conversaciones por día
SELECT 
    DATE(fecha_inicio) as fecha,
    COUNT(*) as total_conversaciones,
    AVG(duracion_total) as duracion_promedio
FROM conversaciones 
GROUP BY DATE(fecha_inicio) 
ORDER BY fecha DESC;

-- Usuarios más activos
SELECT 
    user_id,
    COUNT(*) as total_conversaciones,
    SUM(duracion_total) as tiempo_total,
    MAX(fecha_inicio) as ultima_conversacion
FROM conversaciones 
GROUP BY user_id 
ORDER BY total_conversaciones DESC;
```

#### Análisis del Flujo JSON
```sql
-- Extraer información específica del JSON
SELECT 
    id,
    user_id,
    fecha_inicio,
    JSON_EXTRACT(flujo, '$.metadata.num_mensajes') as num_mensajes_json,
    JSON_EXTRACT(flujo, '$.estado_actual.menu_actual') as menu_final,
    JSON_EXTRACT(flujo, '$.motivo_finalizacion') as motivo
FROM conversaciones
WHERE fecha_inicio >= '2025-08-01';
```

---

## DATA FLOW ARCHITECTURE

### Flujo de Datos de Conversación

```
1. Usuario inicia conversación
   ↓
2. Se crea sesión en Redis (chatbot:conversacion:<user_id>)
   ↓
3. Intercambio de mensajes (actualizaciones en Redis)
   ↓
4. Conversación finaliza o expira
   ↓
5. Datos se migran a PostgreSQL
   ↓
6. Sesión se elimina de Redis
```

### Gestión de Estados

#### Estados Principales
- `main`: Menú principal
- `procesos_electorales`: Navegando procesos electorales
- `organizaciones_politicas`: Navegando organizaciones políticas
- `informacion_institucional`: Navegando información institucional
- `servicios_digitales`: Navegando servicios digitales
- `awaiting_question`: Esperando pregunta del usuario
- `awaiting_another_question`: Esperando confirmación de nueva pregunta

#### Tipos de Intent
- `navegacion_menu`: Navegación entre menús
- `consulta_informacion`: Consultas de información específica
- `finalizacion`: Finalización de conversación

---

## BACKUP AND MAINTENANCE

### Backup de Redis
```bash
# Crear snapshot manual
redis-cli BGSAVE

# Configurar backup automático en redis.conf
save 900 1      # Backup si al menos 1 cambio en 900 segundos
save 300 10     # Backup si al menos 10 cambios en 300 segundos
save 60 10000   # Backup si al menos 10000 cambios en 60 segundos
```

### Backup de PostgreSQL
```bash
# Backup completo
pg_dump -U usuario -h localhost chatbot_db > backup_chatbot_$(date +%Y%m%d).sql

# Backup solo de la tabla conversaciones
pg_dump -U usuario -h localhost -t conversaciones chatbot_db > backup_conversaciones_$(date +%Y%m%d).sql

# Restaurar backup
psql -U usuario -h localhost chatbot_db < backup_chatbot_20251017.sql
```

### Limpieza y Mantenimiento
```sql
-- Limpiar conversaciones antiguas (más de 6 meses)
DELETE FROM conversaciones 
WHERE fecha_inicio < NOW() - INTERVAL '6 months';

-- Analizar tabla para optimizar consultas
ANALYZE conversaciones;

-- Reindexar para optimizar rendimiento
REINDEX TABLE conversaciones;
```

---

## MONITORING AND ANALYTICS

### Métricas Clave de Redis
```bash
# Información de memoria
redis-cli INFO memory

# Número de claves activas
redis-cli DBSIZE

# Información de clientes conectados
redis-cli INFO clients

# Estadísticas de comandos
redis-cli INFO commandstats
```

### Métricas Clave de PostgreSQL
```sql
-- Tamaño de la base de datos
SELECT 
    pg_size_pretty(pg_database_size('chatbot_db')) as database_size;

-- Tamaño de la tabla conversaciones
SELECT 
    pg_size_pretty(pg_total_relation_size('conversaciones')) as table_size;

-- Actividad de la tabla
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables 
WHERE tablename = 'conversaciones';
```

---

## PERFORMANCE OPTIMIZATION

### Redis Optimizations
1. **Configuración de memoria**: Ajustar `maxmemory` según recursos disponibles
2. **Política de expiración**: Usar `allkeys-lru` para manejo automático de memoria
3. **Persistencia**: Configurar RDB snapshots según necesidades

### PostgreSQL Optimizations
1. **Particionamiento**: Considerar particionamiento por fecha para tablas grandes
2. **Índices**: Mantener índices actualizados en columnas de búsqueda frecuente
3. **Vacuum**: Configurar autovacuum para mantenimiento automático

---

## SECURITY CONSIDERATIONS

### Redis Security
- Usar autenticación con `requirepass`
- Configurar bind a IPs específicas
- Deshabilitar comandos peligrosos con `rename-command`

### PostgreSQL Security
- Usar conexiones SSL/TLS
- Implementar roles y permisos granulares
- Configurar pg_hba.conf para acceso restringido
- Encriptar datos sensibles en la columna `flujo`

---

## TROUBLESHOOTING

### Problemas Comunes de Redis
```bash
# Redis no responde
redis-cli ping

# Verificar logs
tail -f /var/log/redis/redis-server.log

# Verificar conexiones
redis-cli CLIENT LIST
```

### Problemas Comunes de PostgreSQL
```sql
-- Verificar conexiones activas
SELECT count(*) FROM pg_stat_activity;

-- Identificar queries lentas
SELECT query, query_start, state 
FROM pg_stat_activity 
WHERE state != 'idle';

-- Verificar locks
SELECT * FROM pg_locks;
```

---

**Documento actualizado:** Octubre 17, 2025  
**Próxima revisión:** Enero 2026