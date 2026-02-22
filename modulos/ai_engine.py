import google.generativeai as genai
import os
import time

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        # Variables de Telemetría (Adición)
        self.ultima_latencia = 0.0
        self.tokens_consumidos = 0

    def ejecutar_failover(self, prompt):
        modelos_disponibles = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        
        for nombre_modelo in modelos_disponibles:
            try:
                tiempo_inicio = time.time()
                model = genai.GenerativeModel(nombre_modelo)
                response = model.generate_content(prompt)
                tiempo_fin = time.time()
                
                if response and response.text:
                    # Registro de telemetría en caso de éxito
                    self.ultima_latencia = round(tiempo_fin - tiempo_inicio, 2)
                    try:
                        self.tokens_consumidos += response.usage_metadata.total_token_count
                    except:
                        pass # Bypass si la API no devuelve los metadatos en este intento
                        
                    return {'resultado_ia': response.text}
            except Exception as e:
                print(f"Falla de cuota en {nombre_modelo}: {str(e)}")
                continue 
        
        self.ultima_latencia = 0.0
        return {'error': 'Saturación en todos los modelos. Requiere pausa táctica o actualizar API Key.'}
    
    def obtener_telemetria(self):
        return {
            'latencia': self.ultima_latencia,
            'tokens': self.tokens_consumidos,
            'estado_api': 'STABLE' if self.api_key else 'OFFLINE'
        }
