# Guía: Verificar Conexión a Oracle desde Docker

## 🔍 Métodos de Verificación

### Método 1: Script de Prueba (Recomendado)

Ejecuta el script de prueba desde dentro del contenedor:

```bash
docker exec chatbot_app python /app/test_oracle_connection.py
```

Este script:
- ✅ Muestra todas las variables de configuración
- ✅ Verifica que el cliente Oracle esté instalado
- ✅ Intenta inicializar el cliente Oracle
- ✅ Intenta conectar a la base de datos
- ✅ Ejecuta una consulta de prueba
- ✅ Muestra información detallada de errores si falla

**Salida esperada (éxito):**
```
============================================================
🔍 Verificando Configuración de Oracle
============================================================

📋 Variables de Entorno:
   ORACLE_USER: eleccia
   ORACLE_PASS: ********
   ORACLE_DSN: oda-x8-2ha-vm1:1521/OPEXTDESA
   TNS_ADMIN: /app
   ORACLEDB_CLIENT_PATH: /opt/oracle/instantclient_23_8

🔧 Verificando Cliente Oracle:
   ✅ Cliente Oracle encontrado en: /opt/oracle/instantclient_23_8
   ✅ libclntsh.so encontrado

🔌 Inicializando Cliente Oracle:
   Detectado entorno Docker/Linux
   ✅ Cliente Oracle inicializado (modo Linux)

🌐 Intentando Conectar a Oracle:
   DSN: oda-x8-2ha-vm1:1521/OPEXTDESA
   User: eleccia
   ✅ ¡Conexión exitosa!

📊 Ejecutando Consulta de Prueba:
   ✅ Fecha del servidor Oracle: 2025-01-22 10:30:00
   ✅ Versión Oracle: Oracle Database 19c Enterprise Edition...

✅ Prueba completada exitosamente!
```

---

### Método 2: Endpoint de Health Check

Verifica la conexión Oracle a través del endpoint HTTP:

```bash
curl http://localhost:8001/health/oracle
```

**Respuesta exitosa:**
```json
{
  "status": "ok",
  "oracle": {
    "connected": true,
    "server_date": "2025-01-22 10:30:00",
    "dsn": "oda-x8-2ha-vm1:1521/OPEXTDESA",
    "user": "eleccia"
  }
}
```

**Respuesta con error:**
```json
{
  "status": "error",
  "oracle": {
    "connected": false,
    "error": "ORA-12154: TNS:could not resolve the connect identifier",
    "dsn": "oda-x8-2ha-vm1:1521/OPEXTDESA",
    "user": "eleccia"
  }
}
```

---

### Método 3: Verificar Variables de Entorno

Verifica que las variables de entorno estén correctamente configuradas en el contenedor:

```bash
docker exec chatbot_app printenv | grep -i oracle
```

**Salida esperada:**
```
ORACLE_USER=eleccia
ORACLE_PASS=desarrollo
ORACLE_DSN=oda-x8-2ha-vm1:1521/OPEXTDESA
TNS_ADMIN=/app
ORACLEDB_CLIENT_PATH=/opt/oracle/instantclient_23_8
LD_LIBRARY_PATH=/opt/oracle/instantclient_23_8:...
```

---

### Método 4: Verificar Cliente Oracle Instalado

Verifica que el cliente Oracle esté correctamente instalado:

```bash
docker exec chatbot_app ls -la /opt/oracle/instantclient_23_8/ | head -20
```

**Deberías ver:**
```
libclntsh.so -> libclntsh.so.23.1
libclntsh.so.23.1
libocci.so.23.1
...
```

---

### Método 5: Verificar desde Python Interactivo

Accede al contenedor y prueba manualmente:

```bash
docker exec -it chatbot_app python
```

Luego ejecuta:

```python
import oracledb
from chatbot.config import settings

# Inicializar cliente
oracledb.init_oracle_client(lib_dir="/opt/oracle/instantclient_23_8")

# Intentar conectar
conn = oracledb.connect(
    user=settings.ORACLE_USER,
    password=settings.ORACLE_PASS,
    dsn=settings.ORACLE_DSN
)

# Ejecutar consulta
cursor = conn.cursor()
cursor.execute("SELECT SYSDATE FROM DUAL")
print(cursor.fetchone())

cursor.close()
conn.close()
```

---

## 🐛 Troubleshooting

### Error: "TNS:could not resolve the connect identifier"

**Causa:** El DSN no es accesible o está mal formado.

