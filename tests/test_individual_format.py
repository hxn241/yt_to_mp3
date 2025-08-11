#!/usr/bin/env python3
"""
Test de descarga individual para verificar el formato artist - title
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader import YouTubeDownloader

async def test_individual_format():
    """Prueba el formato de descarga artist - title para video individual"""
    print("🎵 Probando formato de descarga individual: artist - title")
    
    downloader = YouTubeDownloader()
    
    # URL de un video individual conocido
    test_url = "https://www.youtube.com/watch?v=EDRBluZnyys"
    
    print(f"📺 Probando con: {test_url}")
    print("⚠️  Solo se descargará un archivo para prueba...\n")
    
    try:
        print("🔄 Iniciando descarga de prueba...")
        
        # Obtener archivos antes
        downloads_dir = Path("./downloads")
        files_before = set(downloads_dir.glob("*.mp3")) if downloads_dir.exists() else set()
        
        # Descargar el video individual
        result_file = await downloader.download_audio(test_url)
        
        if result_file and os.path.exists(result_file):
            filename = Path(result_file).name
            print(f"\n✅ Se descargó el archivo:")
            print(f"   📁 {filename}")
            
            # Verificar formato
            if " - " in filename:
                print(f"      ✅ Formato correcto: artist - title")
            else:
                print(f"      ⚠️  Formato no esperado (puede ser que el video no tenga artist)")
            
            # Limpiar archivo de prueba
            print(f"\n🗑️ Limpiando archivo de prueba...")
            try:
                os.remove(result_file)
                print(f"   Eliminado: {filename}")
            except:
                pass
                
        else:
            print("❌ No se descargó el archivo")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")

if __name__ == "__main__":
    asyncio.run(test_individual_format())
