import requests
import base64
import os
import logging
import time

class CCTVEngine:
    def __init__(self):
        # 🔗 ENLACE ACTIVO HACIA SU RTX 3050 (Gradio Live)
        self.url_tunnel = "https://5861cbcf9596bfb6aa.gradio.live" 
        self.temp_dir = os.path.join(os.getcwd(), "static", "imagenes")
        
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
            
        logging.info(f"🛡️ [SISTEMA] Motor CCTV conectado vía Gradio: {self.url_tunnel}")

    def generar_imagen(self, prompt_visual):
        # Generamos un ID de tiempo para que el archivo no se pierda
        tarea_id = int(time.time())
        nombre_archivo = f"cctv_{tarea_id}.png"
        ruta_guardado = os.path.join(self.temp_dir, nombre_archivo)
        
        payload = {
            "prompt": f"{prompt_visual}, cctv footage, night vision green, grainy, realistic",
            "negative_prompt": "cartoon, bright colors, drawing, illustration",
            "steps": 20,
            "width": 1024,
            "height": 576,
            "cfg_scale": 7
        }

        try:
            logging.info(f"📡 [GPU] Solicitando renderizado local...")
            response = requests.post(
                f"{self.url_tunnel}/sdapi/v1/txt2img", 
                json=payload, 
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                with open(ruta_guardado, "wb") as f:
                    f.write(base64.b64decode(data['images'][0]))
                
                logging.info(f"✅ [ÉXITO] Imagen guardada.")
                # Retornamos la ruta para que Pinpinela la muestre
                return f"/static/imagenes/{nombre_archivo}"
            else:
                return f"ERROR_GPU_{response.status_code}"

        except Exception as e:
            logging.error(f"❌ [FALLO] {str(e)}")
            return f"ERROR_CONEXION"
