import os
import asyncio
import tempfile
import shutil
import uuid
from pathlib import Path
from typing import Optional, List, Dict
import yt_dlp
import logging
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class MultiUserYouTubeDownloader:
    """Maneja la descarga y conversión de videos de YouTube a MP3 con soporte para múltiples usuarios"""
    
    def __init__(self, base_temp_dir: str = "./downloads", max_file_size_mb: int = 50, max_concurrent_downloads: int = 3):
        self.base_temp_dir = Path(base_temp_dir)
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.max_concurrent_downloads = max_concurrent_downloads
        
        # Semáforo para limitar descargas concurrentes
        self.download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        
        # Executor para operaciones de descarga
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_downloads)
        
        # Diccionario para trackear descargas activas por usuario
        self.active_downloads = {}
    
    def _create_user_temp_dir(self, user_id: int) -> Path:
        """Crea un directorio temporal único para cada usuario"""
        user_dir = self.base_temp_dir / f"user_{user_id}_{uuid.uuid4().hex[:8]}"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _get_ydl_opts(self, temp_dir: Path, is_playlist: bool = False) -> dict:
        """Obtiene configuración de yt-dlp para un directorio específico"""
        base_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(temp_dir / '%(artist)s - %(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'restrictfilenames': True,
            'windowsfilenames': True,
        }
        
        if is_playlist:
            base_opts.update({
                'noplaylist': False,
                'ignoreerrors': True,
                'extract_flat': False,
                'skip_unavailable_fragments': True,
                'abort_on_unavailable_fragments': False,
            })
        else:
            base_opts['noplaylist'] = True
            
        return base_opts
    
    async def check_if_playlist(self, url: str) -> Dict:
        """
        Verifica si una URL es una playlist y obtiene información básica
        
        Args:
            url: URL a verificar
            
        Returns:
            Dict con información de la URL
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self._check_playlist_sync, url)
        except Exception as e:
            logger.error(f"Error verificando playlist {url}: {str(e)}")
            return {"is_playlist": False, "error": str(e)}
    
    def _check_playlist_sync(self, url: str) -> Dict:
        """Método síncrono para verificar playlist"""
        try:
            # Detectar si hay parámetro de playlist en la URL
            url_has_playlist = any(param in url.lower() for param in ['list=', 'playlist?list='])
            
            if url_has_playlist:
                logger.info(f"URL contiene parámetro de playlist: {url}")
                
                try:
                    check_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': True,
                        'noplaylist': False,
                        'ignoreerrors': True,
                    }
                    
                    with yt_dlp.YoutubeDL(check_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        
                        if 'entries' in info:
                            entries = [e for e in info.get('entries', []) if e is not None]
                            if len(entries) > 0:
                                playlist_title = (info.get('title') or 
                                               info.get('playlist_title') or 
                                               'Playlist sin título')
                                
                                return {
                                    'is_playlist': True,
                                    'title': playlist_title,
                                    'playlist_title': playlist_title,
                                    'playlist_count': len(entries),
                                    'uploader': info.get('uploader', 'Desconocido'),
                                }
                
                except Exception as e:
                    logger.warning(f"Error obteniendo info de playlist: {e}")
                
                return {
                    'is_playlist': True,
                    'title': 'Playlist detectada por URL',
                    'playlist_title': 'Playlist (información limitada)',
                    'playlist_count': 'Desconocido',
                    'uploader': 'Desconocido',
                    'warning': 'No se pudo obtener información detallada de la playlist'
                }
            
            else:
                check_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                }
                
                with yt_dlp.YoutubeDL(check_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    return {
                        'is_playlist': False,
                        'title': info.get('title', 'Sin título'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Desconocido'),
                    }
                
        except Exception as e:
            logger.error(f"Error en _check_playlist_sync: {str(e)}")
            if any(param in url.lower() for param in ['list=', 'playlist?list=']):
                return {
                    "is_playlist": True,
                    "title": "Playlist (error en detección)",
                    "playlist_title": "Playlist con errores",
                    "playlist_count": "Desconocido",
                    "error": str(e),
                    "warning": "Se detectó playlist por URL pero hubo errores"
                }
            else:
                return {"is_playlist": False, "error": str(e)}

    async def download_audio(self, url: str, user_id: int) -> Optional[str]:
        """
        Descarga el audio de un video de YouTube para un usuario específico
        
        Args:
            url: URL del video de YouTube
            user_id: ID del usuario de Telegram
            
        Returns:
            Ruta del archivo MP3 descargado o None si hay error
        """
        # Verificar si el usuario ya tiene una descarga activa
        if user_id in self.active_downloads:
            logger.warning(f"Usuario {user_id} ya tiene una descarga activa")
            return None
        
        # Adquirir semáforo para limitar descargas concurrentes
        async with self.download_semaphore:
            try:
                # Marcar descarga como activa para este usuario
                self.active_downloads[user_id] = time.time()
                
                logger.info(f"Iniciando descarga de: {url} para usuario {user_id}")
                
                # Crear directorio temporal único para el usuario
                user_temp_dir = self._create_user_temp_dir(user_id)
                
                # Ejecutar descarga en thread
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor, 
                    self._download_sync, 
                    url, 
                    user_temp_dir, 
                    False  # is_playlist
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Error descargando {url} para usuario {user_id}: {str(e)}")
                return None
            finally:
                # Quitar usuario de descargas activas
                if user_id in self.active_downloads:
                    del self.active_downloads[user_id]

    async def download_playlist(self, url: str, user_id: int) -> Dict:
        """
        Descarga una playlist completa para un usuario específico
        
        Args:
            url: URL de la playlist
            user_id: ID del usuario de Telegram
            
        Returns:
            Dict con resultados de la descarga
        """
        # Verificar si el usuario ya tiene una descarga activa
        if user_id in self.active_downloads:
            logger.warning(f"Usuario {user_id} ya tiene una descarga activa")
            return {
                "success": False,
                "error": "Ya tienes una descarga en progreso. Espera a que termine.",
                "downloaded_files": [],
                "failed_count": 0,
                "total_count": 0
            }
        
        # Adquirir semáforo para limitar descargas concurrentes
        async with self.download_semaphore:
            try:
                # Marcar descarga como activa para este usuario
                self.active_downloads[user_id] = time.time()
                
                logger.info(f"Iniciando descarga de playlist: {url} para usuario {user_id}")
                
                # Crear directorio temporal único para el usuario
                user_temp_dir = self._create_user_temp_dir(user_id)
                
                # Ejecutar descarga en thread
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor, 
                    self._download_playlist_sync, 
                    url, 
                    user_temp_dir
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Error descargando playlist {url} para usuario {user_id}: {str(e)}")
                return {
                    "success": False,
                    "downloaded_files": [],
                    "failed_count": 0,
                    "total_count": 0,
                    "error": str(e)
                }
            finally:
                # Quitar usuario de descargas activas
                if user_id in self.active_downloads:
                    del self.active_downloads[user_id]
    
    def _download_sync(self, url: str, temp_dir: Path, is_playlist: bool = False) -> Optional[str]:
        """Método síncrono para descargar con yt-dlp"""
        try:
            ydl_opts = self._get_ydl_opts(temp_dir, is_playlist)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Obtener información del video
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                duration = info.get('duration', 0)
                
                # Verificar duración (máximo 30 minutos)
                if not is_playlist and duration > 1800:
                    logger.warning(f"Video muy largo: {duration}s")
                    return None
                
                # Obtener lista de archivos antes de la descarga
                files_before = set(temp_dir.glob("*.mp3"))
                
                # Descargar
                ydl.download([url])
                
                # Obtener archivos después de la descarga
                files_after = set(temp_dir.glob("*.mp3"))
                new_files = files_after - files_before
                
                if new_files:
                    # Verificar tamaño y retornar el archivo más reciente
                    for file_path in new_files:
                        file_size = os.path.getsize(file_path)
                        if file_size > self.max_file_size_bytes:
                            logger.warning(f"Archivo muy grande eliminado: {file_path.name}")
                            os.remove(file_path)
                            continue
                        
                        if file_size > 1024:  # Al menos 1KB
                            return str(file_path)
                
                return None
                
        except Exception as e:
            logger.error(f"Error en descarga síncrona: {str(e)}")
            return None
    
    def _download_playlist_sync(self, url: str, temp_dir: Path) -> Dict:
        """Método síncrono para descargar playlist"""
        downloaded_files = []
        failed_count = 0
        total_count = 0
        
        try:
            ydl_opts = self._get_ydl_opts(temp_dir, True)
            
            # Obtener archivos antes de la descarga
            files_before = set(temp_dir.glob("*.mp3"))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Obtener info de la playlist
                try:
                    info = ydl.extract_info(url, download=False)
                    if '_type' in info and info['_type'] == 'playlist':
                        total_count = len(info.get('entries', []))
                        logger.info(f"Playlist detectada con {total_count} videos")
                            
                except Exception as e:
                    logger.warning(f"No se pudo obtener info de playlist: {e}")
                
                # Descargar la playlist
                try:
                    ydl.download([url])
                except Exception as e:
                    logger.warning(f"Error durante descarga masiva: {e}")
            
            # Obtener archivos después de la descarga
            files_after = set(temp_dir.glob("*.mp3"))
            new_files = files_after - files_before
            
            # Validar archivos descargados
            for file_path in new_files:
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > self.max_file_size_bytes:
                        logger.warning(f"Archivo muy grande eliminado: {file_path.name}")
                        os.remove(file_path)
                        failed_count += 1
                    elif file_size > 1024:  # Al menos 1KB
                        downloaded_files.append(str(file_path))
                        logger.info(f"Archivo descargado: {file_path.name}")
                    else:
                        logger.warning(f"Archivo muy pequeño eliminado: {file_path.name}")
                        os.remove(file_path)
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error procesando archivo {file_path}: {e}")
                    failed_count += 1
            
            # Calcular estadísticas
            if total_count == 0:
                total_count = len(downloaded_files) + failed_count
            else:
                failed_count = max(0, total_count - len(downloaded_files))
            
            result = {
                "success": len(downloaded_files) > 0,
                "downloaded_files": sorted(downloaded_files),
                "failed_count": failed_count,
                "total_count": total_count,
                "downloaded_count": len(downloaded_files)
            }
            
            logger.info(f"Playlist completada: {len(downloaded_files)} descargados, {failed_count} fallaron")
            return result
            
        except Exception as e:
            logger.error(f"Error en _download_playlist_sync: {str(e)}")
            return {
                "success": False,
                "downloaded_files": downloaded_files,
                "failed_count": failed_count,
                "total_count": total_count,
                "downloaded_count": len(downloaded_files),
                "error": str(e)
            }
    
    def cleanup_user_files(self, file_paths: List[str], user_id: int):
        """Elimina archivos específicos de un usuario"""
        for file_path in file_paths:
            self.cleanup_file(file_path)
        
        # Intentar limpiar directorio del usuario si está vacío
        try:
            user_dirs = list(self.base_temp_dir.glob(f"user_{user_id}_*"))
            for user_dir in user_dirs:
                if user_dir.is_dir():
                    try:
                        # Si el directorio está vacío, eliminarlo
                        if not any(user_dir.iterdir()):
                            shutil.rmtree(user_dir)
                            logger.info(f"Directorio temporal del usuario {user_id} eliminado")
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar directorio {user_dir}: {e}")
        except Exception as e:
            logger.warning(f"Error limpiando directorios de usuario {user_id}: {e}")
    
    def cleanup_file(self, file_path: str):
        """Elimina un archivo específico"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Archivo eliminado: {file_path}")
        except Exception as e:
            logger.error(f"Error eliminando archivo {file_path}: {str(e)}")
    
    def get_active_downloads_count(self) -> int:
        """Retorna el número de descargas activas"""
        return len(self.active_downloads)
    
    def is_user_downloading(self, user_id: int) -> bool:
        """Verifica si un usuario específico tiene una descarga activa"""
        return user_id in self.active_downloads
    
    def get_user_download_time(self, user_id: int) -> Optional[float]:
        """Obtiene el tiempo de inicio de descarga de un usuario"""
        return self.active_downloads.get(user_id)
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Verifica si una URL es de YouTube"""
        youtube_domains = [
            'youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com'
        ]
        return any(domain in url.lower() for domain in youtube_domains)
    
    def cleanup_temp_dir(self):
        """Limpia todos los archivos temporales"""
        try:
            if self.base_temp_dir.exists():
                shutil.rmtree(self.base_temp_dir)
                self.base_temp_dir.mkdir(exist_ok=True)
                logger.info("Directorio temporal limpiado completamente")
        except Exception as e:
            logger.error(f"Error limpiando directorio temporal: {str(e)}")
    
    def __del__(self):
        """Cierra el executor al destruir la instancia"""
        try:
            self.executor.shutdown(wait=False)
        except:
            pass
