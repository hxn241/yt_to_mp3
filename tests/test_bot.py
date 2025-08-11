#!/usr/bin/env python3
"""
Script de prueba del bot (sin conversión a MP3)
Solo para verificar que la conexión con Telegram funciona
"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

class TestBot:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token or self.token == 'tu_token_real_aqui':
            raise ValueError("Configura TELEGRAM_BOT_TOKEN en .env")
        
        self.application = Application.builder().token(self.token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        handlers = [
            CommandHandler("start", self.start_command),
            CommandHandler("test", self.test_command),
        ]
        for handler in handlers:
            self.application.add_handler(handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🧪 **Bot de Prueba Activo**\n\n"
            "✅ La conexión con Telegram funciona correctamente\n"
            "🔧 Instala FFmpeg para funcionalidad completa\n\n"
            "Usa /test para una prueba básica",
            parse_mode='Markdown'
        )
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎯 **Test Exitoso**\n\n"
            "✅ Bot funcionando\n"
            "✅ Token válido\n"
            "✅ Conexión estable\n\n"
            "🚀 Listo para descargar MP3 (cuando instales FFmpeg)"
        )
    
    async def run(self):
        try:
            print("🧪 Iniciando bot de prueba...")
            print("📱 Busca tu bot en Telegram y envía /start")
            print("⏹️  Presiona Ctrl+C para detener\n")
            
            # Usar el método más simple y compatible
            self.application.run_polling()
            
        except KeyboardInterrupt:
            print("\n👋 Bot detenido por el usuario")
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    try:
        bot = TestBot()
        await bot.run()
    except KeyboardInterrupt:
        print("\n� Bot detenido")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    # Para el método run_polling, no necesitamos asyncio
    try:
        bot = TestBot()
        bot.application.run_polling()
    except KeyboardInterrupt:
        print("\n👋 Bot detenido")
    except Exception as e:
        print(f"❌ Error: {e}")
