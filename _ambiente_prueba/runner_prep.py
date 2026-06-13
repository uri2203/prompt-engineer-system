"""Preparación del entorno de prueba: directorios y assets."""
import os
import shutil

BASE = "/home/claude/test_env"
SANDBOX = os.path.join(BASE, "sandbox")
ASSETS = os.path.join(BASE, "sandbox_assets")
NODO = os.path.join(BASE, "nodo_pinpinela")

def preparar():
    # Limpiar sandbox y assets (pero conservar voice_local.py en NODO)
    shutil.rmtree(SANDBOX, ignore_errors=True)
    shutil.rmtree(ASSETS, ignore_errors=True)
    os.makedirs(SANDBOX, exist_ok=True)
    os.makedirs(ASSETS, exist_ok=True)
    os.makedirs(NODO, exist_ok=True)
    os.makedirs(os.path.join(NODO, "cola_local"), exist_ok=True)

    # Assets por marca: música, intro, outro reales (con ffmpeg)
    for marca in ["la viuda", "monkygraff", "laesquinarandom", "filtradomx", "tuialista"]:
        carpeta = os.path.join(ASSETS, marca)
        os.makedirs(carpeta, exist_ok=True)
        for nombre in ["musica_fondo1.mp3", "musica_fondo2.mp3", "musica_fondo3.mp3", "musica_tension1.mp3"]:
            ruta = os.path.join(carpeta, nombre)
            os.system(f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t 130 -q:a 9 '{ruta}' >/dev/null 2>&1")
        # Intro y outro (videos cortos reales)
        for nombre in ["intro_916.mp4", "outro_916.mp4", "intro_169.mp4", "outro_169.mp4"]:
            ruta = os.path.join(carpeta, nombre)
            os.system(f"ffmpeg -y -f lavfi -i color=c=black:s=576x1024:d=2 -f lavfi -i anullsrc=r=44100:cl=mono -t 2 -c:v libx264 -pix_fmt yuv420p '{ruta}' >/dev/null 2>&1")

def crear_imagenes_prueba(carpeta, n):
    """Crea n imágenes PNG realistas (con ruido/detalle) que FFmpeg procesa bien."""
    os.makedirs(carpeta, exist_ok=True)
    for i in range(n):
        ruta = os.path.join(carpeta, f"escena_{i:02d}.png")
        # Imagen con ruido real (no color sólido) tamaño 9:16, que zoompan procesa correctamente
        os.system(
            f"ffmpeg -y -f lavfi -i 'nullsrc=s=576x1024,geq=random(1)*255:128:128' "
            f"-frames:v 1 '{ruta}' >/dev/null 2>&1"
        )
        if not os.path.exists(ruta) or os.path.getsize(ruta) < 500:
            # Fallback: testsrc (patrón de barras con detalle)
            os.system(f"ffmpeg -y -f lavfi -i testsrc=s=576x1024:d=1 -frames:v 1 '{ruta}' >/dev/null 2>&1")
