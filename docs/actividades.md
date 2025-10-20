# ACTIVIDADES DEL PROYECTO CHATBOT JNE SIMPLIFICADO

## COMMITS POR AUTOR

### deglan-rivas

**2025-09-16**
- feat: migrate core logic from telegram.py to whatsapp router
  - Migrar lógica principal del bot de Telegram hacia el router de WhatsApp
  - Crear utilidades centralizadas para el manejo del chatbot

- feat: crear whatsapp router para setear el webhook y recibir eventos de whatsapp
  - Implementar endpoint para configurar webhook de WhatsApp
  - Agregar funcionalidad para recibir y procesar eventos de WhatsApp

**2025-08-18**
- fix: agregar nuevo caso: desde la db puede venir 'SETIEMBRE' como 'SEPTIEMBRE'
  - Corregir manejo de variaciones del mes de septiembre en datos de BD

- fix: antes se corrigió el emoji, ahora la respuesta del bot si la fecha ya llegó o aún no llega
  - Mejorar lógica de validación de fechas en cronograma electoral

- fix: corregir fecha como 'soon' y 'cumplidas' para el cronograma electoral
  - Implementar estados de tiempo para fechas próximas y cumplidas

- fix: remove redundant data from 'Servicios Digitales' submen
  - Limpiar datos duplicados en menú de servicios digitales

- fix: remove accents
  - Normalizar texto removiendo acentos de archivos CSV

- fix: ensure '_handle_tramite' returns (str, bool) tuple in 'Servicios Digitales' submenu
  - Corregir tipo de retorno de función de manejo de trámites

- fix: add 'pleno' submenu to 'menus' dictionary
  - Agregar submenú faltante para funcionalidad de pleno

**2025-08-17**
- chore: add temporary changes to deploy using containers
  - Configurar archivos Docker para despliegue en contenedores

**2025-08-16**
- feat: fix temporary docker files
  - Corregir configuración de Docker y archivos de conexión Oracle

**2025-08-14**
- feat: create functions to recieve from and send message to telegram
  - Implementar funciones base para comunicación con API de Telegram

- docs: improve details about setup and run project - README.md
  - Mejorar documentación de instalación y ejecución del proyecto

- chore: remove tracking of .txt and .lock files
  - Actualizar .gitignore para excluir archivos temporales

- chore: add docker compose to connect redis and postgres containers
  - Configurar Docker Compose para servicios de base de datos

**2025-08-13**
- feat: change models from openai to google gemini because of response time
  - Migrar de OpenAI a Google Gemini para mejorar tiempo de respuesta

- feat: add basic functions to get and send messages from telegram
  - Implementar funciones básicas de mensajería con Telegram

**2025-08-12**
- feat: draw basic version of tree decision chatbot
  - Crear estructura básica del árbol de decisiones del chatbot

**2025-08-11**
- feat: release first version by cloning a basic skeleton
  - Crear versión inicial del proyecto con estructura básica

### odt013

**2025-08-18**
- fix: correct errors in electoral processes and services integration
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Corregir errores en integración de procesos electorales y servicios digitales
  - Actualizar repositorio Oracle y rutas de Telegram
  - Mejorar gestión de procesos electorales y servicios digitales

**2025-08-16**
- refactor: restructure codebase and fix integration errors
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Refactorizar código base y corregir errores de integración
  - Actualizar archivos CSV de servicios digitales
  - Mejorar documentación README
  - Refactorizar modelos y repositorio Oracle
  - Optimizar rutas de Telegram y gestión de procesos electorales

**2025-08-15**
- feat: implement cancel and menu navigation functionality
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Implementar funcionalidad de cancelar y navegación de menús
  - Agregar opciones de cancelar operaciones
  - Mejorar navegación entre menús del chatbot

- feat: complete electoral processes module implementation
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Completar implementación del módulo de procesos electorales
  - Implementar repositorio Oracle completo
  - Agregar funcionalidades completas de rutas Telegram
  - Crear gestión completa de procesos electorales

- feat: add electoral processes core functionality
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Agregar funcionalidad principal de procesos electorales
  - Configurar conexión Oracle
  - Implementar modelos de base de datos Oracle
  - Crear repositorio y gestión de procesos electorales
  - Actualizar rutas principales de Telegram

**2025-08-14**
- feat: add institutional information sections 3.A,B,C,D
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Agregar secciones de información institucional 3.A,B,C,D
  - Completar datos de funcionarios en archivos CSV

- feat: implement section 4.B functionality
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Implementar funcionalidad de sección 4.B

- feat: implement section 4.A functionality
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Implementar funcionalidad de sección 4.A

**2025-08-13**
- feat: implement chat memory with Redis and chat logging with PostgreSQL
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Implementar memoria de chat con Redis y logging con PostgreSQL
  - Configurar conexiones Redis y PostgreSQL
  - Resolver conflictos de integración

- feat: add Redis and PostgreSQL database connections
  - DESCRIPCIÓN MEJORADA BASADA EN CAMBIOS: Agregar conexiones a bases de datos Redis y PostgreSQL
  - Configurar conexiones a Redis para cache
  - Configurar conexiones a PostgreSQL para persistencia

## RESUMEN DE ACTIVIDADES

**TOTAL DE COMMITS:** 30
- **deglan-rivas:** 19 commits
- **odt013:** 11 commits

**PERÍODO DE DESARROLLO:** Agosto 11, 2025 - Septiembre 16, 2025

**FUNCIONALIDADES PRINCIPALES DESARROLLADAS:**
1. Estructura base del chatbot con árbol de decisiones
2. Integración con Telegram API
3. Conexión a bases de datos Oracle, PostgreSQL y Redis
4. Implementación de procesos electorales
5. Gestión de servicios digitales
6. Información institucional
7. Migración hacia WhatsApp
8. Sistema de contenedores Docker
9. Documentación y configuración del proyecto