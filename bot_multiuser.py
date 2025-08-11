import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ChatAction, ParseMode
from dotenv import load_dotenv
import asyncio
import time
import nest_asyncio
import traceback
from datetime import datetime

from downloader_multiuser import MultiUserYouTubeDownloader
import re

# Permitir event loops anidados
nest_asyncio.apply()

def escape_markdown(text: str) -> str:
    """Escapa caracteres especiales para Markdown V2"""
    # Caracteres que necesitan ser escapados en Markdown V2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Escapar cada carácter especial
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def create_progress_bar(percentage: int, length: int = 20) -> str:
    """Crea una barra de progreso visual"""
    filled = int(length * percentage / 100)
    bar = '█' * filled + '░' * (length - filled)
    return f"`{bar}` {percentage}%"

def format_time(seconds: int) -> str:
    """Formatea segundos en formato mm:ss"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def setup_logging():
    """Configura el sistema de logging con rotación de archivos"""
    # Crear directorio de logs si no existe
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configurar formato de logging
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    
    # Configurar logging principal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Handler para archivo general (con rotación)
    general_handler = RotatingFileHandler(
        logs_dir / "bot_general.log",
        maxBytes=10*1024*1024,  # 10MB por archivo
        backupCount=5,  # Mantener 5 archivos de respaldo
        encoding='utf-8'
    )
    general_handler.setFormatter(log_format)
    general_handler.setLevel(logging.INFO)
    
    # Handler para errores críticos
    error_handler = RotatingFileHandler(
        logs_dir / "bot_errors.log",
        maxBytes=5*1024*1024,  # 5MB por archivo
        backupCount=10,  # Mantener más archivos de error
        encoding='utf-8'
    )
    error_handler.setFormatter(log_format)
    error_handler.setLevel(logging.ERROR)
    
    # Handler para descargas (info detallada)
    downloads_handler = RotatingFileHandler(
        logs_dir / "bot_downloads.log",
        maxBytes=10*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    downloads_handler.setFormatter(log_format)
    downloads_handler.setLevel(logging.INFO)
    
    # Handler para consola (solo info importante)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    
    # Limpiar handlers existentes
    logger.handlers.clear()
    
    # Agregar todos los handlers
    logger.addHandler(general_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    # Logger específico para descargas
    download_logger = logging.getLogger('downloads')
    download_logger.addHandler(downloads_handler)
    download_logger.setLevel(logging.INFO)
    
    return logger

# Configurar logging al importar el módulo
setup_logging()
logger = logging.getLogger(__name__)
download_logger = logging.getLogger('downloads')

class MultiUserTelegramBot:
    """Bot de Telegram para descargar música de YouTube con soporte multiusuario"""
    
    def __init__(self):
        """Inicializa el bot multiusuario con logging completo"""
        try:
            logger.info("🚀 Iniciando bot multiusuario...")
            
            # Cargar variables de entorno
            load_dotenv()
            
            self.token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not self.token:
                logger.critical("❌ TELEGRAM_BOT_TOKEN no encontrado en .env")
                raise ValueError("TELEGRAM_BOT_TOKEN no encontrado en .env")
            
            # Configuración
            self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', 50))
            self.download_timeout = int(os.getenv('DOWNLOAD_TIMEOUT', 300))
            self.temp_dir = os.getenv('TEMP_DIR', './downloads')
            self.max_concurrent_downloads = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', 3))
            
            logger.info(f"📋 Configuración cargada:")
            logger.info(f"   - Max file size: {self.max_file_size_mb}MB")
            logger.info(f"   - Download timeout: {self.download_timeout}s")
            logger.info(f"   - Temp dir: {self.temp_dir}")
            logger.info(f"   - Max concurrent: {self.max_concurrent_downloads}")
            
            # Inicializar downloader multiusuario
            self.downloader = MultiUserYouTubeDownloader(
                base_temp_dir=self.temp_dir,
                max_file_size_mb=self.max_file_size_mb,
                max_concurrent_downloads=self.max_concurrent_downloads
            )
            logger.info("✅ Downloader multiusuario inicializado")
            
            # Crear aplicación
            self.application = Application.builder().token(self.token).build()
            self._setup_handlers()
            logger.info("✅ Aplicación de Telegram configurada")
            
            # Estadísticas
            self.stats = {
                'downloads_completed': 0,
                'downloads_failed': 0,
                'playlists_completed': 0,
                'playlists_failed': 0,
                'total_files_sent': 0,
                'start_time': time.time(),
                'total_users': set(),
                'commands_processed': 0
            }
            logger.info("✅ Sistema de estadísticas inicializado")
            
        except Exception as e:
            logger.critical(f"❌ Error crítico al inicializar bot: {str(e)}")
            logger.critical(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _setup_handlers(self):
        """Configura los manejadores de comandos"""
        handlers = [
            CommandHandler("start", self.start_command),
            CommandHandler("help", self.help_command),
            CommandHandler("download", self.download_command),
            CommandHandler("get", self.download_command),  # Alias
            CommandHandler("playlist", self.playlist_command),
            CommandHandler("stats", self.stats_command),
            CommandHandler("status", self.status_command),  # Nuevo comando
        ]
        
        for handler in handlers:
            self.application.add_handler(handler)
    
    async def _download_playlist_with_progress(self, url, user_id, status_message, escaped_user_name, playlist_title, playlist_count):
        """Descarga playlist con actualizaciones de progreso simples"""
        
        # Actualización inicial
        try:
            await status_message.edit_text(
                f"🎵 *Playlist:* _{self.escape_markdown(playlist_title)}_\n"
                f"👤 *Usuario:* {escaped_user_name}\n\n"
                f"📊 *Progreso:* Descargando videos\\.\\.\\.\n"
                f"{create_progress_bar(50)}\n\n"
                f"🎬 *Videos detectados:* {playlist_count}\n"
                f"⏳ Procesando playlist\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
        except Exception:
            pass  # Ignorar errores de edición
        
        # Realizar descarga
        result = await self.downloader.download_playlist(url, user_id)
        return result
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start con logging detallado"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Usuario"
        username = update.effective_user.username or "sin_username"
        
        try:
            logger.info(f"📱 Comando /start - Usuario: {user_name} (@{username}, ID: {user_id})")
            self.stats['commands_processed'] += 1
            self.stats['total_users'].add(user_id)
            
            welcome_text = f"""
