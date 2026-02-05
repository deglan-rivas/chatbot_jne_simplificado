# Análisis de Arquitectura y Propuesta de Mejoras
## Chatbot JNE Simplificado

**Fecha:** Enero 2025  
**Versión del Análisis:** 1.0

---

## 📋 ÍNDICE

1. [Análisis de Conexiones a Bases de Datos](#1-análisis-de-conexiones-a-bases-de-datos)
2. [Análisis del Servicio de Datos del Chat](#2-análisis-del-servicio-de-datos-del-chat)
3. [Análisis de Escalabilidad](#3-análisis-de-escalabilidad)
4. [Problemas Identificados](#4-problemas-identificados)
5. [Mejoras Propuestas](#5-mejoras-propuestas)
6. [Plan de Implementación](#6-plan-de-implementación)

---

## 1. ANÁLISIS DE CONEXIONES A BASES DE DATOS

### 1.1 PostgreSQL

**Estado Actual:**
- ✅ Pool de conexiones configurado con SQLAlchemy
- ✅ Configuración: `pool_size=10`, `max_overflow=20`
- ✅ `pool_pre_ping=True` para verificar conexiones
- ✅ `pool_recycle=3600` para reciclar conexiones cada hora
- ⚠️ **Problema:** Conexión global única (`engine_postgresql`) compartida entre todas las requests

**Código Relevante:**
```python
# chatbot/database/connection.py
engine_postgresql: Optional[object] = None
SessionLocal: Optional[object] = None

def inicializar_conexiones():
    global engine_postgresql, SessionLocal
    engine_postgresql = crear_engine_postgresql()
    SessionLocal = sessionmaker(...)
```

**Análisis:**
- El pool funciona correctamente para un solo proceso
- En despliegues multi-worker, cada worker tendrá su propio pool (correcto)
- **Limitación:** No hay gestión de conexiones por contexto de request

### 1.2 Redis

**Estado Actual:**
- ✅ Cliente Redis configurado con timeouts
- ✅ `decode_responses=True` para manejo automático de strings
- ⚠️ **Problema:** Cliente global único sin pooling
- ⚠️ **Problema:** No hay manejo de reconexión automática robusto

**Código Relevante:**
```python
# chatbot/database/connection.py
cliente_redis: Optional[object] = None

def crear_cliente_redis():
    cliente_redis = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
```

**Análisis:**
- Redis es thread-safe, pero un cliente único puede ser cuello de botella
- No hay pooling de conexiones Redis
- Falta manejo de fallos de conexión

### 1.3 Oracle Database

**Estado Actual:**
- ✅ Pool configurado: `pool_size=5`, `max_overflow=10`
- ✅ `pool_recycle=1800` (30 minutos)
- ⚠️ **Problema:** Motor global único (`motor`) compartido
- ⚠️ **Problema:** Uso de `get_db()` como generador puede causar problemas de contexto

**Código Relevante:**
```python
# chatbot/database/oracle_connection.py
motor = create_engine(...)
SessionLocal = sessionmaker(...)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Análisis:**
- El patrón de generador es correcto para FastAPI dependencies
- **Problema crítico:** En `oracle_repository.py` se usa `for session in get_db():` que no es el patrón correcto para FastAPI

---

## 2. ANÁLISIS DEL SERVICIO DE DATOS DEL CHAT

### 2.1 Flujo de Datos Actual

```
Usuario → Telegram Webhook → FastAPI Route
    ↓
ChatbotStateManager (memoria) → user_states[chat_id]
    ↓
ChatMemoryManager → Redis (conversación activa)
    ↓
Procesamiento → Oracle/PostgreSQL (consultas)
    ↓
Respuesta → Telegram API
    ↓
Finalización → PostgreSQL (persistencia)
```

### 2.2 Gestión de Estado

**Estado en Memoria (`user_states`):**
```python
# chatbot/routes/telegram.py
user_states: Dict[int, dict] = {}
```

**Problemas Identificados:**
1. ❌ **No escalable:** Estado en memoria no se comparte entre workers
2. ❌ **Pérdida de estado:** Si el proceso se reinicia, se pierde todo el estado
3. ❌ **Sin sincronización:** Múltiples workers no comparten estado
4. ⚠️ **Race conditions:** Posibles condiciones de carrera en actualizaciones concurrentes

**Estado en Redis:**
```python
# chatbot/services/chat_memory_manager.py
clave = f"chatbot:conversacion:{user_id}"
```

**Análisis:**
- ✅ Redis es adecuado para estado compartido
- ⚠️ **Problema:** Hay duplicación: estado en memoria Y en Redis
- ⚠️ **Problema:** No hay sincronización entre ambos

### 2.3 Persistencia de Conversaciones

**Flujo:**
1. Conversación activa en Redis (30 min TTL)
2. Al finalizar → PostgreSQL
3. Eliminación de Redis

**Análisis:**
- ✅ Estrategia correcta (cache caliente + persistencia fría)
- ⚠️ **Problema:** Si falla la migración a PostgreSQL, se pierde la conversación
- ⚠️ **Problema:** No hay retry logic para fallos de persistencia

---

## 3. ANÁLISIS DE ESCALABILIDAD

### 3.1 Escalabilidad Horizontal

**Estado Actual:**
- ❌ **NO ESCALABLE HORIZONTALMENTE**
- El estado `user_states` en memoria impide escalado horizontal
- Cada worker tiene su propio estado aislado

**Escenario Problemático:**
```
Worker 1: Usuario A en estado "awaiting_politico_nombres"
Worker 2: Usuario A envía mensaje → No encuentra estado → Error
```

### 3.2 Escalabilidad Vertical

**Estado Actual:**
- ⚠️ **Limitada**
- Pool de PostgreSQL: 10 conexiones base + 20 overflow = 30 máximo
- Pool de Oracle: 5 conexiones base + 10 overflow = 15 máximo
- Redis: Sin pooling (1 conexión por worker)

**Análisis:**
- Para carga moderada: Suficiente
- Para alta carga: Puede ser insuficiente
- **Problema:** No hay métricas ni monitoreo de uso de pools

### 3.3 Puntos de Cuello de Botella

1. **Estado en Memoria:**
   - Bloquea escalado horizontal
   - Pérdida de estado en reinicios

2. **Conexiones a Oracle:**
   - Pool pequeño (5 conexiones base)
   - Consultas pueden ser lentas
   - Sin circuit breaker

3. **LLM (Gemini):**
   - Llamadas síncronas sin timeout adecuado
   - Sin retry logic
   - Sin rate limiting

4. **Redis:**
   - Cliente único sin pooling
   - Posible cuello de botella en alta concurrencia

---

## 4. PROBLEMAS IDENTIFICADOS

### 4.1 Problemas Críticos

#### 🔴 P1: Estado en Memoria No Escalable
**Ubicación:** `chatbot/routes/telegram.py:26`
```python
user_states: Dict[int, dict] = {}
```

**Impacto:**
- Imposible escalar horizontalmente
- Pérdida de estado en reinicios
- Race conditions en actualizaciones concurrentes

**Solución Propuesta:** Migrar todo el estado a Redis

#### 🔴 P2: Duplicación de Estado
**Ubicación:** `chatbot/routes/telegram.py` y `chatbot/services/chat_memory_manager.py`

**Impacto:**
- Inconsistencias entre memoria y Redis
- Complejidad innecesaria
- Posibles bugs por desincronización

**Solución Propuesta:** Unificar estado en Redis únicamente

#### 🔴 P3: Uso Incorrecto de `get_db()` en Oracle
**Ubicación:** `chatbot/database/oracle_repository.py`

**Código Problemático:**
```python
for session in get_db():
    result = session.query(...)
```

**Impacto:**
- No funciona correctamente con FastAPI dependencies
- Puede causar leaks de conexiones
- No sigue el patrón de FastAPI

**Solución Propuesta:** Usar dependency injection de FastAPI

### 4.2 Problemas Importantes

#### 🟡 P4: Falta de Manejo de Errores Robusto
- No hay circuit breakers para Oracle
- No hay retry logic para LLM
- No hay fallback cuando Redis falla

#### 🟡 P5: Sin Cache de Consultas Frecuentes
- Consultas a Oracle se repiten sin cache
- Menús se regeneran en cada request
- Sin cache de resultados de LLM

#### 🟡 P6: Sin Rate Limiting
- No hay protección contra abuso
- Sin límites por usuario
- Sin throttling global

#### 🟡 P7: Sin Monitoreo y Métricas
- No hay métricas de performance
- No hay alertas de errores
- No hay tracking de uso de recursos

### 4.3 Problemas Menores

#### 🟢 P8: Configuración Hardcodeada
- Valores mágicos en código
- Falta de configuración por ambiente

#### 🟢 P9: Sin Logging Estructurado
- Logs inconsistentes
- Sin correlación de requests
- Dificulta debugging

#### 🟢 P10: Sin Tests
- No hay tests unitarios
- No hay tests de integración
- No hay tests de carga

---

## 5. MEJORAS PROPUESTAS

### 5.1 Mejora 1: Migración de Estado a Redis (CRÍTICA)

**Objetivo:** Hacer el sistema escalable horizontalmente

**Cambios Propuestos:**

1. **Eliminar `user_states` en memoria:**
```python
# ANTES (chatbot/routes/telegram.py)
user_states: Dict[int, dict] = {}

# DESPUÉS
# Eliminar completamente, usar solo Redis
```

2. **Crear `StateManager` basado en Redis:**
```python
# chatbot/services/state_manager.py
class RedisStateManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.expiration = 1800  # 30 minutos
    
    def get_user_state(self, user_id: str) -> Optional[dict]:
        key = f"chatbot:state:{user_id}"
        state_json = self.redis.get(key)
        if state_json:
            return json.loads(state_json)
        return None
    
    def set_user_state(self, user_id: str, state: dict):
        key = f"chatbot:state:{user_id}"
        self.redis.setex(
            key,
            self.expiration,
            json.dumps(state, ensure_ascii=False)
        )
    
    def delete_user_state(self, user_id: str):
        key = f"chatbot:state:{user_id}"
        self.redis.delete(key)
```

3. **Integrar en `ChatMemoryManager`:**
```python
# Unificar estado y conversación en una sola estructura Redis
```

**Beneficios:**
- ✅ Escalabilidad horizontal
- ✅ Persistencia de estado
- ✅ Sin race conditions
- ✅ Estado compartido entre workers

**Esfuerzo:** Alto (requiere refactorización significativa)  
**Prioridad:** CRÍTICA

---

### 5.2 Mejora 2: Pool de Conexiones Redis

**Objetivo:** Mejorar rendimiento y manejo de conexiones Redis

**Cambios Propuestos:**

```python
# chatbot/database/connection.py
from redis.connection import ConnectionPool

def crear_pool_redis():
    """Crea un pool de conexiones Redis"""
    return ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        max_connections=50,  # Máximo de conexiones en el pool
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )

def crear_cliente_redis():
    """Crea cliente Redis desde pool"""
    pool = crear_pool_redis()
    return redis.Redis(connection_pool=pool)
```

**Beneficios:**
- ✅ Mejor rendimiento en alta concurrencia
- ✅ Reutilización de conexiones
- ✅ Mejor manejo de errores

**Esfuerzo:** Bajo  
**Prioridad:** ALTA

---

### 5.3 Mejora 3: Dependency Injection para Oracle

**Objetivo:** Corregir el uso incorrecto de `get_db()` y seguir patrones de FastAPI

**Cambios Propuestos:**

```python
# chatbot/database/oracle_connection.py
from fastapi import Depends
from sqlalchemy.orm import Session

def get_oracle_db() -> Session:
    """Dependency para obtener sesión de Oracle"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# chatbot/database/oracle_repository.py
class OracleRepository:
    def __init__(self, db: Session = Depends(get_oracle_db)):
        self.db = db
    
    def obtener_procesos_electorales(self) -> list:
        result = self.db.query(
            CronogramaElectoral.PROCESO_ELECTORAL
        ).distinct().all()
        return [row.PROCESO_ELECTORAL for row in result]
```

**Beneficios:**
- ✅ Patrón correcto de FastAPI
- ✅ Gestión automática de sesiones
- ✅ Sin leaks de conexiones

**Esfuerzo:** Medio  
**Prioridad:** ALTA

---

### 5.4 Mejora 4: Circuit Breaker para Oracle

**Objetivo:** Prevenir cascading failures cuando Oracle está caído

**Cambios Propuestos:**

```python
# chatbot/utils/circuit_breaker.py
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_oracle_with_circuit_breaker(func, *args, **kwargs):
    """Wrapper con circuit breaker para llamadas a Oracle"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Oracle error: {e}")
        raise

# Uso en OracleRepository
class OracleRepository:
    def obtener_procesos_electorales(self) -> list:
        return call_oracle_with_circuit_breaker(
            self._obtener_procesos_electorales_internal
        )
    
    def _obtener_procesos_electorales_internal(self) -> list:
        # Lógica original
        ...
```

**Beneficios:**
- ✅ Prevención de cascading failures
- ✅ Respuestas rápidas cuando Oracle está caído
- ✅ Recuperación automática

**Esfuerzo:** Medio  
**Prioridad:** MEDIA

---

### 5.5 Mejora 5: Cache de Consultas Frecuentes

**Objetivo:** Reducir carga en Oracle y mejorar tiempos de respuesta

**Cambios Propuestos:**

```python
# chatbot/services/cache_manager.py
from functools import wraps
import hashlib
import json

class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hora
    
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Genera clave de cache"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"cache:{prefix}:{key_hash}"
    
    def cached(self, ttl: int = None):
        """Decorator para cachear resultados"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = self.cache_key(func.__name__, *args, **kwargs)
                cached_result = self.redis.get(cache_key)
                
                if cached_result:
                    return json.loads(cached_result)
                
                result = func(*args, **kwargs)
                self.redis.setex(
                    cache_key,
                    ttl or self.default_ttl,
                    json.dumps(result, ensure_ascii=False, default=str)
                )
                return result
            return wrapper
        return decorator

# Uso
cache_manager = CacheManager(redis_client)

class OracleRepository:
    @cache_manager.cached(ttl=1800)  # 30 minutos
    def obtener_procesos_electorales(self) -> list:
        # Lógica original
        ...
```

**Beneficios:**
- ✅ Reducción de carga en Oracle
- ✅ Mejora de tiempos de respuesta
- ✅ Menor costo de operación

**Esfuerzo:** Medio  
**Prioridad:** MEDIA

---

### 5.6 Mejora 6: Rate Limiting

**Objetivo:** Proteger el sistema contra abuso

**Cambios Propuestos:**

```python
# chatbot/middleware/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
)

# En main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# En routes
@router.post("")
@limiter.limit("10/minute")  # 10 requests por minuto por IP
async def tilin_chatbot(req: Request):
    ...
```

**Beneficios:**
- ✅ Protección contra abuso
- ✅ Control de costos (LLM)
- ✅ Mejor experiencia para usuarios legítimos

**Esfuerzo:** Bajo  
**Prioridad:** MEDIA

---

### 5.7 Mejora 7: Logging Estructurado

**Objetivo:** Mejorar observabilidad y debugging

**Cambios Propuestos:**

```python
# chatbot/utils/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    rootLogger = logging.getLogger()
    rootLogger.addHandler(logHandler)
    rootLogger.setLevel(logging.INFO)

# Uso con contexto
import structlog

logger = structlog.get_logger()

@router.post("")
async def tilin_chatbot(req: Request):
    request_id = str(uuid.uuid4())
    logger.info(
        "request_received",
        request_id=request_id,
        chat_id=chat_id,
        text_length=len(text)
    )
    # ... procesamiento
    logger.info(
        "request_completed",
        request_id=request_id,
        duration_ms=duration
    )
```

**Beneficios:**
- ✅ Mejor debugging
- ✅ Correlación de logs
- ✅ Análisis de performance

**Esfuerzo:** Bajo  
**Prioridad:** BAJA

---

### 5.8 Mejora 8: Async para LLM

**Objetivo:** Mejorar rendimiento de llamadas a LLM

**Cambios Propuestos:**

```python
# chatbot/services/llm_service.py
import asyncio
from google import genai

class AsyncLLMService:
    def __init__(self):
        self.client = genai.Client()
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def generate_content_async(
        self, 
        model: str, 
        contents: str,
        timeout: int = 30
    ) -> str:
        """Llamada asíncrona a LLM con timeout"""
        loop = asyncio.get_event_loop()
        try:
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    lambda: self.client.models.generate_content(
                        model=model,
                        contents=contents
                    )
                ),
                timeout=timeout
            )
            return response.text
        except asyncio.TimeoutError:
            logger.error("LLM timeout")
            return "Lo siento, la consulta está tardando demasiado. Por favor, intenta de nuevo."
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "Error al procesar la consulta. Por favor, intenta más tarde."
```

**Beneficios:**
- ✅ No bloquea el event loop
- ✅ Mejor throughput
- ✅ Timeout controlado

**Esfuerzo:** Medio  
**Prioridad:** MEDIA

---

### 5.9 Mejora 9: Retry Logic con Exponential Backoff

**Objetivo:** Manejar fallos temporales de servicios externos

**Cambios Propuestos:**

```python
# chatbot/utils/retry.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
async def call_llm_with_retry(prompt: str) -> str:
    """Llamada a LLM con retry automático"""
    return await llm_service.generate_content_async("gemma-3-27b-it", prompt)
```

**Beneficios:**
- ✅ Resiliencia ante fallos temporales
- ✅ Mejor experiencia de usuario
- ✅ Menos errores reportados

**Esfuerzo:** Bajo  
**Prioridad:** MEDIA

---

### 5.10 Mejora 10: Health Checks y Métricas

**Objetivo:** Monitoreo y observabilidad

**Cambios Propuestos:**

```python
# chatbot/routes/health.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Métricas
request_count = Counter('chatbot_requests_total', 'Total requests')
request_duration = Histogram('chatbot_request_duration_seconds', 'Request duration')
active_conversations = Gauge('chatbot_active_conversations', 'Active conversations')
db_connection_pool = Gauge('chatbot_db_pool_size', 'DB pool size', ['db_type'])

@router.get("/health")
async def health_check():
    """Health check completo"""
    health = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check PostgreSQL
    try:
        db = obtener_session_db()
        db.execute("SELECT 1")
        health["checks"]["postgresql"] = "healthy"
        db.close()
    except Exception as e:
        health["checks"]["postgresql"] = f"unhealthy: {e}"
        health["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client = obtener_cliente_redis()
        redis_client.ping()
        health["checks"]["redis"] = "healthy"
    except Exception as e:
        health["checks"]["redis"] = f"unhealthy: {e}"
        health["status"] = "degraded"
    
    # Check Oracle
    try:
        # Test connection
        health["checks"]["oracle"] = "healthy"
    except Exception as e:
        health["checks"]["oracle"] = f"unhealthy: {e}"
        health["status"] = "degraded"
    
    return health

@router.get("/metrics")
async def metrics():
    """Endpoint de métricas Prometheus"""
    return Response(
        generate_latest(),
        media_type="text/plain"
    )
```

**Beneficios:**
- ✅ Visibilidad del estado del sistema
- ✅ Alertas proactivas
- ✅ Análisis de performance

**Esfuerzo:** Medio  
**Prioridad:** MEDIA

---

## 6. PLAN DE IMPLEMENTACIÓN

### Fase 1: Mejoras Críticas (Semanas 1-2)

**Objetivo:** Hacer el sistema escalable horizontalmente

1. ✅ **Mejora 1:** Migración de estado a Redis
   - Eliminar `user_states` en memoria
   - Crear `RedisStateManager`
   - Refactorizar todas las referencias

2. ✅ **Mejora 3:** Dependency Injection para Oracle
   - Corregir uso de `get_db()`
   - Refactorizar `OracleRepository`

**Resultado Esperado:** Sistema escalable horizontalmente

---

### Fase 2: Mejoras de Performance (Semanas 3-4)

**Objetivo:** Mejorar rendimiento y resiliencia

1. ✅ **Mejora 2:** Pool de conexiones Redis
2. ✅ **Mejora 4:** Circuit Breaker para Oracle
3. ✅ **Mejora 5:** Cache de consultas frecuentes
4. ✅ **Mejora 8:** Async para LLM

**Resultado Esperado:** Mejor rendimiento y resiliencia

---

### Fase 3: Mejoras de Operación (Semanas 5-6)

**Objetivo:** Mejorar operabilidad y seguridad

1. ✅ **Mejora 6:** Rate Limiting
2. ✅ **Mejora 7:** Logging Estructurado
3. ✅ **Mejora 9:** Retry Logic
4. ✅ **Mejora 10:** Health Checks y Métricas

**Resultado Esperado:** Sistema operacional y monitoreable

---

### Fase 4: Testing y Documentación (Semana 7)

1. ✅ Tests unitarios
2. ✅ Tests de integración
3. ✅ Tests de carga
4. ✅ Documentación actualizada

**Resultado Esperado:** Sistema robusto y documentado

---

## RESUMEN DE PRIORIDADES

### 🔴 CRÍTICAS (Implementar primero)
1. Migración de estado a Redis
2. Dependency Injection para Oracle

### 🟡 ALTAS (Implementar en Fase 2)
3. Pool de conexiones Redis
4. Circuit Breaker para Oracle
5. Cache de consultas frecuentes

### 🟢 MEDIAS (Implementar en Fase 3)
6. Rate Limiting
7. Async para LLM
8. Retry Logic
9. Health Checks y Métricas

### ⚪ BAJAS (Opcional)
10. Logging Estructurado

---

## MÉTRICAS DE ÉXITO

### Escalabilidad
- ✅ Sistema puede escalar horizontalmente (múltiples workers)
- ✅ Estado compartido entre workers
- ✅ Sin pérdida de estado en reinicios

### Performance
- ✅ Tiempo de respuesta < 2 segundos (p95)
- ✅ Cache hit rate > 70%
- ✅ Pool de conexiones utilizado eficientemente

### Resiliencia
- ✅ Circuit breakers activos
- ✅ Retry logic funcionando
- ✅ Health checks pasando

### Operación
- ✅ Métricas disponibles
- ✅ Logs estructurados
- ✅ Rate limiting activo

---

**Documento creado:** Enero 2025  
**Próxima revisión:** Después de implementación de Fase 1
