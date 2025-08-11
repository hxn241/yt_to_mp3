# 🎵 Bot de Telegram YouTube MP3 - Versión Multiusuario

> **Bot profesional listo para producción 24/7** con soporte completo para múltiples usuarios, playlists, logging avanzado y reinicio automático.

## 🌟 Características Principales

- 🎵 **Descargas individuales** de YouTube con formato `artist - title`
- 📋 **Playlists completas** hasta 30 videos por playlist
- 👥 **Multiusuario simultáneo** (hasta 3 descargas concurrentes)
- 🔄 **Reinicio automático** para operación 24/7
- 📊 **Logging completo** con rotación automática
- ⚡ **Barras de progreso interactivas** en tiempo real
- 🛡️ **Control de límites** y validación de URLs
- 🗑️ **Limpieza automática** de archivos temporales

## 🚀 Inicio Rápido

### 1. Preparación
```bash
# Clonar y navegar al proyecto
cd c:\Users\Cristian\Documents\projects\get_mp3

# Configurar token en .env
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

### 2. Ejecutar Bot

#### 🌟 Modo 24/7 (Recomendado)
```bash
start_24h_bot.bat
```

#### 🔧 Modo Desarrollo
```bash
start_multiuser_bot.bat
```

#### 🔄 Reiniciar Bot
```bash
restart_bot.bat
```

## 📋 Comandos del Bot

### 🎵 Comandos de Descarga
```
/download <URL>    - Descarga video individual
/get <URL>        - Alias para /download
/playlist <URL>   - Descarga playlist completa (máx 30 videos)
```

### ℹ️ Comandos de Información  
```
/start    - Mensaje de bienvenida con instrucciones
/help     - Ayuda detallada con ejemplos
/stats    - Estadísticas de uso del bot
/status   - Estado actual y descargas activas
```

## 🎯 Ejemplos de Uso

### Video Individual
```
/download https://www.youtube.com/watch?v=dQw4w9WgXcQ
/get https://youtu.be/dQw4w9WgXcQ
```

### Playlist Completa
```
/playlist https://www.youtube.com/playlist?list=PLAYLIST_ID
/playlist https://www.youtube.com/watch?v=VIDEO&list=PLAYLIST_ID
```

### Formato de Archivos Resultante
- `Alessia_Cara - Scars_To_Your_Beautiful.mp3`
- `Crystal_Castles - Kerosene.mp3`
- `The_Beatles - Yesterday.mp3`

## 🏗️ Arquitectura Multiusuario

### 🔄 Manejo de Usuarios Simultáneos
```
Usuario A: /download URL1  ← Descargando en user_12345_abc123/
Usuario B: /download URL2  ← Descargando en user_67890_def456/  
Usuario C: /playlist URL3  ← Descargando en user_11111_ghi789/
Usuario D: /download URL4  ← ⏳ En cola (límite alcanzado)
```

### 🛡️ Protecciones Implementadas
- ✅ **Directorios únicos** por usuario (evita conflictos)
- ✅ **Control de concurrencia** (máx 3 descargas simultáneas)
- ✅ **Una descarga por usuario** (evita saturación)
- ✅ **Limpieza automática** después del envío

## ⚙️ Configuración Avanzada

### Variables de Entorno (.env)
```env
# Token obligatorio
TELEGRAM_BOT_TOKEN=tu_token_aqui

# Límites configurables
MAX_FILE_SIZE_MB=50              # Tamaño máximo por archivo
DOWNLOAD_TIMEOUT=300             # Timeout en segundos (5 min)
MAX_CONCURRENT_DOWNLOADS=3       # Descargas simultáneas máximas

