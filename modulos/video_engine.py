import os
import base64
import time
from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips

class VideoEngine:
    def __init__(self):
        self.workspace_dir = os.getcwd()
        # Rutas dinámicas para Assets inmutables (Intros/Outros) y Renders temporales
        self.assets_dir = os.path.join(self.workspace_dir, "static", "assets")
        self.temp_dir = os.path.join(self.workspace_dir, "static", "temp")
        self._inicializar_directorios()

    def _inicializar_directorios(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        marcas = ["la_viuda", "monkygraff"]
        for marca in marcas:
            os.makedirs(os.path.join(self.assets_dir, marca), exist_ok=True)

    def _limpiar_b64(self, b64_string):
        """Remueve las cabeceras URI de los strings de telemetría del Frontend."""
        if "," in b64_string:
            return b64_string.split(",")[1]
        return b64_string

    def ensamblar_pipeline(self, marca, img_b64, audio_b64):
        try:
            # Normalización del silo hermético
            marca_folder = marca.lower().replace(" ", "_")
            timestamp = int(time.time())
            
            # 1. Preparación de Rutas Físicas
            temp_img = os.path.join(self.temp_dir, f"frame_{timestamp}.png")
            temp_audio = os.path.join(self.temp_dir, f"voz_{timestamp}.mp3")
            output_file = os.path.join(self.temp_dir, f"render_final_{timestamp}.mp4")
            output_url = f"/static/temp/render_final_{timestamp}.mp4"

            # 2. Decodificación de Matrices (Base64 -> Físico)
            with open(temp_img, "wb") as fh:
                fh.write(base64.b64decode(self._limpiar_b64(img_b64)))
            with open(temp_audio, "wb") as fh:
                fh.write(base64.b64decode(self._limpiar_b64(audio_b64)))

            # Rutas de Hook/Intro y Outro
            intro_path = os.path.join(self.assets_dir, marca_folder, "intro.mp4")
            outro_path = os.path.join(self.assets_dir, marca_folder, "outro.mp4")

            clips_a_unir = []

            # 3. Ensamblaje: FASE A (Hook de Inicio / Presentación)
            if os.path.exists(intro_path):
                intro_clip = VideoFileClip(intro_path)
                # Forzar 1920x1080 para evitar colapsos por diferencias de formato
                intro_clip = intro_clip.resize((1920, 1080))
                clips_a_unir.append(intro_clip)

            # 4. Ensamblaje: FASE B (Cuerpo IA: Imagen CCTV + Clonación ElevenLabs)
            audio_clip = AudioFileClip(temp_audio)
            # Redimensionado estricto al estándar de YouTube (16:9) y ajuste de duración
            main_clip = ImageClip(temp_img).resize((1920, 1080)).set_duration(audio_clip.duration)
            main_clip = main_clip.set_audio(audio_clip)
            main_clip = main_clip.set_fps(24) # FPS cinematográfico estándar
            clips_a_unir.append(main_clip)

            # 5. Ensamblaje: FASE C (Outro / Llamado a la Acción)
            if os.path.exists(outro_path):
                outro_clip = VideoFileClip(outro_path)
                outro_clip = outro_clip.resize((1920, 1080))
                clips_a_unir.append(outro_clip)

            # 6. Compilación Final
            video_final = concatenate_videoclips(clips_a_unir, method="compose")
            
            # Renderizado (Preset ultrafast para optimizar el CPU de Render)
            video_final.write_videofile(
                output_file, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac", 
                preset="ultrafast", 
                threads=4,
                logger=None
            )

            # 7. Liberación de RAM y limpieza de temporales residuales
            video_final.close()
            audio_clip.close()
            if os.path.exists(temp_img): os.remove(temp_img)
            if os.path.exists(temp_audio): os.remove(temp_audio)

            return {"status": "success", "video_url": output_url}

        except Exception as e:
            return {"status": "error", "message": f"FALLA DE COMPILACIÓN MP4 -> {str(e)}"}