**Soluciones:**
1. Verifica que el servidor Oracle sea accesible desde el contenedor:
   ```bash
   docker exec chatbot_app ping -c 3 oda-x8-2ha-vm1
   ```

2. Verifica que el puerto esté abierto:
   ```bash
   docker exec chatbot_app nc -zv oda-x8-2ha-vm1 1521
   ```

3. Verifica el formato del DSN:
   - Formato correcto: `host:port/service_name`
   - Ejemplo: `oda-x8-2ha-vm1:1521/OPEXTDESA`

---

### Error: "ORA-01017: invalid username/password"

**Causa:** Credenciales incorrectas.

**Soluciones:**
1. Verifica las credenciales en `.env`:
   ```
   ORACLE_USER=eleccia
   ORACLE_PASS=desarrollo
   ```

2. Verifica que las variables se pasen al contenedor:
   ```bash
   docker exec chatbot_app printenv | grep ORACLE
   ```

---

### Error: "libclntsh.so: cannot open shared object file"

**Causa:** El cliente Oracle no está correctamente instalado o configurado.

**Soluciones:**
1. Verifica que el cliente esté instalado:
   ```bash
   docker exec chatbot_app ls /opt/oracle/instantclient_23_8/libclntsh.so*
   ```

2. Verifica `LD_LIBRARY_PATH`:
   ```bash
   docker exec chatbot_app echo $LD_LIBRARY_PATH
   ```
   Debe incluir: `/opt/oracle/instantclient_23_8`

3. Verifica que `ORACLEDB_CLIENT_PATH` esté correcto:
   ```bash
   docker exec chatbot_app printenv ORACLEDB_CLIENT_PATH
   ```
   Debe ser: `/opt/oracle/instantclient_23_8`

---

### Error: "Network is unreachable" o "Connection timeout"

**Causa:** El servidor Oracle no es accesible desde el contenedor Docker.

**Soluciones:**
1. **Si Oracle está en la misma red:**
   - Asegúrate de que el contenedor pueda acceder a la red del host
   - Usa `network_mode: "host"` en `docker-compose.yml` (solo Linux)

2. **Si Oracle está en otra máquina:**
   - Verifica conectividad de red desde el host:
     ```bash
     ping oda-x8-2ha-vm1
     telnet oda-x8-2ha-vm1 1521
     ```
   - Si funciona desde el host pero no desde el contenedor, agrega `network_mode: "host"` o configura un proxy

3. **Si usas Docker Desktop (Windows/Mac):**
   - El contenedor puede no tener acceso directo a la red del host
   - Considera usar la IP del host en lugar del hostname:
     ```bash
     # En Windows/Mac, usa la IP del host
     ORACLE_DSN=host.docker.internal:1521/OPEXTDESA
     # O la IP real de la máquina
     ORACLE_DSN=192.168.1.100:1521/OPEXTDESA
     ```

---

## ✅ Checklist de Verificación

- [ ] Variables de entorno configuradas en `.env`
- [ ] Variables pasadas al contenedor en `docker-compose.yml`
- [ ] Cliente Oracle instalado en `/opt/oracle/instantclient_23_8`
- [ ] `LD_LIBRARY_PATH` configurado correctamente
- [ ] Servidor Oracle accesible desde el contenedor (ping/telnet)
- [ ] Credenciales correctas
- [ ] DSN correctamente formateado
- [ ] Script de prueba ejecutado exitosamente
- [ ] Health check endpoint responde correctamente

---

## 📝 Notas Importantes

1. **Red Docker:** Por defecto, los contenedores Docker tienen su propia red. Si Oracle está en el host o en otra máquina, puede que necesites configurar la red adecuadamente.

2. **Firewall:** Asegúrate de que el puerto 1521 esté abierto y accesible.

3. **DNS:** Si usas hostnames, asegúrate de que el contenedor pueda resolverlos. Considera usar IPs directamente si hay problemas.

4. **Variables de Entorno:** Las variables en `docker-compose.yml` tienen prioridad sobre `.env`. Verifica que estén correctamente configuradas.

---

## 🔧 Comandos Rápidos

```bash
# Verificar configuración
docker exec chatbot_app python /app/test_oracle_connection.py

# Health check HTTP
curl http://localhost:8001/health/oracle

# Ver variables de entorno
docker exec chatbot_app printenv | grep ORACLE

# Verificar conectividad de red
docker exec chatbot_app ping -c 3 oda-x8-2ha-vm1
docker exec chatbot_app nc -zv oda-x8-2ha-vm1 1521

# Ver logs del contenedor
docker logs chatbot_app | grep -i oracle
```
