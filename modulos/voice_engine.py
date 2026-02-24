import requests
import base64
from modulos.boveda import BovedaManager

class VoiceEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        # ADN Vocal: La Viuda (Silo Hermético)
        # Tono exigido: Voz latina, baja, cercana y confidencial.
        # ID de voz por defecto (Ajustar al ID de la voz clonada en ElevenLabs)
        self.voice_id = "pNInz6obbfIdGqcJhcBz" 

    def generar_audio(self, texto_locucion):
        datos_boveda = self.boveda.obtener_datos()
        api_key = datos_boveda.get('voice_api', '')

        if not api_key:
            # MODO DE SIMULACIÓN (MOCKING) ACTIVADO
            # Evita el colapso del pipeline si ElevenLabs no está configurado.
            # Retorna un archivo WAV de calibración (silencio corto codificado) para validar el frontend.
            mock_wav_b64 = "UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="
            return f"data:audio/wav;base64,{mock_wav_b64}"

        # BYPASS HACIA PRODUCCIÓN (ELEVENLABS REST API)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        # Configuración acústica inyectada para forzar suspenso y disonancia (estabilidad baja)
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
