import urllib.parse
import requests
import base64

class CCTVEngine:
    def __init__(self):
        # BYPASS CLOUD TEMPORAL: API pública para validación visual de Prompts 
        # Esta conexión será sustituida por el túnel hacia la NVIDIA RTX 3050 en la fase final.
        self.base_url = "https://image.pollinations.ai/prompt/"

    def generar_imagen(self, prompt_visual):
        try:
            # 1. Sanitización y codificación del prompt extraído de la matriz IA
            prompt_encoded = urllib.parse.quote(prompt_visual)
            
            # 2. Inyección de parámetros estrictos (1920x1080, 16:9, fotorrealismo)
            # El parámetro 'nologo=true' evita marcas de agua.
            url_generacion = f"{self.base_url}{prompt_encoded}?width=1920&height=1080&nologo=true"
            
            # 3. Petición al motor de renderizado Cloud
            response = requests.get(url_generacion, timeout=45)
            
            if response.status_code == 200:
                # 4. Decodificación a Base64 para inyección directa en el DOM del Workspace
                img_b64 = base64.b64encode(response.content).decode('utf-8')
                return f"data:image/jpeg;base64,{img_b64}"
            else:
                return f"ERROR CLOUD VISUAL (HTTP {response.status_code})"
                
        except requests.exceptions.Timeout:
            return "ERROR DE RED: El renderizado Cloud excedió el tiempo límite (45s)."
        except Exception as e:
            return f"ERROR CRÍTICO LOCAL (CCTV) -> {str(e)}"
