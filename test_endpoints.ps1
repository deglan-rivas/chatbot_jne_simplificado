# Script de Prueba de Endpoints - Chatbot JNE
# Ejecutar: .\test_endpoints.ps1

Write-Host "🧪 Probando Endpoints del Chatbot JNE" -ForegroundColor Cyan
Write-Host ""

# 1. Health Check
Write-Host "1️⃣ Probando Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method GET
    Write-Host "✅ Health Check OK: $($response | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error en Health Check: $_" -ForegroundColor Red
}
Write-Host ""

# 2. REST API - Enviar Mensaje
Write-Host "2️⃣ Probando REST API - Enviar Mensaje..." -ForegroundColor Yellow
try {
    $body = @{
        user_id = "test_ps1_$(Get-Random)"
        message = "Hola, quiero información sobre procesos electorales"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/web/chat/message" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    Write-Host "✅ Mensaje enviado correctamente" -ForegroundColor Green
    Write-Host "Respuesta del bot:" -ForegroundColor Cyan
    Write-Host $response.response -ForegroundColor White
    Write-Host ""
    Write-Host "Estado:" -ForegroundColor Cyan
    Write-Host ($response | ConvertTo-Json -Depth 3) -ForegroundColor Gray
} catch {
    Write-Host "❌ Error enviando mensaje: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
Write-Host ""

# 3. Iniciar Conversación
Write-Host "3️⃣ Probando Iniciar Conversación..." -ForegroundColor Yellow
try {
    $body = @{
        user_id = "test_start_$(Get-Random)"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/web/chat/start" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body

    Write-Host "✅ Conversación iniciada" -ForegroundColor Green
    Write-Host "User ID: $($response.user_id)" -ForegroundColor Cyan
    Write-Host "Mensaje de bienvenida:" -ForegroundColor Cyan
    Write-Host $response.welcome_message -ForegroundColor White
} catch {
    Write-Host "❌ Error iniciando conversación: $_" -ForegroundColor Red
}
Write-Host ""

# 4. Obtener Historial (usando el user_id del paso anterior)
Write-Host "4️⃣ Probando Obtener Historial..." -ForegroundColor Yellow
try {
    $userId = "test_ps1_$(Get-Random)"
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/web/chat/history/$userId" -Method GET
    Write-Host "✅ Historial obtenido" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 2) -ForegroundColor Gray
} catch {
    Write-Host "⚠️ No hay historial (normal si es usuario nuevo)" -ForegroundColor Yellow
}
Write-Host ""

# 5. Estado de Conexión
Write-Host "5️⃣ Probando Estado de Conexión..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/web/chat/status/test123" -Method GET
    Write-Host "✅ Estado obtenido" -ForegroundColor Green
    Write-Host "Conectado: $($response.connected)" -ForegroundColor Cyan
    Write-Host "Conexiones activas: $($response.active_connections)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Error obteniendo estado: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "✅ Pruebas completadas!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Para probar WebSocket, abre tu navegador en http://localhost:8001" -ForegroundColor Cyan
Write-Host "   y ejecuta en la consola:" -ForegroundColor Cyan
Write-Host ""
Write-Host '   const ws = new WebSocket("ws://localhost:8001/api/web/chat/ws?user_id=test123");' -ForegroundColor Gray
Write-Host '   ws.onmessage = (e) => console.log("Bot:", JSON.parse(e.data).content);' -ForegroundColor Gray
Write-Host '   ws.onopen = () => ws.send(JSON.stringify({type: "message", message: "Hola"}));' -ForegroundColor Gray
