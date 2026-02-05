# Solución: Error ORA-12262 - Hostname no resuelto en Docker

## 🔍 Problema Identificado

El error `ORA-12262: Could not resolve hostname oda-x8-2ha-vm1` ocurre porque:

1. ✅ El hostname es accesible desde el **host** (Windows)
2. ❌ El contenedor Docker **no puede resolver** el hostname
3. 🔍 El hostname se resuelve a: `192.168.128.42`

**Causa:** Los contenedores Docker en Windows tienen su propia red y no pueden acceder al DNS del host para resolver hostnames de la red interna.

---

## ✅ Solución: Usar IP Directa

### Opción 1: Modificar `.env` (Recomendado)

Cambia el DSN para usar la IP directamente:

```env
# Antes
ORACLE_DSN=oda-x8-2ha-vm1:1521/OPEXTDESA

# Después
ORACLE_DSN=192.168.128.42:1521/OPEXTDESA
```

**Ventajas:**
- ✅ Funciona inmediatamente
- ✅ No requiere cambios en Docker
- ✅ Más rápido (no necesita resolver DNS)

**Desventajas:**
- ⚠️ Si la IP cambia, necesitas actualizarla

---

### Opción 2: Agregar al `/etc/hosts` del Contenedor

Puedes agregar el hostname al archivo `/etc/hosts` del contenedor:

**Modificar `docker-compose.yml`:**

```yaml
services:
  app:
    # ... otras configuraciones ...
    extra_hosts:
      - "oda-x8-2ha-vm1:192.168.128.42"
```

**Ventajas:**
- ✅ Mantiene el hostname legible
- ✅ Funciona con el hostname original

**Desventajas:**
- ⚠️ Necesitas actualizar si la IP cambia

---

### Opción 3: Usar `network_mode: "host"` (Solo Linux)

Si estás en Linux, puedes usar:

```yaml
services:
  app:
    network_mode: "host"
```

**⚠️ Nota:** Esto NO funciona en Windows/Mac con Docker Desktop.

---

## 🚀 Implementación Rápida

### Paso 1: Actualizar `.env`

```env
ORACLE_DSN=192.168.128.42:1521/OPEXTDESA
```

### Paso 2: Reiniciar el contenedor

```bash
docker compose restart app
```

### Paso 3: Probar la conexión

```bash
docker exec chatbot_app python /app/test_oracle_connection.py
```

---

## 🔍 Verificar Conectividad desde el Contenedor

Después de cambiar a IP, verifica:

```bash
# Verificar que la IP sea accesible
docker exec chatbot_app ping -c 3 192.168.128.42

# Verificar que el puerto esté abierto
docker exec chatbot_app nc -zv 192.168.128.42 1521
```

---

## 📝 Notas Importantes

1. **IP Dinámica:** Si la IP del servidor Oracle cambia, necesitarás actualizar el `.env`

2. **Firewall:** Asegúrate de que el puerto 1521 esté abierto y accesible desde el contenedor

3. **Red Docker:** Si el servidor Oracle está en la misma red que el host, usar la IP debería funcionar

4. **Alternativa:** Si prefieres mantener el hostname, usa `extra_hosts` en `docker-compose.yml`

---

## ✅ Checklist

- [ ] Actualizar `ORACLE_DSN` en `.env` con la IP
- [ ] Reiniciar contenedor: `docker compose restart app`
- [ ] Ejecutar script de prueba
- [ ] Verificar conectividad de red desde contenedor
- [ ] Probar endpoint `/health/oracle`
