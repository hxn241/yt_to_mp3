import os
import logging
from pathlib import Path
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ChatAction
from dotenv import load_dotenv
import asyncio

from downloader import YouTubeDownloader

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Bot de Telegram para descargar música de YouTube"""
    
    def __init__(self):
        # Cargar variables de entorno
        load_dotenv()
        
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN no encontrado en .env")
        
        # Configuración
        self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', 50))
        self.download_timeout = int(os.getenv('DOWNLOAD_TIMEOUT', 300))
        self.temp_dir = os.getenv('TEMP_DIR', './downloads')
        
        # Inicializar downloader
        self.downloader = YouTubeDownloader(
            temp_dir=self.temp_dir,
            max_file_size_mb=self.max_file_size_mb
        )
        
        # Crear aplicación
        self.application = Application.builder().token(self.token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configura los manejadores de comandos"""
        handlers = [
            CommandHandler("start", self.start_command),
            CommandHandler("help", self.help_command),
            CommandHandler("download", self.download_command),
            CommandHandler("get", self.download_command),  # Alias
            CommandHandler("playlist", self.playlist_command),
            CommandHandler("stats", self.stats_command),
        ]
        
        for handler in handlers:
            self.application.add_handler(handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        welcome_text = """
🎵 **Bot de Descarga de Música de YouTube** 🎵

¡Hola! Soy un bot que puede descargar música de YouTube y convertirla a MP3.

**Comandos disponibles:**
• `/download <URL>` - Descarga música de YouTube
• `/get <URL>` - Alias para download
• `/playlist <URL>` - Descarga playlist completa
• `/help` - Muestra esta ayuda
• `/stats` - Estadísticas del bot

**Ejemplo de uso:**
`/download https://www.youtube.com/watch?v=dQw4w9WgXcQ`

**Limitaciones:**
• Máximo {max_size}MB por archivo
• Máximo 30 minutos de duración
• Solo URLs de YouTube válidas

¡Envía un comando con una URL para empezar! 🚀
        """.format(max_size=self.max_file_size_mb)
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
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

**Formato correcto:**
`/download https://www.youtube.com/watch?v=VIDEO_ID`
`/get https://youtu.be/VIDEO_ID`

**Limitaciones:**
• Solo URLs de YouTube (youtube.com, youtu.be)
• Máximo {max_size}MB por archivo
• Máximo 30 minutos de duración
• Timeout de {timeout}s por descarga

**Tips:**
• Usa URLs completas para mejores resultados
• El proceso puede tomar unos minutos
• Los archivos se eliminan después del envío

¿Problemas? Verifica que la URL sea correcta y el video esté disponible.
        """.format(
            max_size=self.max_file_size_mb,
            timeout=self.download_timeout
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def download_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando principal para descargar música"""
        try:
            # Verificar argumentos
            if not context.args:
                await update.message.reply_text(
                    "❌ Por favor proporciona una URL de YouTube.\n\n"
                    "Ejemplo: `/download https://www.youtube.com/watch?v=VIDEO_ID`",
                    parse_mode='Markdown'
                )
                return
            
            url = ' '.join(context.args)
            
            # Verificar que sea URL de YouTube
            if not self.downloader.is_youtube_url(url):
                await update.message.reply_text(
                    "❌ La URL debe ser de YouTube (youtube.com o youtu.be)"
                )
                return
            
            # Mensaje de inicio
            status_msg = await update.message.reply_text(
                "🔄 **Procesando tu solicitud...**\n\n"
                f"📺 URL: `{url}`\n"
                "⏳ Descargando y convirtiendo a MP3...",
                parse_mode='Markdown'
            )
            
            # Mostrar acción de "subiendo archivo"
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.UPLOAD_DOCUMENT
            )
            
            # Descargar con timeout
            try:
                file_path = await asyncio.wait_for(
                    self.downloader.download_audio(url),
                    timeout=self.download_timeout
                )
            except asyncio.TimeoutError:
                await status_msg.edit_text(
                    "⏰ **Timeout**\n\n"
                    "La descarga tardó demasiado tiempo. "
                    "Intenta con un video más corto."
                )
                return
            
            if not file_path or not os.path.exists(file_path):
                await status_msg.edit_text(
                    "❌ **Error en la descarga**\n\n"
                    "No se pudo descargar el audio. Posibles causas:\n"
                    "• Video no disponible o privado\n"
                    "• Video demasiado largo (>30 min)\n"
                    "• Problemas de conectividad\n\n"
                    "Intenta con otro video."
                )
                return
            
            # Actualizar estado
            await status_msg.edit_text(
                "📤 **Enviando archivo...**\n\n"
                "El archivo está listo, enviándolo ahora..."
            )
            
            # Enviar archivo
            file_size_mb = os.path.getsize(file_path) / 1024 / 1024
            filename = os.path.basename(file_path)
            
            with open(file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id,
                    audio=audio_file,
                    filename=filename,
                    caption=f"🎵 **Descarga completada**\n\n"
                           f"📁 Archivo: `{filename}`\n"
                           f"📊 Tamaño: {file_size_mb:.1f}MB",
                    parse_mode='Markdown'
                )
            
            # Eliminar archivo temporal
            self.downloader.cleanup_file(file_path)
            
            # Eliminar mensaje de estado
            await status_msg.delete()
            
            logger.info(f"Descarga exitosa para {update.effective_user.username}: {url}")
            
        except Exception as e:
            logger.error(f"Error en download_command: {str(e)}")
            await update.message.reply_text(
                "❌ **Error interno**\n\n"
                "Ocurrió un error inesperado. "
                "Por favor intenta nuevamente en unos minutos."
            )
    
    async def playlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando para descargar playlists completas"""
        try:
            # Verificar argumentos
            if not context.args:
                await update.message.reply_text(
                    "❌ Por favor proporciona una URL de playlist de YouTube.\n\n"
                    "Ejemplo: `/playlist https://www.youtube.com/playlist?list=PLAYLIST_ID`",
                    parse_mode='Markdown'
                )
                return
            
            url = ' '.join(context.args)
            
            # Verificar que sea URL de YouTube
            if not self.downloader.is_youtube_url(url):
                await update.message.reply_text(
                    "❌ La URL debe ser de YouTube (youtube.com o youtu.be)"
                )
                return
            
            # Mensaje de verificación inicial
            status_msg = await update.message.reply_text(
                "🔄 **Verificando URL...**\n\n"
                f"📺 URL: `{url}`\n"
                "⏳ Obteniendo información...",
                parse_mode='Markdown'
            )
            
            # Verificar si es playlist
            try:
                url_info = await asyncio.wait_for(
                    self.downloader.check_if_playlist(url),
                    timeout=30
                )
            except asyncio.TimeoutError:
                await status_msg.edit_text(
                    "⏰ **Timeout**\n\n"
                    "No se pudo verificar la URL. Intenta nuevamente."
                )
                return
            
            if url_info.get("error"):
                await status_msg.edit_text(
                    "❌ **Error al verificar URL**\n\n"
                    f"Error: {url_info['error']}"
                )
                return
            
            if not url_info.get("is_playlist"):
                await status_msg.edit_text(
                    "❌ **No es una playlist**\n\n"
                    "La URL proporcionada no es una playlist.\n"
                    "Para videos únicos usa `/download` en su lugar.\n\n"
                    f"💡 Video detectado: {url_info.get('title', 'Sin título')}"
                )
                return
            
            # Confirmar descarga de playlist
            playlist_title = url_info.get('playlist_title', 'Sin título')
            playlist_count = url_info.get('playlist_count', 0)
            
            await status_msg.edit_text(
                f"📋 **Playlist detectada**\n\n"
                f"• **Título:** {playlist_title}\n"
                f"• **Videos:** {playlist_count}\n\n"
                f"⚠️ **Importante:**\n"
                f"• Se intentarán descargar TODOS los videos\n"
                f"• Videos con errores se saltarán automáticamente\n"
                f"• Archivos >50MB se omitirán\n"
                f"• Este proceso puede tardar varios minutos\n\n"
                f"🚀 **Iniciando descarga...**",
                parse_mode='Markdown'
            )
            
            # Mostrar acción de "subiendo archivo"
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.UPLOAD_DOCUMENT
            )
            
            # Descargar playlist
            try:
                result = await self.downloader.download_playlist(url)
            except Exception as e:
                await status_msg.edit_text(
                    "❌ **Error en la descarga**\n\n"
                    f"Error: {str(e)}"
                )
                return
            
            if not result.get("success"):
                await status_msg.edit_text(
                    "❌ **Descarga fallida**\n\n"
                    "No se pudo descargar ningún video de la playlist.\n"
                    "Posibles causas:\n"
                    "• Playlist privada o no disponible\n"
                    "• Todos los videos tienen restricciones\n"
                    "• Problemas de conectividad"
                )
                return
            
            downloaded_files = result.get("downloaded_files", [])
            failed_count = result.get("failed_count", 0)
            total_count = result.get("total_count", 0)
            
            # Actualizar estado con resultados
            await status_msg.edit_text(
                f"✅ **Descarga completada**\n\n"
                f"📊 **Resultados:**\n"
                f"• Descargados: {len(downloaded_files)}\n"
                f"• Fallidos: {failed_count}\n"
                f"• Total: {total_count}\n\n"
                f"📤 **Enviando archivos...**"
            )
            
            # Enviar archivos descargados
            sent_count = 0
            max_files_to_send = 30  # Límite para evitar spam
            
            for i, file_path in enumerate(downloaded_files):
                if sent_count >= max_files_to_send:
                    break
                    
                try:
                    if not os.path.exists(file_path):
                        continue
                    
                    file_size_mb = os.path.getsize(file_path) / 1024 / 1024
                    filename = os.path.basename(file_path)
                    
                    # Actualizar progreso cada 3 archivos
                    if i % 3 == 0:
                        await context.bot.send_chat_action(
                            chat_id=update.effective_chat.id,
                            action=ChatAction.UPLOAD_DOCUMENT
                        )
                    
                    with open(file_path, 'rb') as audio_file:
                        await context.bot.send_audio(
                            chat_id=update.effective_chat.id,
                            audio=audio_file,
                            filename=filename,
                            caption=f"🎵 {i+1}/{min(len(downloaded_files), max_files_to_send)} - {filename[:50]}{'...' if len(filename) > 50 else ''}"
                        )
                    
                    sent_count += 1
                    
                    # Pequeña pausa para evitar rate limits
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error enviando archivo {file_path}: {e}")
                    continue
            
            # Limpiar archivos
            self.downloader.cleanup_files(downloaded_files)
            
            # Mensaje final
            final_message = f"🎉 **Playlist procesada**\n\n"
            
            if sent_count > 0:
                final_message += f"✅ **Enviados:** {sent_count} archivos\n"
                
            if len(downloaded_files) > max_files_to_send:
                final_message += f"⚠️ **Límite alcanzado:** Solo se enviaron los primeros {max_files_to_send} archivos\n"
                final_message += f"📥 **Disponibles:** {len(downloaded_files) - max_files_to_send} archivos adicionales se omitieron\n"
            
            if failed_count > 0:
                final_message += f"❌ **Fallidos:** {failed_count} videos no se pudieron descargar\n"
            
            final_message += f"\n📊 **Total procesado:** {total_count} videos"
            
            await status_msg.edit_text(final_message)
            
            logger.info(f"Playlist procesada para {update.effective_user.username}: {url} - {sent_count} enviados de {len(downloaded_files)} descargados")
            
        except Exception as e:
            logger.error(f"Error en playlist_command: {str(e)}")
            await update.message.reply_text(
                "❌ **Error interno**\n\n"
                "Ocurrió un error inesperado procesando la playlist. "
                "Por favor intenta nuevamente en unos minutos."
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando de estadísticas básicas"""
        stats_text = f"""
📊 **Estadísticas del Bot**

**Configuración:**
• Tamaño máximo: {self.max_file_size_mb}MB
• Timeout: {self.download_timeout}s
• Directorio temporal: `{self.temp_dir}`

**Estado:**
• ✅ Bot activo y funcionando
• 🤖 Versión: 1.0.0

**Soporte:**
• YouTube URLs (youtube.com, youtu.be)
• Formato de salida: MP3 (192kbps)
• Duración máxima: 30 minutos
        """
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    
    async def setup_bot_commands(self):
        """Configura los comandos del bot en el menú de Telegram"""
        commands = [
            BotCommand("start", "Iniciar el bot"),
            BotCommand("download", "Descargar música de YouTube"),
            BotCommand("get", "Alias para download"),
            BotCommand("playlist", "Descargar playlist completa"),
            BotCommand("help", "Mostrar ayuda"),
            BotCommand("stats", "Estadísticas del bot"),
        ]
        
        await self.application.bot.set_my_commands(commands)
        logger.info("Comandos del bot configurados")
    
    async def run(self):
        """Ejecuta el bot"""
        try:
            logger.info("Iniciando bot de Telegram...")
            
            # Configurar comandos
            await self.setup_bot_commands()
            
            logger.info("Bot iniciado correctamente. Presiona Ctrl+C para detener.")
            
            # Usar run_polling que es más simple y estable
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Error ejecutando el bot: {str(e)}")
            raise
        finally:
            # Limpiar recursos
            self.downloader.cleanup_temp_dir()

async def main():
    """Función principal"""
    try:
        bot = TelegramBot()
        await bot.setup_bot_commands()  # Configurar comandos
        bot.application.run_polling()   # Ejecutar bot
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        raise

if __name__ == '__main__':
    # No usar asyncio para run_polling
    try:
        bot = TelegramBot()
        bot.application.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
