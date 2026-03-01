import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        # 🔗 ENLACE DE SU TÚNEL ACTIVO (SSH localhost.run)
        self.url_tunnel = "https://969d8f9d4291e9.lhr.life" 
        self.temp_dir = os.path.join(os.getcwd(), "workspace_temp", "imagenes")
        
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
            
        logging.info(f"🛡️ [SISTEMA] Motor CCTV conectado vía SSH: {self.url_tunnel}")

    def generar_imagen(self, prompt_visual, tarea_id):
        ruta_guardado = os.path.join(self.temp_dir, f"cctv_{tarea_id}.png")
        
        # Configuración optimizada para generar el CCTV en su RTX 3050
        payload = {
            "prompt": f"{prompt_visual}, cctv footage, night vision green, grainy, realistic",
            "negative_prompt": "cartoon, bright colors, drawing, illustration",
            "steps": 25,
            "width": 1024,
            "height": 576,
            "cfg_scale": 7
        }

        try:
            logging.info(f"📡 [FASE 2] Solicitando renderizado a GPU local...")
            
            # Petición directa a su túnel SSH sin intermediarios
            response = requests.post(
                f"{self.url_tunnel}/sdapi/v1/txt2img", 
                json=payload, 
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                # Guardamos la imagen para que el motor de video la ensamble
                with open(ruta_guardado, "wb") as f:
                    f.write(base64.b64decode(data['images'][0]))
                
                logging.info(f"✅ [ÉXITO] Imagen recibida y guardada en Render.")
                return ruta_guardado
            else:
                logging.error(f"❌ [FALLO GPU] La tarjeta respondió con error: {response.status_code}")
                return None

        except Exception as e:
            logging.error(f"❌ [FALLO CONEXIÓN] El túnel no responde: {str(e)}")
            return None
