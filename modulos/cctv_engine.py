import requests
import base64
import os
import logging

class CCTVEngine:
    def __init__(self):
        # SU LINK DE NGROK (Asegúrese de que sea el mismo de su ventana negra)
        self.url_ngrok = "https://barest-ephraim-lazily.ngrok-free.dev"
        self.temp_dir = os.path.join(os.getcwd(), "workspace_temp", "imagenes")
        os.makedirs(self.temp_dir, exist_ok=True)

    def generar_imagen(self, prompt_visual, tarea_id):
        ruta_guardado = os.path.join(self.temp_dir, f"cctv_{tarea_id}.png")
        
        # 🛡️ SALTO DE MURO: Evita la página de advertencia de Ngrok
        headers = {"ngrok-skip-browser-warning": "69420"}
        
        payload = {
            "prompt": f"{prompt_visual}, found footage, cctv security camera, realistic, grainy vhs",
            "steps": 25,
            "width": 1024,
            "height": 576
        }

        try:
            logging.info(f"📡 Conectando con RTX 3050 via Ngrok...")
            response = requests.post(f"{self.url_ngrok}/sdapi/v1/txt2img", json=payload, headers=headers, timeout=80)
            
            if response.status_code == 200:
                r = response.json()
                with open(ruta_guardado, "wb") as f:
                    f.write(base64.b64decode(r['images'][0]))
                logging.info(f"✅ Imagen recibida y guardada: {ruta_guardado}")
                return ruta_guardado
            else:
                logging.error(f"❌ La GPU devolvió error: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"❌ Error de enlace: {str(e)}")
            return None
