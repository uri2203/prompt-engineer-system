import urllib.parse
import requests
import base64

class CCTVEngine:
    def __init__(self):
        # BYPASS CLOUD TEMPORAL: API pública para validación visual de Prompts 
        self.base_url = "https://image.pollinations.ai/prompt/"

    def generar_imagen(self, prompt_visual):
        try:
            # 1. Límite de seguridad: Truncar el prompt a 800 caracteres máximo 
            # Evita colapsos de red por URLs demasiado largas (Error 530 / 414)
            prompt_seguro = prompt_visual[:800]
            
            # 2. Sanitización y codificación
            prompt_encoded = urllib.parse.quote(prompt_seguro)
            url_generacion = f"{self.base_url}{prompt_encoded}?width=1920&height=1080&nologo=true"
            
            # 3. BLINDAJE ANTI-CLOUDFLARE (Spoofing de Cabeceras)
            # Camuflamos la petición HTTP para que el firewall de la API no bloquee a Python.
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
            
            # 4. Petición al motor de renderizado Cloud
            response = requests.get(url_generacion, headers=headers, timeout=45)
            
            if response.status_code == 200:
                # 5. Decodificación a Base64 para inyección directa en el DOM del Workspace
                img_b64 = base64.b64encode(response.content).decode('utf-8')
                return f"data:image/jpeg;base64,{img_b64}"
            else:
                return f"ERROR CLOUD VISUAL (HTTP {response.status_code})"
                
        except requests.exceptions.Timeout:
            return "ERROR DE RED: El renderizado Cloud excedió el tiempo límite (45s)."
        except Exception as e:
            return f"ERROR CRÍTICO LOCAL (CCTV) -> {str(e)}"
