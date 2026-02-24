import requests
import base64
from modulos.boveda import BovedaManager

class CCTVEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        # ADN Visual: La Viuda (Silo Hermético)
        self.estetica_base = "CCTV security camera footage, liminal space, psychological horror, forensic realism, low light, grainy, vhs glitch, realistic, photorealistic. Strictly 16:9 aspect ratio."
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
                # Bypass REST Directo hacia el modelo unificado 2.5 Flash
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
                headers = {"Content-Type": "application/json"}
                
                # Payload configurado para modalidad visual nativa
                payload = {
                    "contents": [{"parts": [{"text": prompt_maestro}]}],
                    "generationConfig": {
                        "responseModalities": ["IMAGE"]
                    }
                }
                
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    try:
                        # Extraemos la imagen codificada en Base64 de la matriz de partes
                        partes = data['candidates'][0]['content']['parts']
                        imagen_b64 = ""
                        for part in partes:
                            if 'inlineData' in part:
                                imagen_b64 = part['inlineData']['data']
                                break
                        
                        if imagen_b64:
                            return f"data:image/jpeg;base64,{imagen_b64}"
                        else:
                            errores_detallados.append(f"> Tanque {index + 1}: El servidor no devolvió la cadena Base64 en inlineData.")
                    except (KeyError, IndexError):
                        errores_detallados.append(f"> Tanque {index + 1}: El servidor de Google devolvió una estructura JSON inesperada.")
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
