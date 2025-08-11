#!/usr/bin/env python3
"""
Test completo del bot con el nuevo formato
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader import YouTubeDownloader

async def test_both_formats():
    """Prueba tanto descarga individual como playlist con formato artist - title"""
    print("🎵 Probando formato artist - title en ambos modos")
    
    downloader = YouTubeDownloader()
    downloads_dir = Path("./downloads")
    
    print("\n=== PRUEBA 1: Video Individual ===")
    individual_url = "https://www.youtube.com/watch?v=EDRBluZnyys"
    print(f"📺 URL: {individual_url}")
    
    try:
        # Verificar si es playlist
        info = await downloader.check_if_playlist(individual_url)
        print(f"🔍 Es playlist: {info.get('is_playlist', False)}")
        
        # Descargar como individual
        result = await downloader.download_audio(individual_url)
        if result:
            filename = Path(result).name
            print(f"✅ Descargado: {filename}")
            if " - " in filename:
                print("   ✅ Formato artist - title correcto")
            
            # Limpiar
            downloader.cleanup_file(result)
            print("   🗑️ Archivo limpiado")
    except Exception as e:
        print(f"❌ Error en individual: {e}")
    
    print("\n=== PRUEBA 2: Playlist (limitada) ===")
    playlist_url = "https://www.youtube.com/watch?v=EDRBluZnyys&list=PLa7sBOYG7Txw0SdJCDwLFyPwkyphPRXkk"
    print(f"📺 URL: {playlist_url}")
    
    try:
        # Verificar si es playlist
        info = await downloader.check_if_playlist(playlist_url)
        print(f"🔍 Es playlist: {info.get('is_playlist', False)}")
        if info.get('is_playlist'):
            print(f"   📋 Título: {info.get('playlist_title', 'Sin título')}")
        
        # Limitar la playlist para la prueba
        original_opts = downloader.playlist_ydl_opts.copy()
        downloader.playlist_ydl_opts['playlistend'] = 2
        
        # Descargar como playlist
        result = await downloader.download_playlist(playlist_url)
        if result.get('success'):
            print(f"✅ Playlist descargada: {result.get('downloaded_count', 0)} archivos")
            for file_path in result.get('downloaded_files', []):
                filename = Path(file_path).name
                print(f"   📁 {filename}")
                if " - " in filename:
                    print("      ✅ Formato artist - title correcto")
            
            # Limpiar
            downloader.cleanup_files(result.get('downloaded_files', []))
            print("   🗑️ Archivos limpiados")
        
        # Restaurar configuración
        downloader.playlist_ydl_opts = original_opts
        
    except Exception as e:
        print(f"❌ Error en playlist: {e}")
    
    print("\n🎉 Pruebas completadas")

if __name__ == "__main__":
    asyncio.run(test_both_formats())
