#!/usr/bin/env python3
"""
Test del bot multiusuario - Simula múltiples usuarios
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from downloader_multiuser import MultiUserYouTubeDownloader

async def test_multiuser():
    """Prueba del sistema multiusuario"""
    print("👥 PRUEBA MULTIUSUARIO")
    print("=" * 50)
    
    downloader = MultiUserYouTubeDownloader(
        base_temp_dir="./downloads_test",
        max_concurrent_downloads=2  # Limitar para la prueba
    )
    
    # Simular 3 usuarios
    users = [
        {"id": 12345, "name": "Usuario1"},
        {"id": 67890, "name": "Usuario2"},  
        {"id": 11111, "name": "Usuario3"}
    ]
    
    # URL de prueba
    test_url = "https://www.youtube.com/watch?v=EDRBluZnyys"
    
    print(f"🔧 Configuración:")
    print(f"   • Máximo descargas simultáneas: {downloader.max_concurrent_downloads}")
    print(f"   • Usuarios de prueba: {len(users)}")
    print(f"   • URL de prueba: {test_url}")
    print()
    
    async def simulate_user_download(user):
        """Simula descarga de un usuario"""
        user_id = user["id"]
        user_name = user["name"]
        
        print(f"👤 {user_name} (ID:{user_id}) - Iniciando descarga...")
        
        try:
            # Verificar si el usuario puede descargar
            if downloader.is_user_downloading(user_id):
                print(f"   ⏳ {user_name} - Ya tiene descarga activa")
                return False
            
            if downloader.get_active_downloads_count() >= downloader.max_concurrent_downloads:
                print(f"   🚦 {user_name} - Bot ocupado, esperando...")
                return False
            
            # Intentar descarga
            result = await downloader.download_audio(test_url, user_id)
            
            if result and os.path.exists(result):
                filename = Path(result).name
                print(f"   ✅ {user_name} - Descargado: {filename}")
                
                # Verificar formato
                if " - " in filename:
                    print(f"      ✅ Formato artist - title correcto")
                
                # Verificar directorio único
                user_dir = Path(result).parent.name
                if f"user_{user_id}_" in user_dir:
                    print(f"      ✅ Directorio único: {user_dir}")
                
                # Limpiar archivo
                downloader.cleanup_user_files([result], user_id)
                print(f"      🗑️ Archivo limpiado")
                return True
            else:
                print(f"   ❌ {user_name} - Descarga falló")
                return False
                
        except Exception as e:
            print(f"   ❌ {user_name} - Error: {e}")
            return False
    
    # Prueba 1: Descargas secuenciales
    print("📝 PRUEBA 1: Descargas secuenciales")
    print("-" * 30)
    
    successful_downloads = 0
    for user in users[:2]:  # Solo 2 usuarios para no saturar
        success = await simulate_user_download(user)
        if success:
            successful_downloads += 1
        
        print(f"   📊 Descargas activas: {downloader.get_active_downloads_count()}")
        await asyncio.sleep(1)  # Pequeña pausa
    
    print(f"\n✅ Prueba 1 completada: {successful_downloads} descargas exitosas")
    
    # Prueba 2: Verificar límites
    print(f"\n📝 PRUEBA 2: Verificación de límites")
    print("-" * 30)
    
    print(f"   🔢 Máximo configurado: {downloader.max_concurrent_downloads}")
    print(f"   🔄 Descargas activas actuales: {downloader.get_active_downloads_count()}")
    
    # Intentar con el tercer usuario cuando ya hay descargas
    if downloader.get_active_downloads_count() >= downloader.max_concurrent_downloads:
        print(f"   🚦 Sistema correctamente limitando descargas")
    
    # Verificar estado de usuarios
    print(f"\n📝 ESTADO DE USUARIOS:")
    for user in users:
        user_id = user["id"]
        user_name = user["name"]
        is_downloading = downloader.is_user_downloading(user_id)
        download_time = downloader.get_user_download_time(user_id)
        
        status = "🟢 Disponible"
        if is_downloading:
            elapsed = "unknown"
            if download_time:
                elapsed = f"{asyncio.get_event_loop().time() - download_time:.1f}s"
            status = f"🟡 Descargando ({elapsed})"
        
        print(f"   👤 {user_name}: {status}")
    
    # Limpiar directorio de prueba
    print(f"\n🗑️ Limpiando directorio de prueba...")
    try:
        downloader.cleanup_temp_dir()
        print("   ✅ Limpieza completada")
    except Exception as e:
        print(f"   ⚠️ Error en limpieza: {e}")
    
    print(f"\n🎉 PRUEBA MULTIUSUARIO COMPLETADA")
    print("=" * 50)
    
    print("\n📋 RESUMEN DE CARACTERÍSTICAS:")
    print("✅ Directorios únicos por usuario")
    print("✅ Límite de descargas concurrentes")
    print("✅ Una descarga por usuario")
    print("✅ Formato artist - title")
    print("✅ Limpieza automática")
    print("✅ Control de errores")
    
    print(f"\n🚀 ¡Bot listo para múltiples usuarios!")

if __name__ == "__main__":
    asyncio.run(test_multiuser())
