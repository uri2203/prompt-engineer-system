import os
import logging
from moviepy.editor import ImageClip, AudioFileClip

# Mantenemos su sistema de logs profesional
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [VIDEO_RENDER] - %(levelname)s - %(message)s')

class VideoRenderEngine:
    def __init__(self):
        logging.info("🛡️ [SISTEMA] Inicializando Motor de Renderizado (Modo Real CCTV 16:9 / 9:16)")
        self.output_dir = os.path.join(os.getcwd(), "workspace_temp", "video")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Mantenemos sus marcas y resoluciones originales
        self.formatos = {
            "La Viuda": {"resolucion": (1280, 720), "orientacion": "16:9"},
            "Monkygraff": {"resolucion": (1280, 720), "orientacion": "16:9"},
            "TuIALista": {"resolucion": (1280, 720), "orientacion": "16:9"},
            "Ezzenshop": {"resolucion": (720, 1280), "orientacion": "9:16"},
            "Yayika Digital": {"resolucion": (720, 1280), "orientacion": "9:16"},
            "Yayika Apparel": {"resolucion": (720, 1280), "orientacion": "9:16"},
            "default": {"resolucion": (1280, 720), "orientacion": "16:9"}
        }

    def compilar_video_base(self, ruta_audio, ruta_imagen, marca, tarea_id):
        """
        Ensambla el video final usando la imagen generada por la RTX 3050.
        """
        logging.info(f"🚀 [PROCESO] Iniciando compilación de evidencia | Tarea: {tarea_id} | Proyecto: {marca}")
        
        # Verificación de archivos (Seguridad de Datos)
        if not os.path.exists(ruta_audio):
            logging.error("❌ Audio no encontrado.")
            return {"status": "ERROR", "mensaje": "Audio no encontrado."}
        
        if not os.path.exists(ruta_imagen):
            logging.error("❌ Imagen de la RTX 3050 no encontrada. Abortando render.")
            return {"status": "ERROR", "mensaje": "Imagen no encontrada."}

        config = self.formatos.get(marca, self.formatos["default"])
        resolucion = config["resolucion"]
        ruta_salida = os.path.join(self.output_dir, f"video_{tarea_id}.mp4")

        try:
            # CARGA DE ASSETS
            audio_clip = AudioFileClip(ruta_audio)
            
            # CAMBIO CLAVE: Ya no usamos ColorClip. Usamos la imagen generada por la IA.
            video_clip = ImageClip(ruta_imagen).set_duration(audio_clip.duration)
            
            # Ajuste de tamaño para evitar errores de FFmpeg
            video_clip = video_clip.resize(newsize=resolucion)
            
            # ENSAMBLE FINAL
            video_final = video_clip.set_audio(audio_clip)
            
            # RENDERIZADO (Configurado para velocidad máxima)
            video_final.write_videofile(
                ruta_salida, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac", 
                preset="ultrafast", 
                logger=None
            )
            
            # LIMPIEZA DE MEMORIA VRAM/RAM
            audio_clip.close()
            video_clip.close()
            video_final.close()
            
            logging.info(f"✅ [ÉXITO] Video generado correctamente en: {ruta_salida}")
            return {"status": "SUCCESS", "ruta_video": ruta_salida}

        except Exception as e:
            logging.error(f"❌ [FALLA CRÍTICA] Error en el ensamble: {str(e)}")
            return {"status": "ERROR", "mensaje": str(e)}