# Directorios
TEMP_DIR=./downloads            # Carpeta temporal
```

### Límites por Defecto
- **📁 Tamaño máximo**: 50MB por archivo (límite de Telegram)
- **⏱️ Duración máxima**: 30 minutos por video individual  
- **📋 Playlist máxima**: 30 videos por playlist
- **🔄 Descargas simultáneas**: 3 usuarios concurrentes
- **⏳ Timeout**: 5 minutos por descarga

## 📊 Sistema de Logging 24/7

### 📁 Archivos de Log
```
logs/
├── bot_general.log     # Actividad general y estadísticas
├── bot_errors.log      # Errores que requieren atención  
├── bot_downloads.log   # Historial detallado de descargas
└── startup.log         # Inicios y reinicios del bot
```

### 🔍 Información Registrada
- 👤 **Usuarios**: ID, nombre, username de cada solicitud
- 🔗 **URLs**: Todas las URLs procesadas con resultado
- ⏱️ **Tiempos**: Duración de cada descarga
- 📊 **Estadísticas**: Contadores de éxito/error
- ❌ **Errores**: Tracebacks completos para debugging

### 📈 Monitoreo Automático
- ✅ **Health check** cada 5 minutos
- ✅ **Estadísticas** cada hora  
- ✅ **Reporte completo** cada 24 horas
- ✅ **Tracking** de usuarios únicos

## 🔄 Sistema de Reinicio Automático

### 🛡️ Funciones de Supervivencia 24/7
- **Reinicio automático** tras errores críticos
- **Gestión de señales** para cierre limpio (Ctrl+C, SIGTERM)
- **Recovery automático** de errores de red temporales
- **Logging de eventos** de inicio/parada

### 📋 Script start_24h_bot.bat
```batch
:RESTART_LOOP
echo 🔄 Iniciando bot...
powershell -Command "& { .\.venv\Scripts\Activate.ps1; python bot_multiuser.py }"

if errorlevel 1 (
    echo ⚠️ Bot se detuvo - Reiniciando en 10 segundos...
    timeout /t 10
    goto RESTART_LOOP
)
```

## 📦 Instalación Completa

### 1. Dependencias del Sistema
```bash
# Instalar uv (gestor de paquetes Python)
# Windows: https://docs.astral.sh/uv/getting-started/installation/

# Verificar uv
uv --version
```

### 2. Configurar Virtual Environment
```bash
# Crear entorno virtual
uv venv

# Instalar dependencias
uv pip install -r requirements.txt
```

### 3. Configurar Bot de Telegram
1. Crear bot con [@BotFather](https://t.me/BotFather)
2. Usar `/newbot` y seguir instrucciones
3. Guardar token en archivo `.env`

### 4. Estructura Final del Proyecto
```
get_mp3/
├── 🤖 Bot principal
│   ├── bot_multiuser.py        # Bot con logging y multiusuario
│   ├── downloader_multiuser.py # Downloader robusto
│   └── .env                    # Configuración (TOKEN aquí)
│
├── 🚀 Scripts de inicio  
│   ├── start_24h_bot.bat       # Modo 24/7 con reinicio automático
│   ├── start_multiuser_bot.bat # Modo desarrollo
│   └── restart_bot.bat         # Reinicio manual
│
├── 📊 Configuración
│   ├── requirements.txt        # Dependencias Python
│   ├── pyproject.toml         # Configuración del proyecto
│   └── uv.lock                # Lock file de dependencias
│
├── 📁 Datos y logs
│   ├── downloads/             # Archivos temporales (auto-cleanup)
│   └── logs/                  # Sistema de logging rotativo
│
└── 📚 Documentación
    └── README.md              # Este archivo
