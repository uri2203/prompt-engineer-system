import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        # Jala el link de Render para no editar archivos cada vez
        self.url_tunnel = os.environ.get("SD_URL", "https://5861cbcf9596bfb6aa.gradio.live")
        logging.info(f"🛡️ [SISTEMA] Motor CCTV conectado a: {self.url_tunnel}")

    def generar_imagen(self, prompt_visual):
        payload = {
            "prompt": f"{prompt_visual}, cctv footage, grainy",
            "negative_prompt": "cartoon",
            "steps": 10,   # Bajamos pasos para que sea ultra rápido
            "width": 384,  # Tamaño pequeño para brincar el timeout
            "height": 384,
            "cfg_scale": 5
        }

        try:
            logging.info(f"📡 [GPU] Solicitando renderizado express...")
            # Le damos 40 segundos máximo para responder
            response = requests.post(
                f"{self.url_tunnel}/sdapi/v1/txt2img", 
                json=payload, 
                timeout=40 
            )
            
            if response.status_code == 200:
                data = response.json()
                img_b64 = data['images'][0]
                logging.info(f"✅ [ÉXITO] Imagen enviada.")
                return f"data:image/png;base64,{img_b64}"
            else:
                return "ERROR_TIMEOUT_GPU"

        except Exception as e:
            return "ERROR_CONEXION_PERDIDA"