🎵 **Bot de Descarga de Música de YouTube** 🎵

¡Hola! Soy un bot que puede descargar música de YouTube y convertirla a MP3.

**✨ Características:**
• 🎵 Descarga videos individuales (formato: artist - title)
• 📋 Descarga playlists completas (formato: artist - title)
• 👥 Soporte multiusuario (hasta {self.max_concurrent_downloads} descargas simultáneas)
• 🔄 Procesamiento en paralelo
• 🗑️ Limpieza automática de archivos

**Comandos disponibles:**
• `/download <URL>` - Descarga música de YouTube
• `/get <URL>` - Alias para download
• `/playlist <URL>` - Descarga playlist completa
• `/help` - Muestra ayuda detallada
• `/stats` - Estadísticas del bot
• `/status` - Estado actual del bot

**Limitaciones:**
• Máximo {self.max_file_size_mb}MB por archivo
• Máximo 30 minutos de duración (videos individuales)
• Solo URLs de YouTube válidas
• Una descarga por usuario a la vez

¡Envía un comando con una URL para empezar! 🚀
            """
            
            await update.message.reply_text(welcome_text, parse_mode='Markdown')
            logger.info(f"✅ Mensaje de bienvenida enviado a usuario {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error en start_command para usuario {user_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                await update.message.reply_text("❌ Error interno. Inténtalo más tarde.")
            except:
                logger.error(f"❌ No se pudo enviar mensaje de error a usuario {user_id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_text = """
📖 **Ayuda del Bot**

**Comandos:**
• `/start` - Mensaje de bienvenida
• `/download <URL>` - Descarga música de YouTube
• `/get <URL>` - Alias para download
• `/playlist <URL>` - Descarga playlist completa
• `/help` - Muestra esta ayuda
• `/stats` - Estadísticas del bot
• `/status` - Estado actual y descargas activas

**Formato correcto:**
`/download https://www.youtube.com/watch?v=VIDEO_ID`
`/get https://youtu.be/VIDEO_ID`
`/playlist https://www.youtube.com/playlist?list=PLAYLIST_ID`

**Ejemplos de URLs válidas:**
• `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
• `https://youtu.be/dQw4w9WgXcQ`
• `https://www.youtube.com/playlist?list=PLxxx...`
• `https://www.youtube.com/watch?v=xxx&list=PLxxx...`

**Características multiusuario:**
• ✅ Hasta {self.max_concurrent_downloads} usuarios pueden descargar simultáneamente
• ✅ Cada usuario tiene su propio directorio temporal
• ✅ Una descarga por usuario a la vez (evita saturación)
• ✅ Limpieza automática de archivos después del envío

