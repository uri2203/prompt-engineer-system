import os
import base64
import time
from PIL import Image

# BLINDAJE DE INFRAESTRUCTURA (MONKEY PATCH)
if not hasattr(Image, 'ANTIALIAS'):
    try:
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    except AttributeError:
        Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips

class VideoEngine:
    def __init__(self):
        self.workspace_dir = os.getcwd()
        self.assets_dir = os.path.join(self.workspace_dir, "static", "assets")
        self.temp_dir = os.path.join(self.workspace_dir, "static", "temp")
        self._inicializar_directorios()

    def _inicializar_directorios(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        marcas = ["la_viuda", "monkygraff"]
        for marca in marcas:
            os.makedirs(os.path.join(self.assets_dir, marca), exist_ok=True)

    def _limpiar_b64(self, b64_string):
        if "," in b64_string:
            return b64_string.split(",")[1]
        return b64_string

    def ensamblar_pipeline(self, marca, img_b64, audio_b64):
        try:
            marca_folder = marca.lower().replace(" ", "_")
            timestamp = int(time.time())
            
            # Rutas
            temp_img = os.path.join(self.temp_dir, f"frame_{timestamp}.png")
            temp_audio = os.path.join(self.temp_dir, f"voz_{timestamp}.mp3")
            output_file = os.path.join(self.temp_dir, f"render_final_{timestamp}.mp4")
            output_url = f"/static/temp/render_final_{timestamp}.mp4"

            # Decodificación
            with open(temp_img, "wb") as fh:
                fh.write(base64.b64decode(self._limpiar_b64(img_b64)))
            with open(temp_audio, "wb") as fh:
                fh.write(base64.b64decode(self._limpiar_b64(audio_b64)))

            intro_path = os.path.join(self.assets_dir, marca_folder, "intro.mp4")
            outro_path = os.path.join(self.assets_dir, marca_folder, "outro.mp4")

            clips_a_unir = []
            
            # TÁCTICA DE OPTIMIZACIÓN DE RECURSOS (NUBE GRATUITA)
            fps_optimo = 5 # Drástica reducción de carga en RAM (Suficiente para estáticos)

            # Fase A (Intro)
            if os.path.exists(intro_path):
                intro_clip = VideoFileClip(intro_path).resize((1920, 1080))
                clips_a_unir.append(intro_clip)

            # Fase B (Cuerpo)
            audio_clip = AudioFileClip(temp_audio)
            main_clip = ImageClip(temp_img).resize((1920, 1080)).set_duration(audio_clip.duration)
            main_clip = main_clip.set_audio(audio_clip)
            main_clip = main_clip.set_fps(fps_optimo)
            clips_a_unir.append(main_clip)

            # Fase C (Outro)
            if os.path.exists(outro_path):
                outro_clip = VideoFileClip(outro_path).resize((1920, 1080))
                clips_a_unir.append(outro_clip)

            # Compilación
            video_final = concatenate_videoclips(clips_a_unir, method="compose")
            
            # Renderizado Estratégico para CPU de 0.1 Cores
            video_final.write_videofile(
                output_file, 
                fps=fps_optimo, 
                codec="libx264", 
                audio_codec="aac", 
                preset="ultrafast", 
                threads=1, # Obligatorio para evitar congelamiento del contenedor
                logger=None
            )

            # Limpieza
            video_final.close()
            audio_clip.close()
            if os.path.exists(temp_img): os.remove(temp_img)
            if os.path.exists(temp_audio): os.remove(temp_audio)

            return {"status": "success", "video_url": output_url}

        except Exception as e:
            return {"status": "error", "message": f"FALLA DE COMPILACIÓN MP4 -> {str(e)}"}