```

## 🛠️ Tecnologías Utilizadas

### Core
- **[python-telegram-bot](https://python-telegram-bot.org/)** `22.3` - Framework principal para bots
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** `2025.7.21` - Descarga de YouTube (sucesor de youtube-dl)
- **[asyncio](https://docs.python.org/3/library/asyncio.html)** - Programación asíncrona nativa

### Gestión
- **[uv](https://docs.astral.sh/uv/)** - Gestor rápido de paquetes y entornos Python
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** - Variables de entorno
- **[nest-asyncio](https://pypi.org/project/nest-asyncio/)** - Manejo de loops asíncronos anidados

## 🚦 Estados del Bot

### 🟢 Bot Disponible
```
🚀 Bot multiusuario iniciado y funcionando
📊 Descargas activas: 0/3
✅ Listo para nuevas descargas
```

### 🟡 Bot Ocupado  
```
🚦 Bot ocupado - Descargas activas: 3/3
⏳ Intenta en unos momentos
```

### 🔴 Bot con Problemas
```
❌ Error crítico detectado
🔄 Reiniciando automáticamente en 10 segundos...
📝 Revisa logs/bot_errors.log para detalles
```

## 🐛 Solución de Problemas

### Error: Virtual Environment No Encontrado
```bash
# Crear nuevo entorno virtual
uv venv
uv pip install -r requirements.txt
```

### Error: Token Inválido
```bash
# Verificar .env
TELEGRAM_BOT_TOKEN=123456789:ABC...  # Debe empezar con números
```

### Bot No Responde
```bash
# Verificar logs
type logs\bot_errors.log
type logs\startup.log

# Reiniciar manualmente  
restart_bot.bat
```

### Archivos Muy Grandes (>50MB)
```
❌ Limitación de Telegram Bot API
💡 Usa videos más cortos o listas más pequeñas
⚙️ El límite no se puede cambiar (restricción de Telegram)
```

## 📈 Estadísticas de Rendimiento

### 📊 Capacidad Teórica
- **👥 Usuarios simultáneos**: 3 descargas concurrentes
- **📋 Playlist máxima**: 30 videos × 50MB = 1.5GB por playlist
- **⏱️ Tiempo por descarga**: ~30-120 segundos promedio
- **🔄 Disponibilidad**: 24/7 con reinicio automático

### 🎯 Métricas Monitoreadas
El comando `/stats` proporciona:
- ⏱️ **Uptime** del bot
- 📥 **Descargas exitosas** vs fallidas
- 📋 **Playlists procesadas** 
- 📤 **Total de archivos enviados**
- 👤 **Usuarios únicos**
- 🔄 **Descargas activas actuales**

## ⚖️ Consideraciones Legales y Éticas

### 📜 Uso Responsable
- ✅ Solo descargar contenido **con permisos apropiados**
- ✅ **Respetar términos de servicio** de YouTube
- ✅ Uso **personal/educativo** recomendado
- ✅ **No redistribuir** contenido con derechos de autor

### ⚠️ Limitaciones Técnicas
- Bot usa `yt-dlp` (no API oficial de YouTube)
- Dependiente de disponibilidad de YouTube
- Archivos se eliminan automáticamente tras el envío
- Control de límites para evitar abusos

## 🚀 Producción y Deployment

### ✅ Checklist de Producción
- [x] **Logging completo** implementado con rotación
- [x] **Reinicio automático** configurado  
- [x] **Limpieza de recursos** automática
- [x] **Control de concurrencia** implementado
- [x] **Gestión de errores** robusta
- [x] **Monitoreo 24/7** activo
- [x] **Variables de entorno** configuradas
- [x] **Virtual environment** aislado

### 🎬 Iniciar en Producción
```bash
# Terminal/CMD como administrador
cd c:\Users\Cristian\Documents\projects\get_mp3
start_24h_bot.bat

# El bot iniciará automáticamente y se mantendrá corriendo
# Presiona Ctrl+C para detener manualmente (cierre limpio)
```

### 📊 Monitoreo en Producción
```bash
# Verificar logs en tiempo real
Get-Content logs\bot_general.log -Wait    # PowerShell
tail -f logs/bot_general.log              # Git Bash/WSL

# Ver errores recientes
type logs\bot_errors.log | select -Last 10

# Estado de archivos temporales
dir downloads\
```

---

## 🎉 **¡Bot Listo para Uso 24/7!**

### 🌟 **Para Usuarios**
- Envía `/start` al bot para comenzar
- Usa `/help` para ver todos los comandos
- Disfruta descargas rápidas y sin conflictos

### 🔧 **Para Administradores**  
- Ejecuta `start_24h_bot.bat` para iniciar
- Revisa `logs/` para monitorear estado
- El bot se reinicia automáticamente si hay problemas

**¡Disfruta tu bot de música profesional! 🎵✨**
