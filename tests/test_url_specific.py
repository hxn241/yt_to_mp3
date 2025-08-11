#!/usr/bin/env python3
"""
Script de prueba específico para la URL de playlist que reportaste
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader import YouTubeDownloader

async def test_specific_url():
    """Prueba la URL específica que reportaste"""
    print("🔍 Probando detección de la URL específica...")
    
    downloader = YouTubeDownloader()
    
    # La URL que reportaste como problemática
    test_url = "https://www.youtube.com/watch?v=EDRBluZnyys&list=PLa7sBOYG7Txw0SdJCDwLFyPwkyphPRXkk"
    
    print(f"📺 Verificando: {test_url}")
    try:
        info = await downloader.check_if_playlist(test_url)
        print(f"   ✅ Es playlist: {info.get('is_playlist', False)}")
        print(f"   📋 Título: {info.get('title', 'N/A')}")
        
        if info.get('is_playlist'):
            print(f"   📋 Título de playlist: {info.get('playlist_title', 'N/A')}")
            print(f"   🎵 Cantidad de videos: {info.get('playlist_count', 'N/A')}")
        else:
            print(f"   ⏱️ Duración: {info.get('duration', 'N/A')}s")
            
        if info.get('error'):
            print(f"   ❌ Error: {info.get('error')}")
            
    except Exception as e:
        print(f"   ❌ Error en prueba: {e}")

    # También probar algunas variantes de URL
    print("\n🔄 Probando variantes de URL:")
    
    variant_urls = [
        # Solo la playlist
        "https://www.youtube.com/playlist?list=PLjh5PhNL23sZ8sa6p19Rml_zL8krYjJzN",
        # Video + playlist (la original)
        "https://www.youtube.com/watch?v=qnqdJy3m9Rw&list=PLjh5PhNL23sZ8sa6p19Rml_zL8krYjJzN",
        # Solo el video
        "https://www.youtube.com/watch?v=qnqdJy3m9Rw",
    ]
    
    for i, url in enumerate(variant_urls, 1):
        print(f"\n{i}. {url}")
        try:
            info = await downloader.check_if_playlist(url)
            print(f"   Es playlist: {info.get('is_playlist', False)}")
            if info.get('is_playlist'):
                print(f"   Videos: {info.get('playlist_count', 'N/A')}")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_specific_url())
