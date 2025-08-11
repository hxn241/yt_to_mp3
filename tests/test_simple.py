#!/usr/bin/env python3
"""
Script de prueba simple para verificar que la conexión con Telegram funciona
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configurar logging para ver qué está pasando
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Función principal del bot"""
    print("🧪 Bot de Prueba Simple")
    print("=" * 30)
    
    # Cargar variables de entorno
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token or token == 'tu_token_real_aqui':
        print("❌ ERROR: Token no configurado en .env")
        return
    
    print(f"✅ Token cargado: {token[:10]}...")
    
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        user = update.effective_user
        logger.info(f"Usuario {user.username} ejecutó /start")
        
        await update.message.reply_text(
            f"¡Hola {user.first_name}! 👋\n\n"
            "🧪 **Bot de Prueba Funcionando**\n\n"
            "✅ Conexión con Telegram: OK\n"
            "✅ Token válido: OK\n"
            "✅ Comandos funcionando: OK\n\n"
            "🎯 Usa /test para otra prueba\n"
            "🎵 El bot está listo para descargar MP3!"
        )
    
    async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /test"""
        user = update.effective_user
        logger.info(f"Usuario {user.username} ejecutó /test")
        
        await update.message.reply_text(
            "🎯 **Test Completado**\n\n"
            f"👤 Usuario: {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📱 Chat: {update.effective_chat.id}\n\n"
            "✅ Todo funciona correctamente!\n"
            "🚀 Bot listo para usar!"
        )
    
    # Crear aplicación
    application = Application.builder().token(token).build()
    
    # Añadir manejadores
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("test", test_command))
    
    # Ejecutar bot
    try:
        print("🚀 Iniciando bot...")
        print("📱 Ve a Telegram y busca tu bot")
        print("💬 Envía /start para probar")
        print("⏹️  Presiona Ctrl+C para detener")
        print()
        
        # Ejecutar bot con polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except KeyboardInterrupt:
        print("\n👋 Bot detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Error ejecutando bot: {e}")

if __name__ == '__main__':
    main()
