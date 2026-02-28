import urllib.parse

class CCTVEngine:
    def __init__(self):
        print("🛡️ [SISTEMA] Motor Visual CCTV Inicializado (Modo Fotorrealismo 16:9).")

    def generar_imagen(self, prompt_visual):
        try:
            # Enriquecemos el prompt obligatoriamente para garantizar calidad suprema y fotorrealismo
            prompt_enriquecido = f"{prompt_visual}, hyperrealistic, analog photography, cinematic lighting, highly detailed, 8k resolution"
            prompt_seguro = urllib.parse.quote(prompt_enriquecido)
            
            # Conexión táctica a motor de generación directa (Devuelve un JPG puro)
            # Medidas estrictamente bloqueadas en relación 16:9 (1920x1080)
            url_imagen = f"https://image.pollinations.ai/prompt/{prompt_seguro}?width=1920&height=1080&nologo=true"
            
            # Retornamos el enlace limpio. 
            # El Frontend lo previsualizará y el Nodo Gamma local lo descargará como archivo físico.
            return url_imagen
            
        except Exception as e:
            return f"ERROR: Falla en el núcleo del Motor Visual - {str(e)}"
