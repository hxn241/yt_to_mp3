# Archivo para configurar el path de Python en el proyecto
import sys
import os

# Añadir el directorio del proyecto al path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Verificar que las importaciones funcionen
try:
    import telegram
    import yt_dlp
    import dotenv
    print("✅ Todas las librerías importadas correctamente")
except ImportError as e:
    print(f"❌ Error importando: {e}")
