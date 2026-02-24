import requests
import base64
import urllib.parse
from modulos.boveda import BovedaManager

class CCTVEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        # ADN Visual: La Viuda (Silo Hermético)
        self.estetica_base = "CCTV security camera footage, liminal space, psychological horror, forensic realism, low light, grainy, vhs glitch, realistic, photorealistic. Strictly 16:9 aspect ratio."
        self.negative_prompt = "3d render, illustration, monsters, gore, blood, cinematic lighting, professional photography, oversaturated, clean, text, watermark"

    def generar_imagen(self, prompt_visual):
        # Inyectamos la estética estricta y limitantes al prompt de la IA de texto
        prompt_maestro = f"{self.estetica_base} {prompt_visual}. Avoid: {self.negative_prompt}"
        errores_detallados = []

        try:
            # HARD BYPASS: Enrutamiento a infraestructura abierta (Pollinations)
            # Evade el error 402 (Replicate) y el bloqueo de modalidad (Google)
            prompt_codificado = urllib.parse.quote(prompt_maestro)
            
            # Forzamos resolución panorámica estricta 1920x1080 (16:9)
            url = f"https://image.pollinations.ai/prompt/{prompt_codificado}?width=1920&height=1080&nologo=true"
            
            # Petición HTTP pura sin autenticación ni barreras de pago
            response = requests.get(url)
            
            if response.status_code == 200:
                # Empaquetamos los bytes en Base64 para inyección directa en el frontend
                imagen_b64 = base64.b64encode(response.content).decode('utf-8')
                return f"data:image/jpeg;base64,{imagen_b64}"
            else:
                errores_detallados.append(f"> BYPASS FALLIDO: El servidor abierto rechazó la conexión (HTTP {response.status_code}).")
                    
        except Exception as e:
            errores_detallados.append(f"> ERROR CRÍTICO LOCAL -> {str(e)}")
                
        return "ERROR DE RENDERIZADO VISUAL (HARD BYPASS):\n" + "\n".join(errores_detallados)
