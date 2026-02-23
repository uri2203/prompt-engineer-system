import os
import replicate

class CCTVEngine:
    def __init__(self):
        # ADN Visual: La Viuda (Silo Hermético)
        self.estetica_base = "CCTV security camera footage, liminal space, psychological horror, forensic realism, low light, grainy, vhs glitch, realistic, photorealistic."
        self.negative_prompt = "3d render, illustration, monsters, gore, blood, cinematic lighting, professional photography, oversaturated, clean, text, watermark"

    def generar_imagen(self, prompt_visual):
        replicate_api = os.environ.get("REPLICATE_API_TOKEN", "")
        if not replicate_api:
            return "ERROR CRÍTICO: REPLICATE_API_TOKEN no encontrado en las variables de entorno de Render."
        
        os.environ["REPLICATE_API_TOKEN"] = replicate_api
        prompt_maestro = f"{self.estetica_base} {prompt_visual}"

        try:
            # Renderizado estricto a 16:9 (1920x1080 Full HD)
            output = replicate.run(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                input={
                    "prompt": prompt_maestro,
                    "negative_prompt": self.negative_prompt,
                    "width": 1920,
                    "height": 1080,
                    "refine": "expert_ensemble_refiner",
                    "apply_watermark": False
                }
            )
            # Retorna la URL de la imagen generada
            return output[0]
        except Exception as e:
            return f"ERROR DE RENDERIZADO VISUAL: {str(e)}"
