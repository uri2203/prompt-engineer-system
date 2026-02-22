import os
import logging
from moviepy.editor import ColorClip, AudioFileClip

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [VIDEO_RENDER] - %(levelname)s - %(message)s')

class VideoRenderEngine:
    def __init__(self):
        logging.info("Inicializando Motor de Renderizado (Dual Format: 16:9 / 9:16)")
        self.output_dir = os.path.join(os.getcwd(), "workspace_temp", "video")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.formatos = {
            "La Viuda": {"resolucion": (1280, 720), "orientacion": "16:9", "color": (15, 21, 35)},
            "Monkygraff": {"resolucion": (1280, 720), "orientacion": "16:9", "color": (40, 40, 40)},
            "TuIALista": {"resolucion": (1280, 720), "orientacion": "16:9", "color": (11, 17, 32)},
            "Ezzenshop": {"resolucion": (720, 1280), "orientacion": "9:16", "color": (139, 92, 246)},
            "Yayika Digital": {"resolucion": (720, 1280), "orientacion": "9:16", "color": (244, 114, 182)},
            "Yayika Apparel": {"resolucion": (720, 1280), "orientacion": "9:16", "color": (20, 20, 20)},
            "default": {"resolucion": (1280, 720), "orientacion": "16:9", "color": (0, 0, 0)}
        }

    def compilar_video_base(self, ruta_audio, marca, tarea_id):
        logging.info(f"Iniciando compilación | Orden: {tarea_id} | Marca: {marca}")
        
        if not os.path.exists(ruta_audio):
            return {"status": "ERROR", "mensaje": "Audio no encontrado."}

        config = self.formatos.get(marca, self.formatos["default"])
        resolucion = config["resolucion"]
        ruta_salida = os.path.join(self.output_dir, f"video_{tarea_id}.mp4")

        try:
            audio_clip = AudioFileClip(ruta_audio)
            video_clip = ColorClip(size=resolucion, color=config["color"], duration=audio_clip.duration)
            video_final = video_clip.set_audio(audio_clip)
            
            video_final.write_videofile(ruta_salida, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
            
            audio_clip.close(); video_clip.close(); video_final.close()
            return {"status": "SUCCESS", "ruta_video": ruta_salida}
        except Exception as e:
            return {"status": "ERROR", "mensaje": str(e)}
