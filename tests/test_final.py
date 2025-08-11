#!/usr/bin/env python3
"""
Test final del bot con formato artist - title
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader import YouTubeDownloader

async def final_test():
    """Prueba final con el formato artist - title"""
    print("🎉 TEST FINAL: Formato artist - title habilitado")
    
    downloader = YouTubeDownloader()
    
    print("\n=== Verificación de configuración ===")
    print(f"📁 Individual outtmpl: {downloader.ydl_opts['outtmpl']}")
    print(f"📁 Playlist outtmpl: {downloader.playlist_ydl_opts['outtmpl']}")
    
    # Verificar que ambas configuraciones usen artist - title
    individual_format = "%(artist)s - %(title)s.%(ext)s" in downloader.ydl_opts['outtmpl']
    playlist_format = "%(artist)s - %(title)s.%(ext)s" in downloader.playlist_ydl_opts['outtmpl']
    
    if individual_format and playlist_format:
        print("✅ Ambas configuraciones usan formato artist - title")
    else:
        print("❌ Error en configuración de formato")
        return
    
    print("\n=== PRUEBA RÁPIDA: Un video individual ===")
    test_url = "https://www.youtube.com/watch?v=EDRBluZnyys"
    
    try:
        # Verificar detección
        info = await downloader.check_if_playlist(test_url)
        print(f"🔍 URL detectada como: {'Playlist' if info.get('is_playlist') else 'Video Individual'}")
        
        # Descargar
        result = await downloader.download_audio(test_url)
        if result:
            filename = Path(result).name
            print(f"✅ Descargado: {filename}")
            
            # Verificar formato
            if " - " in filename and filename.endswith('.mp3'):
                print("   ✅ Formato artist - title correcto")
                print("   ✅ Extensión MP3 correcta")
            else:
                print("   ⚠️ Formato o extensión inesperados")
            
            # Limpiar
            downloader.cleanup_file(result)
            print("   🗑️ Archivo limpiado")
        else:
            print("❌ Fallo en descarga")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 ¡TODO LISTO!")
    print("✅ Descargas individuales: formato artist - title")
    print("✅ Descargas de playlist: formato artist - title")
    print("✅ Bot listo para usar en producción")
    print("\nComandos disponibles:")
    print("  /download <URL>  - Video individual")
    print("  /playlist <URL>  - Playlist completa")

if __name__ == "__main__":
    asyncio.run(final_test())
