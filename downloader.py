import os
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict
import yt_dlp
import logging

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """Maneja la descarga y conversión de videos de YouTube a MP3"""
    
    def __init__(self, temp_dir: str = "./downloads", max_file_size_mb: int = 50):
        self.temp_dir = Path(temp_dir)
        # Crear la carpeta de descargas si no existe
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        # Configuración para yt-dlp (video único)
        self.ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(self.temp_dir / '%(artist)s - %(title)s.%(ext)s'),  # Formato artist - title
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,  # Menos output verboso
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'restrictfilenames': True,  # Evitar caracteres problemáticos en nombres
            'windowsfilenames': True,   # Compatibilidad con Windows
            'noplaylist': True,  # Solo video único
        }
        
        # Configuración para playlists
        self.playlist_ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(self.temp_dir / '%(artist)s - %(title)s.%(ext)s'),  # Formato artist - title
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
            'noplaylist': False,  # Permitir playlists
            'ignoreerrors': True,  # Continuar si hay errores en algunos videos
            'extract_flat': False,  # Extraer información completa
            'skip_unavailable_fragments': True,  # Saltar fragmentos no disponibles
            'abort_on_unavailable_fragments': False,  # No abortar por fragmentos
        }
    
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
            return await loop.run_in_executor(None, self._check_playlist_sync, url)
        except Exception as e:
            logger.error(f"Error verificando playlist {url}: {str(e)}")
            return {"is_playlist": False, "error": str(e)}
    
    def _check_playlist_sync(self, url: str) -> Dict:
        """Método síncrono para verificar playlist"""
        try:
            # Primero, detectar si hay parámetro de playlist en la URL
            url_has_playlist = any(param in url.lower() for param in ['list=', 'playlist?list='])
            
            # Si la URL claramente indica una playlist, asumir que es playlist
            if url_has_playlist:
                logger.info(f"URL contiene parámetro de playlist: {url}")
                
                # Intentar obtener info básica
                try:
                    check_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': True,  # Más rápido para solo info básica
                        'noplaylist': False,   # Permitir playlists
                        'ignoreerrors': True,  # Ignorar videos individuales con errores
                    }
                    
                    with yt_dlp.YoutubeDL(check_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        
                        # Si conseguimos info y hay entries, es playlist
                        if 'entries' in info:
                            entries = [e for e in info.get('entries', []) if e is not None]
                            if len(entries) > 0:
                                playlist_title = (info.get('title') or 
                                               info.get('playlist_title') or 
                                               'Playlist sin título')
                                
                                result = {
                                    'is_playlist': True,
                                    'title': playlist_title,
                                    'playlist_title': playlist_title,
                                    'playlist_count': len(entries),
                                    'uploader': info.get('uploader', 'Desconocido'),
                                }
                                logger.info(f"Playlist detectada: '{playlist_title}' con {len(entries)} videos")
                                return result
                
                except Exception as e:
                    logger.warning(f"Error obteniendo info de playlist, pero URL indica playlist: {e}")
                
                # Si falla la obtención de info pero la URL claramente es de playlist,
                # asumir que es playlist con información limitada
                result = {
                    'is_playlist': True,
                    'title': 'Playlist detectada por URL',
                    'playlist_title': 'Playlist (información limitada)',
                    'playlist_count': 'Desconocido',
                    'uploader': 'Desconocido',
                    'warning': 'No se pudo obtener información detallada de la playlist'
                }
                logger.info("Playlist asumida por formato de URL")
                return result
            
            # Si no hay indicador de playlist en URL, verificar como video individual
            else:
                check_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,  # Solo video individual
                }
                
                with yt_dlp.YoutubeDL(check_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    result = {
                        'is_playlist': False,
                        'title': info.get('title', 'Sin título'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Desconocido'),
                    }
                    logger.info(f"Video individual detectado: '{info.get('title', 'Sin título')}'")
                    return result
                
        except Exception as e:
            logger.error(f"Error en _check_playlist_sync: {str(e)}")
            # Si hay parámetro de playlist en la URL pero falló todo,
            # still asumir que es playlist
            if any(param in url.lower() for param in ['list=', 'playlist?list=']):
                return {
                    "is_playlist": True,
                    "title": "Playlist (error en detección)",
                    "playlist_title": "Playlist con errores",
                    "playlist_count": "Desconocido",
                    "error": str(e),
                    "warning": "Se detectó playlist por URL pero hubo errores al obtener información"
                }
            else:
                return {"is_playlist": False, "error": str(e)}

    async def download_playlist(self, url: str) -> Dict:
        """
        Descarga una playlist completa, continuando aunque haya errores
        
        Args:
            url: URL de la playlist
            
        Returns:
            Dict con resultados de la descarga
        """
        try:
            logger.info(f"Iniciando descarga de playlist: {url}")
            
            # Ejecutar en thread para no bloquear
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._download_playlist_sync, url)
            
            return result
            
        except Exception as e:
            logger.error(f"Error descargando playlist {url}: {str(e)}")
            return {
                "success": False,
                "downloaded_files": [],
                "failed_count": 0,
                "total_count": 0,
                "error": str(e)
            }
    
    def _download_playlist_sync(self, url: str) -> Dict:
        """Método síncrono para descargar playlist"""
        downloaded_files = []
        failed_count = 0
        total_count = 0
        
        try:
            # Obtener archivos antes de la descarga
            files_before = set(self.temp_dir.glob("*.mp3"))
            
            with yt_dlp.YoutubeDL(self.playlist_ydl_opts) as ydl:
                # Primero obtener info de la playlist para contar videos
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
                    logger.warning(f"Error durante descarga masiva, pero algunos archivos pueden haberse descargado: {e}")
            
            # Obtener archivos después de la descarga
            files_after = set(self.temp_dir.glob("*.mp3"))
            new_files = files_after - files_before
            
            # Filtrar archivos por tamaño y validarlos
            for file_path in new_files:
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > self.max_file_size_bytes:
                        logger.warning(f"Archivo muy grande eliminado: {file_path.name} ({file_size / 1024 / 1024:.1f}MB)")
                        os.remove(file_path)
                        failed_count += 1
                    elif file_size > 1024:  # Al menos 1KB para ser válido
                        downloaded_files.append(str(file_path))
                        logger.info(f"Archivo descargado: {file_path.name}")
                    else:
                        logger.warning(f"Archivo muy pequeño eliminado: {file_path.name}")
                        os.remove(file_path)
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error procesando archivo {file_path}: {e}")
                    failed_count += 1
            
            # Si no tenemos total_count, estimarlo
            if total_count == 0:
                total_count = len(downloaded_files) + failed_count
            else:
                # Calcular fallidos basado en diferencia
                failed_count = max(0, total_count - len(downloaded_files))
            
            result = {
                "success": len(downloaded_files) > 0,
                "downloaded_files": sorted(downloaded_files),
                "failed_count": failed_count,
                "total_count": total_count,
                "downloaded_count": len(downloaded_files)
            }
            
            logger.info(f"Playlist completada: {len(downloaded_files)} descargados, {failed_count} fallaron de {total_count} total")
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

    async def download_audio(self, url: str) -> Optional[str]:
        """
        Descarga el audio de un video de YouTube y lo convierte a MP3
        
        Args:
            url: URL del video de YouTube
            
        Returns:
            Ruta del archivo MP3 descargado o None si hay error
        """
        try:
            logger.info(f"Iniciando descarga de: {url}")
            
            # Ejecutar yt-dlp en un thread para no bloquear
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._download_sync, url)
            
            if result:
                # Verificar tamaño del archivo
                file_size = os.path.getsize(result)
                if file_size > self.max_file_size_bytes:
                    logger.warning(f"Archivo muy grande: {file_size / 1024 / 1024:.1f}MB")
                    os.remove(result)
                    return None
                
                logger.info(f"Descarga completada: {result}")
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error descargando {url}: {str(e)}")
            return None
    
    def _download_sync(self, url: str) -> Optional[str]:
        """Método síncrono para descargar con yt-dlp"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Obtener información del video
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
                duration = info.get('duration', 0)
                
                # Limpiar título para búsqueda de archivos
                clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                clean_title = clean_title[:60]  # Limitar longitud
                
                # Verificar duración (máximo 30 minutos)
                if duration > 1800:
                    logger.warning(f"Video muy largo: {duration}s")
                    return None
                
                # Obtener lista de archivos antes de la descarga
                files_before = set(self.temp_dir.glob("*.mp3"))
                
                # Descargar
                ydl.download([url])
                
                # Obtener archivos después de la descarga
                files_after = set(self.temp_dir.glob("*.mp3"))
                new_files = files_after - files_before
                
                if new_files:
                    # Retornar el archivo más reciente
                    newest_file = max(new_files, key=lambda f: f.stat().st_mtime)
                    return str(newest_file)
                
                # Fallback: buscar por título
                possible_files = list(self.temp_dir.glob(f"*{clean_title}*.mp3"))
                if possible_files:
                    return str(possible_files[0])
                
                # Último fallback: cualquier MP3 reciente
                all_mp3_files = list(self.temp_dir.glob("*.mp3"))
                if all_mp3_files:
                    newest = max(all_mp3_files, key=lambda f: f.stat().st_mtime)
                    return str(newest)
                
                return None
                
        except Exception as e:
            logger.error(f"Error en descarga síncrona: {str(e)}")
            return None
    
    def cleanup_files(self, file_paths: List[str]):
        """Elimina múltiples archivos después de enviarlos"""
        for file_path in file_paths:
            self.cleanup_file(file_path)
    
    def cleanup_file(self, file_path: str):
        """Elimina un archivo después de enviarlo"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Archivo eliminado: {file_path}")
        except Exception as e:
            logger.error(f"Error eliminando archivo {file_path}: {str(e)}")
    
    def cleanup_temp_dir(self):
        """Limpia todos los archivos temporales"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
                logger.info("Directorio temporal limpiado")
        except Exception as e:
            logger.error(f"Error limpiando directorio temporal: {str(e)}")
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Verifica si una URL es de YouTube"""
        youtube_domains = [
            'youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com'
        ]
        return any(domain in url.lower() for domain in youtube_domains)
