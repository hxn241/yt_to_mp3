#!/usr/bin/env python3
"""
Prueba rápida de detección de playlist con URL específica
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader import YouTubeDownloader

async def quick_test():
    """Prueba rápida"""
    print("🔍 Prueba rápida de detección de playlist")
    
    downloader = YouTubeDownloader()
    
    # La URL problemática
    test_url = "https://www.youtube.com/watch?v=EDRBluZnyys&list=PLa7sBOYG7Txw0SdJCDwLFyPwkyphPRXkk"
    
    print(f"📺 Verificando: {test_url}")
    
    try:
        info = await downloader.check_if_playlist(test_url)
        
        print(f"\n✅ RESULTADO:")
        print(f"   Es playlist: {info.get('is_playlist', False)}")
        print(f"   Título: {info.get('title', 'N/A')}")
        
        if info.get('is_playlist'):
            print(f"   Título playlist: {info.get('playlist_title', 'N/A')}")
            print(f"   Cantidad videos: {info.get('playlist_count', 'N/A')}")
            
            if info.get('warning'):
                print(f"   ⚠️ Advertencia: {info.get('warning')}")
        
        if info.get('error'):
            print(f"   ❌ Error: {info.get('error')}")
            
        print(f"\n🎯 CONCLUSIÓN: {'PLAYLIST DETECTADA' if info.get('is_playlist') else 'NO ES PLAYLIST'}")
            
    except Exception as e:
        print(f"❌ Error en prueba: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
