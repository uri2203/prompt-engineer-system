import os
import logging
from modulos.cctv_engine import CCTVEngine
from modulos.bot_audio import AudioSynthEngine
from modulos.bot_video import VideoRenderEngine

class PinpinelaOrchestrator:
    def __init__(self):
        self.mod_cctv = CCTVEngine()
        self.mod_audio = AudioSynthEngine()
        self.mod_video = VideoRenderEngine()

    def procesar_orden(self, tarea_id, marca, premisa, formato="16:9"):
        logging.info(f"> [SISTEMA] Disparando Fase 2 (CCTV)...")
        # 1. Generar imagen en la RTX 3050
        ruta_img = self.mod_cctv.generar_imagen(premisa, tarea_id)
        
        if not ruta_img:
            return {"status": "FAILED", "fase": "CCTV", "detalle": "La GPU no respondió"}

        logging.info(f"> [SISTEMA] Disparando Fase 3 (Locución)...")
        # 2. Generar Audio
        res_audio = self.mod_audio.generar_audio_base(premisa, marca, tarea_id)
        ruta_mp3 = res_audio["ruta_audio"]

        logging.info(f"> [SISTEMA] Disparando Fase 4 (Video)...")
        # 3. Ensamblar todo
        res_video = self.mod_video.compilar_video_base(ruta_mp3, ruta_img, marca, tarea_id)
        
        return {
            "status": "SUCCESS",
            "ruta_video": res_video["ruta_video"]
        }
