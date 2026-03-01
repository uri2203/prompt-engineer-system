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
            "prompt": f"{prompt_visual}, realistic cctv, night vision, high quality",
            "negative_prompt": "cartoon, low quality, drawing",
            "steps": 12,      # BAJAMOS DE 20 A 12 (Esto ahorrará casi un minuto)
            "width": 640,     # BAJAMOS UN POCO LA RESOLUCIÓN
            "height": 360,
            "cfg_scale": 7
        }

        try:
            logging.info(f"📡 [GPU] Generando imagen equilibrada...")
            response = requests.post(
                f"{self.url_tunnel}/sdapi/v1/txt2img", 
                json=payload, 
                timeout=50 # Render aguanta hasta 50-60 seg en algunos casos
            )
            
            if response.status_code == 200:
                data = response.json()
                img_b64 = data['images'][0]
                return f"data:image/png;base64,{img_b64}"
            return "ERROR_TIMEOUT_GPU"
        except Exception as e:
            return "ERROR_CONEXION"
