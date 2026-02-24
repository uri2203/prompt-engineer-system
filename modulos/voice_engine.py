import requests
import base64
from modulos.boveda import BovedaManager

class VoiceEngine:
    def __init__(self):
        self.boveda = BovedaManager()

    def generar_audio(self, texto_locucion, marca="La Viuda"):
        datos_boveda = self.boveda.obtener_datos()
        api_key = datos_boveda.get('voice_api', '')

        # ENRUTADOR DINÁMICO DE SILOS HERMÉTICOS
        if marca == "Monkygraff":
            # Silo: Documental Geopolítico / Análisis serio
            voice_id = "PHKlYg202ODwQRa3Fxuo" 
        else:
            # Silo: La Viuda (Por defecto) / Terror Psicológico, tono bajo y confidencial
            voice_id = "GTY55jD77hLBRrnQOhNk" 

        if not api_key:
            # MODO DE SIMULACIÓN (MOCKING) ACTIVADO
            mock_wav_b64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="
            return f"data:audio/wav;base64,{mock_wav_b64}"

        # BYPASS HACIA PRODUCCIÓN (ELEVENLABS REST API)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        # Configuración acústica inyectada
        payload = {
            "text": texto_locucion,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.35, 
                "similarity_boost": 0.85,
                "style": 0.50,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                audio_b64 = base64.b64encode(response.content).decode('utf-8')
                return f"data:audio/mpeg;base64,{audio_b64}"
            else:
                return f"ERROR DE RENDERIZADO VOCAL (HTTP {response.status_code}): {response.text}"
                
        except Exception as e:
            return f"ERROR CRÍTICO LOCAL (VOZ) -> {str(e)}"
