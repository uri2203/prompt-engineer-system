import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        # 🔗 LINK DE SU TÚNEL SSH (EXTRAÍDO DE SU CAPTURA)
        self.url_tunnel = "https://969d8f9d4291e9.lhr.life" 
        self.temp_dir = os.path.join(os.getcwd(), "workspace_temp", "imagenes")
        
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
            
        logging.info(f"🛡️ [SISTEMA] Motor CCTV conectado al túnel: {self.url_tunnel}")

    def generar_imagen(self, prompt_visual, tarea_id):
        ruta_guardado = os.path.join(self.temp_dir, f"cctv_{tarea_id}.png")
        
        # Configuración optimizada para su RTX 3050
        payload = {
            "prompt": f"{prompt_visual}, cctv found footage, realistic, vhs grain",
            "negative_prompt": "bright colors, cartoon, drawing, high saturation",
            "steps": 25,
            "width": 1024,
            "height": 576,
            "cfg_scale": 7
        }

        try:
            logging.info(f"📡 [FASE 2] Solicitando render a GPU local vía SSH...")
            
            # Conexión directa al túnel de su terminal
            response = requests.post(
                f"{self.url_tunnel}/sdapi/v1/txt2img", 
                json=payload, 
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                # Guardamos la imagen procesada por su tarjeta en el servidor
                with open(ruta_guardado, "wb") as f:
                    f.write(base64.b64decode(data['images'][0]))
                
                logging.info(f"✅ [ÉXITO] Imagen recibida y guardada.")
                return ruta_guardado
            else:
                logging.error(f"❌ [ERROR GPU] Código de respuesta: {response.status_code}")
                return None

        except Exception as e:
            logging.error(f"❌ [ERROR CONEXIÓN] El túnel no responde: {str(e)}")
            return None
