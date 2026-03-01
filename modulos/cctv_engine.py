import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        # SU LINK DE NGROK ACTIVO
        self.url_ngrok = "https://barest-ephraim-lazily.ngrok-free.dev"
        self.temp_dir = os.path.join(os.getcwd(), "workspace_temp", "imagenes")
        os.makedirs(self.temp_dir, exist_ok=True)
        logging.info(f"🛡️ [SISTEMA] Motor CCTV enlazado a RTX 3050.")

    def generar_imagen(self, prompt_visual, tarea_id):
        ruta_guardado = os.path.join(self.temp_dir, f"cctv_{tarea_id}.png")
        
        # SALTO DE MURO: Ngrok pide esto para no mostrar la página de advertencia
        headers = {"ngrok-skip-browser-warning": "69420"}
        
        payload = {
            "prompt": f"{prompt_visual}, found footage, cctv security camera, vhs grain, realistic",
            "steps": 20,
            "width": 1024,
            "height": 576
        }

        try:
            # Llamada a su casa (RTX 3050)
            response = requests.post(f"{self.url_ngrok}/sdapi/v1/txt2img", json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                r = response.json()
                # Decodificar la imagen que manda su tarjeta
                with open(ruta_guardado, "wb") as f:
                    f.write(base64.b64decode(r['images'][0]))
                return ruta_guardado # Retorna la ruta real del archivo
            else:
                logging.error(f"⚠️ Error GPU: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"❌ Falla de conexión Ngrok: {str(e)}")
            return None
