import urllib.parse
import requests

class CCTVEngine:
    def __init__(self):
        print("🛡️ [SISTEMA] Motor Visual CCTV Inicializado (Modo 16:9 + Failover Activo).")

    def generar_imagen(self, prompt_visual):
        # Imagen fotográfica de emergencia en 16:9 real (Asegura que FFmpeg nunca falle)
        imagen_respaldo = "https://images.unsplash.com/photo-1519074069444-1ba4fff66d16?q=80&w=1920&h=1080&auto=format&fit=crop"
        
        try:
            # 1. Purgar longitud extrema: Evita el colapso 530 de servidores URL
            prompt_limpio = prompt_visual[:200]
            prompt_enriquecido = f"{prompt_limpio}, highly detailed, photorealistic, 8k, cinematic lighting"
            prompt_seguro = urllib.parse.quote(prompt_enriquecido)
            
            # 2. Enlace al motor de generación
            url_imagen = f"https://image.pollinations.ai/prompt/{prompt_seguro}?width=1920&height=1080&nologo=true"
            
            # 3. Inspección en Nube (Radar): Verificamos si Pollinations responde antes de enviarlo al Nodo local
            respuesta = requests.head(url_imagen, timeout=8)
            
            if respuesta.status_code == 200:
                return url_imagen
            else:
                print("⚠️ [ALERTA CLOUD] Pollinations saturado (Error 530). Inyectando imagen de respaldo táctico.")
                return imagen_respaldo
                
        except Exception as e:
            print(f"❌ [ERROR CLOUD] Falla crítica en API Visual: {str(e)}")
            return imagen_respaldo
