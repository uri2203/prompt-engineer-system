import google.generativeai as genai
from modulos.boveda import BovedaManager
import base64

class CCTVEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        # ADN Visual: La Viuda (Silo Hermético)
        self.estetica_base = "CCTV security camera footage, liminal space, psychological horror, forensic realism, low light, grainy, vhs glitch, realistic, photorealistic."
        self.negative_prompt = "3d render, illustration, monsters, gore, blood, cinematic lighting, professional photography, oversaturated, clean, text, watermark"

    def generar_imagen(self, prompt_visual):
        llaves = self.boveda.obtener_llaves()
        if not llaves:
            return "ERROR CRÍTICO: No hay API Keys cargadas en la Bóveda ni en el Entorno."
        
        # Inyectamos la estética estricta y limitantes al prompt de la IA de texto
        prompt_maestro = f"{self.estetica_base} {prompt_visual}. Avoid: {self.negative_prompt}"
        errores_detallados = []

        for index, key in enumerate(llaves):
            try:
                genai.configure(api_key=key)
                # Invocamos el motor visual nativo de Google
                imagen_model = genai.ImageGenerationModel("imagen-3.0-generate-001")
                
                # Renderizado estricto a 16:9 panorámico
                resultado = imagen_model.generate_images(
                    prompt=prompt_maestro,
                    number_of_images=1,
                    aspect_ratio="16:9",
                    output_mime_type="image/jpeg"
                )
                
                if resultado.images:
                    # Empaquetado Base64 para inyección directa en el frontend (sin uso de disco local)
                    imagen_b64 = base64.b64encode(resultado.images[0].image.image_bytes).decode('utf-8')
                    return f"data:image/jpeg;base64,{imagen_b64}"
                else:
                    errores_detallados.append(f"> Tanque {index + 1}: El servidor de Google no devolvió datos visuales.")
                    
            except Exception as e:
                mensaje_error = str(e).replace(key, f"[*TANQUE_{index+1}*]")
                if "429" in mensaje_error:
                    errores_detallados.append(f"> Tanque {index + 1}: CUOTA AGOTADA (429)")
                else:
                    errores_detallados.append(f"> Tanque {index + 1}: {mensaje_error}")
                continue
                
        return "ERROR DE RENDERIZADO VISUAL (GOOGLE IMAGEN):\n" + "\n".join(errores_detallados)
