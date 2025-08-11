#!/usr/bin/env python3
"""
Test de descarga para verificar el formato artist - title
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader import YouTubeDownloader

async def test_download_format():
    """Prueba el formato de descarga artist - title"""
    print("🎵 Probando formato de descarga: artist - title")
    
    downloader = YouTubeDownloader()
    
    # URL de una playlist conocida (usamos una pequeña)
    test_url = "https://www.youtube.com/watch?v=EDRBluZnyys&list=PLa7sBOYG7Txw0SdJCDwLFyPwkyphPRXkk"
    
    print(f"📺 Probando con: {test_url}")
    print("⚠️  Solo se descargarán algunos archivos para prueba...\n")
    
    # Crear configuración de prueba que limite la descarga
    test_opts = downloader.playlist_ydl_opts.copy()
    test_opts['playlistend'] = 2  # Solo los primeros 2 videos
    
    try:
        print("🔄 Iniciando descarga de prueba...")
        
        # Obtener archivos antes
        downloads_dir = Path("./downloads")
        files_before = set(downloads_dir.glob("*.mp3")) if downloads_dir.exists() else set()
        
        # Usar método síncrono directamente para control más específico
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, test_download_sync, test_url, test_opts)
        
        # Obtener archivos después
        files_after = set(downloads_dir.glob("*.mp3")) if downloads_dir.exists() else set()
        new_files = files_after - files_before
        
        if new_files:
            print(f"\n✅ Se descargaron {len(new_files)} archivos:")
            for file_path in sorted(new_files):
                filename = file_path.name
                print(f"   📁 {filename}")
                
                # Verificar formato
                if " - " in filename:
                    print(f"      ✅ Formato correcto: artist - title")
                else:
                    print(f"      ⚠️  Formato no esperado")
            
            # Limpiar archivos de prueba
            print(f"\n🗑️ Limpiando archivos de prueba...")
            for file_path in new_files:
                try:
                    os.remove(file_path)
                    print(f"   Eliminado: {file_path.name}")
                except:
                    pass
                    
        else:
            print("❌ No se descargaron archivos")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")

def test_download_sync(url, opts):
    """Descarga síncrona para prueba"""
    import yt_dlp
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Error en descarga: {e}")

if __name__ == "__main__":
    asyncio.run(test_download_format())
