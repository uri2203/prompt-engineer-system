"""Mock de voice_local — genera un MP3 real (silencioso) en vez de usar XTTS."""
import os

def generar_audio_local(texto, marca, ruta_salida):
    """Simula la generación de voz. Crea un MP3 real cuya duración es
    proporcional al número de palabras (como sería la narración real)."""
    palabras = len(texto.split()) if texto else 50
    # ~2.5 palabras por segundo (ritmo de narración normal)
    duracion = max(5, palabras / 2.5)
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    cmd = f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t {duracion:.1f} -q:a 9 '{ruta_salida}' >/dev/null 2>&1"
    os.system(cmd)
    if os.path.exists(ruta_salida) and os.path.getsize(ruta_salida) > 100:
        print(f"[VOICE MOCK] Audio generado: {palabras} palabras → {duracion:.1f}s")
        return ruta_salida
    return None
