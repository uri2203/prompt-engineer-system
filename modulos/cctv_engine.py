import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        # 🔗 COLOQUE AQUÍ SU LINK DE LOCALTUNNEL
        self.url_tunnel = "https://vicious-dogs-jump.loca.lt" 
        self.temp_dir = os.path.join(os.getcwd(), "workspace_temp", "imagenes")
        os.makedirs(self.temp_dir, exist_ok=True)

    def generar_imagen(self, prompt_visual, tarea_id):
        ruta_guardado = os.path.join(self.temp_dir, f"cctv_{tarea_id}.png")
        
        # Localtunnel no necesita headers raros, es conexión directa
        payload = {
            "prompt": f"{prompt_visual}, cctv found footage style, hyper-realistic, 8k, grainy night vision",
            "steps": 25,
            "width": 1024,
            "height": 576
        }

        try:
            logging.info(f"📡 Solicitando evidencia a RTX 3050 (Localtunnel)...")
            response = requests.post(f"{self.url_tunnel}/sdapi/v1/txt2img", json=payload, timeout=90)
            
            if response.status_code == 200:
                data = response.json()
                with open(ruta_guardado, "wb") as f:
                    f.write(base64.b64decode(data['images'][0]))
                logging.info(f"✅ Imagen capturada con éxito en: {ruta_guardado}")
                return ruta_guardado
            else:
                logging.error(f"❌ Error en GPU Local: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"❌ Error de conexión: {str(e)}")
            return None
