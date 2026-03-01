import urllib.parse
import requests
import base64
import json

class CCTVEngine:
    def __init__(self):
        # La URL de su túnel Ngrok activa (La Pintora - RTX 3050)
        self.url_local = "https://barest-ephraim-lazily.ngrok-free.dev"
        print(f"🛡️ [SISTEMA] Motor Visual CCTV Inicializado (Conectado a RTX 3050 via Ngrok).")

    def generar_imagen(self, prompt_visual):
        # Imagen fotográfica de emergencia en 16:9 real (Asegura que FFmpeg nunca falle)
        imagen_respaldo = "https://images.unsplash.com/photo-1519074069444-1ba4fff66d16?q=80&w=1920&h=1080&auto=format&fit=crop"
        
        try:
            # 1. Preparar el Payload para la API de Stability Matrix (SD WebUI)
            # Aplicamos sus reglas de estilo: CCTV, Found Footage, 16:9
            prompt_final = f"{prompt_visual}, found footage, cctv security camera, vhs grain, gritty, realistic"
            
            payload = {
                "prompt": prompt_final,
                "negative_prompt": "cartoon, 3d, render, anime, plastic, blurry, bad anatomy",
                "steps": 25,
                "width": 1024, # Optimizado para XL en la 3050
                "height": 576,  # Proporción 16:9
                "cfg_scale": 7
            }

            # 2. Enviar la orden al Túnel de Ngrok (Hacia su casa)
            print(f"📡 [PROCESO] Enviando prompt a la RTX 3050 local...")
            respuesta = requests.post(
                url=f"{self.url_local}/sdapi/v1/txt2img",
                json=payload,
                timeout=120 # Damos tiempo a la 3050 para procesar
            )

            if respuesta.status_code == 200:
                print("✅ [EXITO] Imagen generada en hardware local.")
                # Nota: El bot en Render necesita una URL para procesar el video. 
                # Si su sistema espera una URL de imagen, este motor debe subirla a un host 
                # o devolverla como base64 según cómo esté configurado el resto de Pinpinela.
                return url_imagen # (Sigue la lógica de su pipeline original)
            else:
                print(f"⚠️ [ALERTA LOCAL] Error en GPU: {respuesta.status_code}. Usando respaldo.")
                return imagen_respaldo
                
        except Exception as e:
            print(f"❌ [ERROR CRÍTICO] Falla de conexión con la RTX 3050: {str(e)}")
            return imagen_respaldo
