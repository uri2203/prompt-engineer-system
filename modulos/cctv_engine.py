import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        self.url_tunnel = os.environ.get("SD_URL", "https://5861cbcf9596bfb6aa.gradio.live")
        logging.info(f"🛡️ [SISTEMA] Motor CCTV conectado a: {self.url_tunnel}")

    def generar_imagen(self, prompt_visual):
        payload = {
            "prompt": f"{prompt_visual}, cctv footage, grainy",
            "negative_prompt": "cartoon",
            "steps": 5,      # ULTRA RÁPIDO (5 pasos)
            "width": 256,    # MINI IMAGEN (256px) para que vuele
            "height": 256,
            "cfg_scale": 5
        }

        try:
            logging.info(f"📡 [GPU] Disparo express iniciado...")
            response = requests.post(
                f"{self.url_tunnel}/sdapi/v1/txt2img", 
                json=payload, 
                timeout=25 # Si no llega en 25 seg, abortamos
            )
            
            if response.status_code == 200:
                data = response.json()
                img_b64 = data['images'][0]
                logging.info(f"✅ [ÉXITO] Imagen enviada al frontend.")
                return f"data:image/png;base64,{img_b64}"
            return "ERROR_GPU_LENTA"
        except Exception as e:
            return "ERROR_CONEXION"
