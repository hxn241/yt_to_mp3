#!/usr/bin/env python3
"""
Test básico del sistema de logging del bot
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_logging():
    """Test del sistema de logging"""
    print("🧪 Probando sistema de logging...")
    
    try:
        # Importar y configurar logging
        from bot_multiuser import setup_logging, logger, download_logger
        
        print("✅ Logging configurado correctamente")
        
        # Test de logs básicos
        logger.info("🧪 Test de logging - Info message")
        logger.warning("⚠️ Test de logging - Warning message")
        logger.error("❌ Test de logging - Error message")
        
        download_logger.info("📥 Test de logging - Download info")
        
        print("✅ Mensajes de log enviados")
        print("📁 Revisa la carpeta 'logs/' para verificar los archivos")
        
        # Listar archivos de log creados
        logs_dir = "logs"
        if os.path.exists(logs_dir):
            log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
            if log_files:
                print(f"📋 Archivos de log encontrados: {', '.join(log_files)}")
            else:
                print("⚠️ No se encontraron archivos .log")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_logging()
    if success:
        print("🎉 Test de logging completado exitosamente")
        exit(0)
    else:
        print("💥 Test de logging falló")
        exit(1)
