import time

class CCTVEngine:
    def __init__(self):
        pass

    def empaquetar_tarea(self, prompt_visual):
        # Creamos la receta con calidad MÁXIMA
        return {
            "id": str(int(time.time())),
            "tipo": "IMAGEN_CCTV",
            "prompt": f"{prompt_visual}, realistic cctv footage, night vision green, grainy, 4k, cinematic lighting",
            "negative_prompt": "cartoon, bright colors, drawing, illustration, low quality",
            "steps": 30,      # Calidad profesional
            "width": 1024,    # Resolución completa
            "height": 576,    # 16:9 Real
            "cfg_scale": 7
        }
