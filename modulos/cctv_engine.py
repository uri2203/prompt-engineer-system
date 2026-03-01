import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        # Jala el link de Render automáticamente
        self.url_tunnel = os.environ.get("SD_URL", "https://5861cbcf9596bfb6aa.gradio.live")
        logging.info(f"🛡️ [SISTEMA] Motor CCTV conectado a: {self.url_tunnel}")

    def generar_imagen(self, prompt_visual):
        payload = {
            # El prompt ahora pide más detalle y realismo
            "prompt": f"{prompt_visual}, high quality, realistic cctv, night vision, 4k",
            "negative_prompt": "cartoon, blur, low quality, distorted, drawing",
            "steps": 20,      # SUBIMOS A 20 PASOS (Mucho más detalle)
            "width": 768,     # RESOLUCIÓN PANORÁMICA (16:9 real)
            "height": 432,
            "cfg_scale": 7    # Más fidelidad al texto
        }

        try:
            logging.info(f"📡 [GPU] Generando imagen de alta fidelidad...")
            response = requests.post(
                f"{self.url_tunnel}/sdapi/v1/txt2img", 
                json=payload, 
                timeout=45 # Le damos un poco más de tiempo de espera
            )
            
            if response.status_code == 200:
                data = response.json()
                img_b64 = data['images'][0]
                logging.info(f"✅ [ÉXITO] Imagen HD enviada.")
                return f"data:image/png;base64,{img_b64}"
            return "ERROR_GPU_LENTA"
        except Exception as e:
            return "ERROR_CONEXION"
