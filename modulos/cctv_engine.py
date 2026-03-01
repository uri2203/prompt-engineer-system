import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        # 🔗 LINK DEL TÚNEL SSH (DE TU CAPTURA DEL QR)
        self.url_tunnel = "https://969d8f9d4291e9.lhr.life" 
        self.temp_dir = os.path.join(os.getcwd(), "workspace_temp", "imagenes")
        
        # Crear carpeta de trabajo si no existe
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
            
        logging.info(f"🛡️ [MOTOR CCTV] Enlazado a túnel SSH: {self.url_tunnel}")

    def generar_imagen(self, prompt_visual, tarea_id):
        ruta_guardado = os.path.join(self.temp_dir, f"cctv_{tarea_id}.png")
        
        # Parámetros exactos para que tu RTX 3050 trabaje sin errores
        payload = {
            "prompt": f"{prompt_visual}, cctv found footage style, realistic, grainy night vision, high contrast",
            "negative_prompt": "cartoon, painting, drawing, illustration, bright colors, saturated",
            "steps": 25,
            "width": 1024,
            "height": 576,
            "cfg_scale": 7
        }

        try:
            logging.info(f"📡 [FASE 2] Solicitando evidencia a RTX 3050 vía SSH...")
            
            # Petición directa a la API de tu Stability Matrix
            response = requests.post(
                f"{self.url_tunnel}/sdapi/v1/txt2img", 
                json=payload, 
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                # Decodificar y guardar físicamente en Render
                with open(ruta_guardado, "wb") as f:
                    f.write(base64.b64decode(data['images'][0]))
                
                logging.info(f"✅ [ÉXITO] Imagen guardada en: {ruta_guardado}")
                return ruta_guardado
            else:
                logging.error(f"❌ [FALLO GPU] La tarjeta respondió con error: {response.status_code}")
                return None

        except Exception as e:
            logging.error(f"❌ [FALLO TOTAL] Error de conexión SSH: {str(e)}")
            return None
