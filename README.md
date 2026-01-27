# Chatbot JNE Simplificado

## Requisitos
- Python 3.10+
- uv (gestor de dependencias)
- Redis
- Base de datos (PostgreSQL)
- Docker
- LLM (OpenAI o Google Gemini)
- Telegram
- Cloudflared (Solo si se quiere exponer el backend e interactuar mediante Telegram)

## Instalacion y configuracion

Consultar la [guia de instalacion](SETUP.md) para los pasos detallados.

## Estructura
- `routes/`: endpoints de Telegram y API Gateway
- `services/`: lógica de validación, enriquecimiento, ejecución LangGraph y logging en DB
- `config.py`: carga de configuración

## Funcionalidades del Chatbot

#### **Menú Principal (4 opciones):**
1. **Procesos Electorales** - Cronogramas y consulta de políticos
2. **Organizaciones Políticas** - Tipos y consulta de afiliación
3. **Información Institucional** - Pleno, funcionarios, JEE y sedes
4. **Servicios Digitales** - Servicios ciudadanos y búsqueda de trámites

#### **Submenús Especializados:**
- **Cronograma Electoral**: Procesos específicos (EG.2026, EMC.2025, ERM.2022, EG.2021)
- **Consulta de Políticos**: Búsqueda por nombres y apellidos
- **Pleno del JNE**: Miembros y cargos específicos
- **Servicios Digitales**: Catálogo de servicios disponibles

### 🔄 **Menús Dinámicos**

#### **Generación Automática:**
- **Servicios Digitales**: Se cargan desde archivos CSV (`RAG/SERVICIOS_DIGITALES.csv`)
- **Pleno del JNE**: Se construye dinámicamente desde `RAG/PLENO.csv`
- **Procesos Electorales**: Se obtienen en tiempo real desde la base de datos Oracle

#### **Adaptación Contextual:**
- Los menús se adaptan según el estado del usuario
- Opciones se generan dinámicamente basadas en la consulta
- Navegación fluida entre diferentes niveles de información

### 📊 **Obtención de Información**

#### **Fuentes de Datos:**
1. **Base de Datos Oracle**: Información electoral, candidatos, hitos y cronogramas
2. **Archivos CSV (RAG)**: Datos estáticos como funcionarios, servicios y pleno
3. **LLM (Gemini)**: Búsqueda semántica y generación de respuestas contextualizadas

#### **Flujo de Datos:**
```
Usuario → Consulta → Búsqueda Semántica (LLM) → Base de Datos → Respuesta Contextualizada
```

#### **Tipos de Consulta:**
- **Búsqueda Directa**: Información institucional y servicios
- **Búsqueda Semántica**: Hitos electorales y trámites específicos
- **Búsqueda de Candidatos**: Por nombres, apellidos y elecciones

### 🧠 **Intervención del LLM (Gemini)**

#### **Funciones Principales:**
1. **Búsqueda Semántica de Hitos Electorales:**
   - Analiza consultas en lenguaje natural
   - Selecciona hitos más relevantes del cronograma
   - Proporciona contexto temporal (pasado/futuro)

2. **Búsqueda de Servicios Digitales:**
   - Interpreta consultas de trámites
   - Encuentra servicios más relevantes
   - Genera respuestas contextualizadas

3. **Generación de Respuestas Amigables:**
   - Convierte información técnica en lenguaje simple
   - Agrega contexto temporal y relevancia
   - Optimiza respuestas para dispositivos móviles

#### **Proceso de Búsqueda Semántica:**
```
1. Usuario: "¿Cuándo son las elecciones generales?"
2. LLM: Analiza consulta y contexto
3. Base de Datos: Obtiene todos los hitos del proceso electoral
4. LLM: Selecciona los 5 hitos más relevantes
5. Respuesta: Menú con hitos seleccionados y contexto temporal
```

#### **Fallback Inteligente:**
- Si el LLM falla, se activa algoritmo de puntuación por relevancia
- Sistema de scoring basado en palabras clave y contexto temporal
- Priorización de hitos futuros y recientes

### 🎯 **Características Técnicas**

#### **Arquitectura Modular:**
- **ChatbotStateManager**: Manejo de estados y transiciones
- **ResponseManager**: Gestión de respuestas y logging
- **MenuHandler**: Lógica de navegación por menús
- **StateHandler**: Manejo de estados específicos

#### **Gestores de Servicios:**
- **ProcesosElectoralesManager**: Lógica electoral y candidatos
- **ServiciosDigitalesManager**: Catálogo de servicios
- **InformacionInstitucionalManager**: Datos institucionales

#### **Comandos de Navegación:**
- **`menu`**: Regresa al menú principal (preserva estado)
- **`adios`**: Finaliza la conversación y cierra sesión
- **`salir`**: Regresa al menú principal (reinicia estado)

