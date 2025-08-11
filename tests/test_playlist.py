#!/usr/bin/env python3
"""
Script de prueba para la funcionalidad de playlist del YouTubeDownloader
"""
import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader import YouTubeDownloader

async def test_playlist_detection():
    """Prueba la detección de playlists"""
    print("🔍 Probando detección de playlists...")
    
    downloader = YouTubeDownloader()
    
    # URLs de prueba
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Video único
        "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy5L_X5Vr0eYKNlGZhM5U4D",  # Playlist (ejemplo)
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmRdnEQy5L_X5Vr0eYKNlGZhM5U4D",  # Video en playlist
    ]
    
    for url in test_urls:
        print(f"\n📺 Verificando: {url}")
        try:
            info = await downloader.check_if_playlist(url)
            print(f"   ✅ Es playlist: {info.get('is_playlist', False)}")
            print(f"   📋 Título: {info.get('title', 'N/A')}")
            if info.get('is_playlist'):
                print(f"   🎵 Videos: {info.get('playlist_count', 'N/A')}")
            else:
                print(f"   ⏱️ Duración: {info.get('duration', 'N/A')}s")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def test_single_download():
    """Prueba descarga de video único"""
    print("\n🎵 Probando descarga de video único...")
    
    downloader = YouTubeDownloader()
    
    # URL de video corto para prueba
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        print(f"   📥 Descargando: {test_url}")
        file_path = await downloader.download_audio(test_url)
        
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024 / 1024
            print(f"   ✅ Descargado: {os.path.basename(file_path)}")
            print(f"   📊 Tamaño: {file_size:.1f}MB")
            
            # Limpiar archivo de prueba
            downloader.cleanup_file(file_path)
            print(f"   🗑️ Archivo de prueba eliminado")
        else:
            print(f"   ❌ No se pudo descargar")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def main():
    """Función principal de prueba"""
    print("🚀 Iniciando pruebas del YouTubeDownloader")
    print("=" * 50)
    
    # Verificar que existe el directorio de downloads
    downloads_dir = Path("./downloads")
    if not downloads_dir.exists():
        downloads_dir.mkdir()
        print("📁 Directorio downloads creado")
    
    # Ejecutar pruebas
    await test_playlist_detection()
    await test_single_download()
    
    print("\n" + "=" * 50)
    print("✅ Pruebas completadas")

if __name__ == "__main__":
    asyncio.run(main())
