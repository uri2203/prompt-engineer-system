import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        # Jala el link directo de Render para que no tenga que editar este archivo
        self.url_tunnel = os.environ.get("SD_URL", "https://5861cbcf9596bfb6aa.gradio.live")
        logging.info(f"🛡️ [SISTEMA] Motor CCTV conectado a: {self.url_tunnel}")

    def generar_imagen(self, prompt_visual):
        payload = {
            "prompt": f"{prompt_visual}, cctv footage, night vision green, grainy, realistic",
            "negative_prompt": "cartoon, bright colors, drawing, illustration",
            "steps": 20,
            "width": 512, # Bajamos resolución para que sea instantáneo el test
            "height": 512,
            "cfg_scale": 7
        }

        try:
            logging.info(f"📡 [GPU] Solicitando renderizado local...")
            response = requests.post(
                f"{self.url_tunnel}/sdapi/v1/txt2img", 
                json=payload, 
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                img_b64 = data['images'][0]
                logging.info(f"✅ [ÉXITO] Imagen generada.")
                # Mandamos la imagen codificada directo al navegador
                return f"data:image/png;base64,{img_b64}"
            else:
                return f"ERROR_GPU_{response.status_code}"

        except Exception as e:
            logging.error(f"❌ [FALLO] {str(e)}")
            return "ERROR_CONEXION"