**Limitaciones:**
• Máximo {self.max_file_size_mb}MB por archivo
• Videos individuales: máximo 30 minutos
• Solo URLs de YouTube válidas
• Archivos con formato: "artist - title.mp3"

**Tips:**
• Si ya tienes una descarga en progreso, espera a que termine
• Las playlists grandes pueden tardar varios minutos
• Usa `/status` para ver el estado actual del bot
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def download_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /download y /get para videos individuales con logging completo"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Usuario"
        username = update.effective_user.username or "sin_username"
        
        # Logging inicial
        download_logger.info(f"🎵 Descarga iniciada - Usuario: {user_name} (@{username}, ID: {user_id})")
        
        try:
            self.stats['commands_processed'] += 1
            self.stats['total_users'].add(user_id)
            
            # Verificar argumentos
            if not context.args:
                logger.warning(f"⚠️ Usuario {user_id} envió comando sin URL")
                await update.message.reply_text(
                    "❌ *Error*: Debes proporcionar una URL\\.\n\n"
                    "*Uso correcto:*\n"
                    "`/download https://www\\.youtube\\.com/watch\\?v=VIDEO\\_ID`\n"
                    "`/get https://youtu\\.be/VIDEO\\_ID`",
                    parse_mode='MarkdownV2'
                )
                return
            
            url = context.args[0]
            download_logger.info(f"📺 URL recibida: {url} (Usuario: {user_id})")
            
            # Verificar si es URL de YouTube
            if not self.downloader.is_youtube_url(url):
                logger.warning(f"⚠️ URL inválida de usuario {user_id}: {url}")
                await update.message.reply_text(
                    "❌ *Error*: La URL debe ser de YouTube\\.\n\n"
                    "*URLs válidas:*\n"
                    "• `https://www\\.youtube\\.com/watch\\?v=VIDEO\\_ID`\n"
                    "• `https://youtu\\.be/VIDEO\\_ID`",
                    parse_mode='MarkdownV2'
                )
                return
            
            # Verificar si el usuario ya tiene una descarga activa
            if self.downloader.is_user_downloading(user_id):
                logger.info(f"⏳ Usuario {user_id} ya tiene descarga activa")
                escaped_user_name = escape_markdown(user_name)
                await update.message.reply_text(
                    f"⏳ {escaped_user_name}, ya tienes una descarga en progreso\\.\n"
                    "Espera a que termine antes de empezar otra\\.\n\n"
                    "Usa `/status` para ver el estado actual\\.",
                    parse_mode='MarkdownV2'
                )
                return
            
            # Verificar límite de descargas concurrentes
            active_downloads = self.downloader.get_active_downloads_count()
            if active_downloads >= self.max_concurrent_downloads:
                logger.warning(f"🚦 Límite alcanzado: {active_downloads}/{self.max_concurrent_downloads} - Usuario {user_id} rechazado")
                await update.message.reply_text(
                    f"🚦 *Bot ocupado*: Hay {self.max_concurrent_downloads} descargas activas\\.\n"
                    "Intenta de nuevo en unos momentos\\.\n\n"
                    "Usa `/status` para ver el estado actual\\.",
                    parse_mode='MarkdownV2'
                )
                return
            
            download_logger.info(f"✅ Descarga autorizada para usuario {user_id} - Descargas activas: {active_downloads}/{self.max_concurrent_downloads}")
            
            # Enviar indicador de que el bot está trabajando
            await update.message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
            
            # Mensaje de inicio
            escaped_url = escape_markdown(url)
            escaped_user_name = escape_markdown(user_name)
            
            status_message = await update.message.reply_text(
                f"🔄 *Iniciando descarga\\.\\.\\.*\n"
                f"👤 Usuario: {escaped_user_name}\n"
                f"📺 URL: `{escaped_url}`\n"
                f"⏱️ Esto puede tardar unos momentos\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # Verificar si es playlist
            download_logger.info(f"🔍 Verificando tipo de URL: {url} (Usuario: {user_id})")
            info = await self.downloader.check_if_playlist(url)
            
            if info.get('is_playlist'):
                logger.info(f"📋 URL de playlist detectada por usuario {user_id}: {url}")
                escaped_url = escape_markdown(url)
                escaped_user_name = escape_markdown(user_name)
                
                await status_message.edit_text(
                    f"⚠️ *URL de playlist detectada*\n"
                    f"👤 Usuario: {escaped_user_name}\n\n"
                    f"Esta URL parece ser de una playlist\\.\n"
                    f"Usa `/playlist {escaped_url}` para descargar la playlist completa\\.\n\n"
                    f"Si solo quieres un video específico, usa la URL directa del video\\.",
                    parse_mode='MarkdownV2'
                )
                return
            
            # Continuar con descarga individual
            video_title = info.get('title', 'Obteniendo información...')
            download_logger.info(f"🎵 Video detectado: '{video_title}' (Usuario: {user_id})")
            
            # ... resto del código de descarga con logs
            # [El resto del método se mantiene igual pero con más logs]
            
            # Descargar video individual con barra de progreso
            video_title_escaped = escape_markdown(video_title)
            escaped_user_name = escape_markdown(user_name)
            
            # Progreso 1: Analizando
            await status_message.edit_text(
                f"🔍 *Analizando video\\.\\.\\.*\n"
                f"👤 Usuario: {escaped_user_name}\n"
                f"🎵 Video: {video_title_escaped}\n\n"
                f"{create_progress_bar(10)}\n"
                f"📊 Estado: Obteniendo información\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            await asyncio.sleep(0.5)
            
            # Progreso 2: Iniciando descarga
            await status_message.edit_text(
                f"⬇️ *Iniciando descarga\\.\\.\\.*\n"
                f"👤 Usuario: {escaped_user_name}\n"
                f"🎵 Video: {video_title_escaped}\n\n"
                f"{create_progress_bar(25)}\n"
                f"📊 Estado: Conectando a YouTube\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            await asyncio.sleep(0.5)
            
            # Progreso 3: Descargando audio
            await status_message.edit_text(
                f"🎧 *Descargando audio\\.\\.\\.*\n"
                f"👤 Usuario: {escaped_user_name}\n"
                f"🎵 Video: {video_title_escaped}\n\n"
                f"{create_progress_bar(50)}\n"
                f"📊 Estado: Extrayendo audio\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # Ejecutar descarga real
            download_start = time.time()
            download_logger.info(f"⬇️ Iniciando descarga real de: {url} (Usuario: {user_id})")
            result_file = await self.downloader.download_audio(url, user_id)
            download_time = time.time() - download_start
            
            if result_file and os.path.exists(result_file):
                download_logger.info(f"✅ Descarga exitosa en {download_time:.1f}s: {Path(result_file).name} (Usuario: {user_id})")
                
                # Progreso 4: Procesando
                await status_message.edit_text(
                    f"🔄 *Procesando archivo\\.\\.\\.*\n"
                    f"👤 Usuario: {escaped_user_name}\n"
                    f"🎵 Video: {video_title_escaped}\n\n"
                    f"{create_progress_bar(75)}\n"
                    f"📊 Estado: Convirtiendo a MP3\\.\\.\\.",
                    parse_mode='MarkdownV2'
                )
                
                await asyncio.sleep(0.5)
                
                # Progreso 5: Enviando
                filename = escape_markdown(Path(result_file).name)
                
                await status_message.edit_text(
                    f"📤 *Enviando archivo\\.\\.\\.*\n"
                    f"👤 Usuario: {escaped_user_name}\n"
                    f"🎵 Video: {video_title_escaped}\n\n"
                    f"{create_progress_bar(90)}\n"
                    f"📊 Estado: Preparando envío\\.\\.\\.",
                    parse_mode='MarkdownV2'
                )
                
                # Enviar archivo
                file_size = os.path.getsize(result_file) / (1024*1024)  # MB
                download_logger.info(f"📤 Enviando archivo: {Path(result_file).name} ({file_size:.1f}MB) a usuario {user_id}")
                
                try:
                    with open(result_file, 'rb') as audio_file:
                        await update.message.reply_audio(
                            audio=audio_file,
                            filename=Path(result_file).name,
                            title=info.get('title', 'Audio de YouTube'),
                            performer=info.get('uploader', 'YouTube')
                        )
                    
                    download_logger.info(f"✅ Archivo enviado exitosamente a usuario {user_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Error enviando archivo a usuario {user_id}: {str(e)}")
                    raise
                
                # Limpiar archivo
                self.downloader.cleanup_user_files([result_file], user_id)
                download_logger.info(f"🗑️ Archivo limpiado: {Path(result_file).name} (Usuario: {user_id})")
                
                # Actualizar estadísticas
                self.stats['downloads_completed'] += 1
                self.stats['total_files_sent'] += 1
                
                # Progreso 6: Completado
                await status_message.edit_text(
                    f"✅ *¡Descarga completada\\!*\n"
                    f"👤 Usuario: {escaped_user_name}\n"
                    f"🎵 Video: {video_title_escaped}\n\n"
                    f"{create_progress_bar(100)}\n"
                    f"🎉 ¡Disfruta tu música\\!",
                    parse_mode='MarkdownV2'
                )
                
                download_logger.info(f"🎉 Descarga completada exitosamente para usuario {user_id} en {download_time:.1f}s")
                
            else:
                # Error en descarga
                self.stats['downloads_failed'] += 1
                download_logger.error(f"❌ Descarga falló para usuario {user_id}: No se pudo obtener el archivo")
                
                escaped_user_name = escape_markdown(user_name)
                
                await status_message.edit_text(
                    f"❌ *Error en la descarga*\n"
                    f"👤 Usuario: {escaped_user_name}\n\n"
                    f"Posibles causas:\n"
                    f"• Video privado o eliminado\n"
                    f"• Video muy largo \\(\\>30 min\\)\n"
                    f"• Archivo muy grande \\(\\>{self.max_file_size_mb}MB\\)\n"
                    f"• Error temporal\n\n"
                    f"Intenta con otro video o inténtalo más tarde\\.",
                    parse_mode='MarkdownV2'
                )
                
        except Exception as e:
            self.stats['downloads_failed'] += 1
            logger.error(f"❌ Error inesperado en download_command para usuario {user_id}: {str(e)}")
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            download_logger.error(f"❌ Error inesperado descargando {url} para usuario {user_id}: {str(e)}")
            
            try:
                error_text = escape_markdown(str(e)[:200])
                escaped_user_name = escape_markdown(user_name)
                
                await status_message.edit_text(
                    f"❌ *Error inesperado*\n"
                    f"👤 Usuario: {escaped_user_name}\n"
                    f"🐛 Error: {error_text}\n\n"
                    f"Inténtalo de nuevo más tarde\\.",
                    parse_mode='MarkdownV2'
                )
            except Exception as msg_error:
                logger.error(f"❌ No se pudo enviar mensaje de error a usuario {user_id}: {str(msg_error)}")
    
    async def playlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /playlist para playlists completas"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Usuario"
        
        # Verificar argumentos
        if not context.args:
            await update.message.reply_text(
                "❌ **Error**: Debes proporcionar una URL de playlist.\n\n"
                "**Uso correcto:**\n"
                "`/playlist https://www.youtube.com/playlist?list=PLAYLIST_ID`\n"
                "`/playlist https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID`",
                parse_mode='Markdown'
            )
            return
        
        url = context.args[0]
        
        # Verificar si es URL de YouTube
        if not self.downloader.is_youtube_url(url):
            await update.message.reply_text(
                "❌ **Error**: La URL debe ser de YouTube.\n\n"
                "**URLs válidas:**\n"
                "• `https://www.youtube.com/playlist?list=PLAYLIST_ID`\n"
                "• `https://www.youtube.com/watch?v=VIDEO_ID&list=PLAYLIST_ID`",
                parse_mode='Markdown'
            )
            return
        
        # Verificar si el usuario ya tiene una descarga activa
        if self.downloader.is_user_downloading(user_id):
            await update.message.reply_text(
                f"⏳ {user_name}, ya tienes una descarga en progreso.\n"
                "Espera a que termine antes de empezar otra.\n\n"
                "Usa `/status` para ver el estado actual.",
                parse_mode='Markdown'
            )
            return
        
        # Verificar límite de descargas concurrentes
        if self.downloader.get_active_downloads_count() >= self.max_concurrent_downloads:
            await update.message.reply_text(
                f"🚦 **Bot ocupado**: Hay {self.max_concurrent_downloads} descargas activas.\n"
                "Intenta de nuevo en unos momentos.\n\n"
                "Usa `/status` para ver el estado actual.",
                parse_mode='Markdown'
            )
            return
        
        logger.info(f"Usuario {user_id} ({user_name}) iniciando playlist: {url}")
        
        # Enviar indicador de que el bot está trabajando
        await update.message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
        
        # Mensaje de inicio
        escaped_url = escape_markdown(url)
        escaped_user_name = escape_markdown(user_name)
        
        status_message = await update.message.reply_text(
            f"� *Analizando playlist\\.\\.\\.*\n"
            f"👤 Usuario: {escaped_user_name}\n"
            f"📺 URL: `{escaped_url}`\n\n"
            f"{create_progress_bar(5)}\n"
            f"📊 Estado: Conectando con YouTube\\.\\.\\.\n"
            f"⏱️ Esto puede tardar varios minutos\\.\\.\\.",
            parse_mode='MarkdownV2'
        )
        
        try:
            # Progreso: Verificando información de playlist
            await status_message.edit_text(
                f"🔍 *Verificando playlist\\.\\.\\.*\n"
                f"👤 Usuario: {escaped_user_name}\n"
                f"📺 URL: `{escaped_url}`\n\n"
                f"{create_progress_bar(10)}\n"
                f"📊 Estado: Obteniendo metadatos\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # Verificar información de playlist
            info = await self.downloader.check_if_playlist(url)
            
            if not info.get('is_playlist'):
                await status_message.edit_text(
                    f"⚠️ *No es una playlist*\n"
                    f"👤 Usuario: {escaped_user_name}\n\n"
                    f"Esta URL parece ser de un video individual\\.\n"
                    f"Usa `/download {escaped_url}` para descargar el video\\.\n\n"
                    f"Para playlists, asegúrate de que la URL contenga `list=`\\.",
                    parse_mode='MarkdownV2'
                )
                return
            
            playlist_title = escape_markdown(info.get('playlist_title', 'Playlist sin título'))
            playlist_count = info.get('playlist_count', 'Desconocido')
            
            # Progreso: Playlist detectada
            await status_message.edit_text(
                f"📋 *Playlist encontrada\\!*\n"
                f"👤 Usuario: {escaped_user_name}\n"
                f"📋 Título: {playlist_title}\n"
                f"📊 Videos: {playlist_count}\n\n"
                f"{create_progress_bar(20)}\n"
                f"🔄 Estado: Preparando descarga\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            await asyncio.sleep(1)  # Pausa para mostrar la información
            
            # Progreso: Iniciando descarga de playlist
            await status_message.edit_text(
                f"⬇️ *Descargando playlist\\.\\.\\.*\n"
                f"👤 Usuario: {escaped_user_name}\n"
                f"📋 Título: {playlist_title}\n"
                f"📊 Videos: {playlist_count}\n\n"
                f"{create_progress_bar(30)}\n"
                f"🎵 Estado: Procesando videos\\.\\.\\.",
                parse_mode='MarkdownV2'
            )
            
            # Ejecutar descarga con callback de progreso
            result = await self._download_playlist_with_progress(
                url, user_id, status_message, escaped_user_name, playlist_title, playlist_count
            )
            
            if result.get('success') and result.get('downloaded_files'):
                files = result['downloaded_files']
                downloaded_count = len(files)
                failed_count = result.get('failed_count', 0)
                total_count = result.get('total_count', downloaded_count + failed_count)
                
                # Limitar archivos a enviar (máximo 30 por defecto)
                max_files_to_send = 30
                files_to_send = files[:max_files_to_send]
                remaining_files = max(0, len(files) - max_files_to_send)
                
                await status_message.edit_text(
                    f"📤 **Enviando archivos...**\n"
                    f"👤 Usuario: {user_name}\n"
                    f"📋 Playlist: {playlist_title}\n"
                    f"✅ Descargados: {downloaded_count}/{total_count}\n"
                    f"📤 Enviando: {len(files_to_send)} archivos",
                    parse_mode='Markdown'
                )
                
                # Enviar archivos
                sent_files = 0
                for file_path in files_to_send:
                    try:
                        with open(file_path, 'rb') as audio_file:
                            await update.message.reply_audio(
                                audio=audio_file,
                                filename=Path(file_path).name,
                                title=Path(file_path).stem,  # Nombre sin extensión
                                performer="YouTube Playlist"
                            )
                        sent_files += 1
                        self.stats['total_files_sent'] += 1
                        
                        # Pequeña pausa para evitar límites de rate
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error enviando archivo {file_path}: {e}")
                
                # Limpiar archivos
                self.downloader.cleanup_user_files(files, user_id)
                
                # Mensaje final
                final_message = f"✅ **¡Playlist completada!**\n"
                final_message += f"👤 Usuario: {user_name}\n"
                final_message += f"📋 Playlist: {playlist_title}\n"
                final_message += f"📤 Enviados: {sent_files} archivos\n"
                
                if failed_count > 0:
                    final_message += f"⚠️ Fallaron: {failed_count} videos\n"
                
                if remaining_files > 0:
                    final_message += f"ℹ️ {remaining_files} archivos adicionales descargados pero no enviados (límite de {max_files_to_send})\n"
                
                final_message += f"🎉 ¡Disfruta tu música!"
                
                await status_message.edit_text(final_message, parse_mode='Markdown')
                
                # Actualizar estadísticas
                self.stats['playlists_completed'] += 1
                
                logger.info(f"Playlist exitosa para usuario {user_id}: {sent_files} archivos enviados")
                
            else:
                self.stats['playlists_failed'] += 1
                error_msg = result.get('error', 'Error desconocido')
                
                await status_message.edit_text(
                    f"❌ **Error en playlist**\n"
                    f"👤 Usuario: {user_name}\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Posibles causas:\n"
                    f"• Playlist privada o eliminada\n"
                    f"• Todos los videos fallaron\n"
                    f"• Problema temporal\n\n"
                    f"Intenta con otra playlist.",
                    parse_mode='Markdown'
                )
                
                logger.warning(f"Playlist falló para usuario {user_id}: {error_msg}")
        
        except Exception as e:
            self.stats['playlists_failed'] += 1
            await status_message.edit_text(
                f"❌ **Error inesperado**\n"
                f"👤 Usuario: {user_name}\n"
                f"🐛 Error: {str(e)}\n\n"
                f"Inténtalo de nuevo más tarde.",
                parse_mode='Markdown'
            )
            
            logger.error(f"Error inesperado en playlist para usuario {user_id}: {str(e)}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stats - Estadísticas del bot"""
        uptime_seconds = time.time() - self.stats['start_time']
        uptime_hours = uptime_seconds / 3600
        
        stats_text = f"""
📊 **Estadísticas del Bot**

**⏱️ Tiempo activo:** {uptime_hours:.1f} horas

**📥 Descargas individuales:**
• ✅ Exitosas: {self.stats['downloads_completed']}
• ❌ Fallidas: {self.stats['downloads_failed']}

**📋 Playlists:**
• ✅ Exitosas: {self.stats['playlists_completed']}
• ❌ Fallidas: {self.stats['playlists_failed']}

**📤 Total archivos enviados:** {self.stats['total_files_sent']}

**🔄 Estado actual:**
• Descargas activas: {self.downloader.get_active_downloads_count()}/{self.max_concurrent_downloads}
• Límite por archivo: {self.max_file_size_mb}MB
• Timeout: {self.download_timeout}s

**💻 Sistema:**
• Soporte multiusuario: ✅
• Formato archivos: artist - title.mp3
• Limpieza automática: ✅
        """
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status - Estado actual del bot"""
        user_id = update.effective_user.id
        active_count = self.downloader.get_active_downloads_count()
        user_downloading = self.downloader.is_user_downloading(user_id)
        
        status_text = f"🔄 **Estado del Bot**\n\n"
        
        if active_count == 0:
            status_text += "✅ **Bot disponible** - Sin descargas activas\n"
        else:
            status_text += f"⚡ **Bot ocupado** - {active_count}/{self.max_concurrent_downloads} descargas activas\n"
        
        if user_downloading:
            download_time = self.downloader.get_user_download_time(user_id)
            if download_time:
                elapsed = time.time() - download_time
                status_text += f"\n⏳ **Tu descarga:** En progreso ({elapsed:.0f}s transcurridos)\n"
            else:
                status_text += f"\n⏳ **Tu descarga:** En progreso\n"
        else:
            status_text += f"\n✅ **Tu estado:** Disponible para nueva descarga\n"
        
        status_text += f"\n**Límites:**\n"
        status_text += f"• Máximo {self.max_concurrent_downloads} descargas simultáneas\n"
        status_text += f"• Máximo {self.max_file_size_mb}MB por archivo\n"
        status_text += f"• Una descarga por usuario a la vez"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def _periodic_health_check(self):
        """Monitoreo periódico del estado del bot para logging"""
        while True:
            try:
                await asyncio.sleep(300)  # Cada 5 minutos
                
                uptime = time.time() - self.stats['start_time']
                active_downloads = self.downloader.get_active_downloads_count()
                total_users = len(self.stats['total_users'])
                
                # Log de estado cada 5 minutos
                logger.info(f"📊 Estado del bot - Uptime: {uptime/3600:.1f}h, "
                          f"Usuarios únicos: {total_users}, "
                          f"Descargas activas: {active_downloads}/{self.max_concurrent_downloads}, "
                          f"Comandos procesados: {self.stats['commands_processed']}")
                
                # Log detallado cada hora
                if int(uptime) % 3600 < 300:  # Si han pasado múltiplos de 1 hora (±5min)
                    logger.info(f"🕐 Reporte horario:")
                    logger.info(f"   ✅ Descargas exitosas: {self.stats['downloads_completed']}")
                    logger.info(f"   ❌ Descargas fallidas: {self.stats['downloads_failed']}")
                    logger.info(f"   📋 Playlists exitosas: {self.stats['playlists_completed']}")
                    logger.info(f"   📤 Total archivos enviados: {self.stats['total_files_sent']}")
                    
                # Log diario con estadísticas completas
                if int(uptime) % 86400 < 300:  # Si han pasado múltiplos de 24 horas (±5min)
                    logger.info(f"📅 REPORTE DIARIO - Bot funcionando {uptime/86400:.1f} días")
                    logger.info(f"   👥 Usuarios únicos: {total_users}")
                    logger.info(f"   📊 Total comandos: {self.stats['commands_processed']}")
                    logger.info(f"   ✅ Tasa de éxito: {(self.stats['downloads_completed']/(self.stats['downloads_completed']+self.stats['downloads_failed']+0.01)*100):.1f}%")
                    
            except Exception as e:
                logger.error(f"❌ Error en health check: {str(e)}")
                await asyncio.sleep(60)  # Esperar 1 minuto si hay error
    
    async def run(self):
        """Ejecuta el bot con monitoreo completo"""
        try:
            # Configurar comandos del bot
            commands = [
                BotCommand("start", "Mensaje de bienvenida"),
                BotCommand("help", "Mostrar ayuda"),
                BotCommand("download", "Descargar video individual"),
                BotCommand("playlist", "Descargar playlist completa"),
                BotCommand("stats", "Estadísticas del bot"),
                BotCommand("status", "Estado actual del bot"),
            ]
            await self.application.bot.set_my_commands(commands)
            logger.info("✅ Comandos del bot configurados")
            
            # Iniciar monitoreo en segundo plano
            asyncio.create_task(self._periodic_health_check())
            logger.info("✅ Sistema de monitoreo iniciado")
            
            # Logging de inicio
            logger.info("🚀 Bot multiusuario iniciado y funcionando")
            logger.info(f"📊 Configuración activa:")
            logger.info(f"   - Descargas simultáneas: {self.max_concurrent_downloads}")
            logger.info(f"   - Tamaño máximo: {self.max_file_size_mb}MB")
            logger.info(f"   - Timeout: {self.download_timeout}s")
            logger.info(f"   - Directorio temporal: {self.temp_dir}")
            logger.info("💡 Bot listo para funcionar 24/7")
            
            # Iniciar el bot
            await self.application.run_polling()
            
        except Exception as e:
            logger.critical(f"❌ Error crítico ejecutando el bot: {str(e)}")
            logger.critical(f"Traceback: {traceback.format_exc()}")
            raise

def main():
    """Función principal con manejo de errores robusto"""
    print("🚀 Iniciando bot multiusuario...")
    print("⏹️ Presiona Ctrl+C para detener")
    
    bot = None
    try:
        logger.info("=" * 50)
        logger.info("🚀 INICIANDO BOT MULTIUSUARIO")
        logger.info("=" * 50)
        
        bot = MultiUserTelegramBot()
        
        # Configurar manejador de señales para cierre limpio
        import signal
        
        def signal_handler(signum, frame):
            logger.info(f"📴 Señal recibida ({signum}) - Iniciando cierre limpio...")
            if bot:
                # Limpiar archivos temporales
                try:
                    bot.downloader.cleanup_temp_dir()
                    logger.info("✅ Archivos temporales limpiados")
                except Exception as e:
                    logger.error(f"⚠️ Error limpiando archivos: {e}")
                
                # Log final
                uptime = time.time() - bot.stats['start_time']
                logger.info(f"📊 ESTADÍSTICAS FINALES:")
                logger.info(f"   - Tiempo activo: {uptime/3600:.1f} horas")
                logger.info(f"   - Usuarios únicos: {len(bot.stats['total_users'])}")
                logger.info(f"   - Comandos procesados: {bot.stats['commands_processed']}")
                logger.info(f"   - Descargas exitosas: {bot.stats['downloads_completed']}")
                logger.info(f"   - Archivos enviados: {bot.stats['total_files_sent']}")
            
            logger.info("👋 Bot detenido limpiamente")
            exit(0)
        
        # Registrar handlers para diferentes señales
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Terminación
        
        # Ejecutar bot
        asyncio.run(bot.run())
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot detenido por el usuario (Ctrl+C)")
        print("\n🛑 Bot detenido por el usuario")
        
    except Exception as e:
        logger.critical(f"❌ Error crítico en main: {str(e)}")
        logger.critical(f"Traceback completo: {traceback.format_exc()}")
        print(f"❌ Error crítico: {e}")
        
        # Intentar limpiar antes de salir
        if bot:
            try:
                bot.downloader.cleanup_temp_dir()
                logger.info("✅ Limpieza de emergencia completada")
            except:
                pass
        
        return 1  # Código de error para reinicio automático
    
    finally:
        logger.info("🔚 Proceso main finalizado")
    
    return 0  # Código de salida normal

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
