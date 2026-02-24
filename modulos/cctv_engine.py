import base64
from modulos.boveda import BovedaManager

class CCTVEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        # ADN Visual: La Viuda (Silo Hermético)
        self.estetica_base = "CCTV security camera footage, liminal space, psychological horror, forensic realism, low light, grainy, vhs glitch, realistic, photorealistic. Strictly 16:9 aspect ratio."
        self.negative_prompt = "3d render, illustration, monsters, gore, blood, cinematic lighting, professional photography, oversaturated, clean, text, watermark"

    def generar_imagen(self, prompt_visual):
        # MODO DE SIMULACIÓN (MOCKING) ACTIVADO
        # El sistema evade conexiones externas defectuosas para garantizar la continuidad del Pipeline.
        
        try:
            # Cadena Base64 real de una imagen de calibración (Píxel oscuro).
            # El frontend (CSS) se encargará de escalarla al formato 16:9 de la interfaz.
            mock_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
            
            # Retorno instantáneo y garantizado sin consumo de red ni de cuotas.
            return f"data:image/png;base64,{mock_b64}"
            
        except Exception as e:
            return f"ERROR DE RENDERIZADO VISUAL (MOCK LOCAL) -> {str(e)}"
