import requests
import base64
from modulos.boveda import BovedaManager

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
                # Bypass REST Directo (Inmune a versiones del SDK)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={key}"
                headers = {"Content-Type": "application/json"}
                
                # Payload estándar para la API Visual de Google
                payload = {
                    "instances": [{"prompt": prompt_maestro}],
                    "parameters": {
                        "sampleCount": 1,
                        "aspectRatio": "16:9"
                    }
                }
                
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'predictions' in data and len(data['predictions']) > 0:
                        # Extraemos la imagen codificada en Base64 devuelta por el servidor REST
                        imagen_b64 = data['predictions'][0].get('bytesBase64Encoded', '')
                        if imagen_b64:
                            return f"data:image/jpeg;base64,{imagen_b64}"
                        else:
                            errores_detallados.append(f"> Tanque {index + 1}: El servidor no devolvió la cadena Base64.")
                    else:
                        errores_detallados.append(f"> Tanque {index + 1}: El servidor de Google no devolvió datos visuales.")
                else:
                    error_json = response.json()
                    error_msg = error_json.get('error', {}).get('message', response.text)
                    
                    if "429" in str(response.status_code):
                        errores_detallados.append(f"> Tanque {index + 1}: CUOTA AGOTADA (429 REST)")
                    else:
                        errores_detallados.append(f"> Tanque {index + 1}: ERROR REST -> {error_msg}")
                    
            except Exception as e:
                errores_detallados.append(f"> Tanque {index + 1}: FALLA LOCAL -> {str(e)}")
                continue
                
        return "ERROR DE RENDERIZADO VISUAL (REST BYPASS):\n" + "\n".join(errores_detallados)
