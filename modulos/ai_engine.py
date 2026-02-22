import google.generativeai as genai
import os
import time

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        # Historial de memoria para las gráficas (20 puntos de datos)
        self.historial_latencia = [0.0] * 20
        self.historial_tokens = [0] * 20
        self.tokens_totales = 0

    def ejecutar_failover(self, prompt):
        modelos_disponibles = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        
        for nombre_modelo in modelos_disponibles:
            try:
                tiempo_inicio = time.time()
                model = genai.GenerativeModel(nombre_modelo)
                response = model.generate_content(prompt)
                tiempo_fin = time.time()
                
                if response and response.text:
                    latencia = round(tiempo_fin - tiempo_inicio, 2)
                    tokens_peticion = 0
                    try:
                        tokens_peticion = response.usage_metadata.total_token_count
                    except:
                        pass # Bypass si la API oculta los metadatos
                        
                    # Actualización matemática de los historiales
                    self.tokens_totales += tokens_peticion
                    self.historial_latencia.append(latencia)
                    self.historial_latencia.pop(0) # Elimina el dato más viejo
                    self.historial_tokens.append(tokens_peticion)
                    self.historial_tokens.pop(0)
                        
                    return {'resultado_ia': response.text}
            except Exception as e:
                print(f"Falla de cuota en {nombre_modelo}: {str(e)}")
                continue 
        
        return {'error': 'Saturación en todos los modelos. Requiere pausa táctica o actualizar API Key.'}
    
    def obtener_telemetria(self):
        return {
            'estado_api': 'STABLE' if self.api_key else 'OFFLINE',
            'tokens_totales': self.tokens_totales,
            'historial_latencia': self.historial_latencia,
            'historial_tokens': self.historial_tokens,
            'latencia_actual': self.historial_latencia[-1]
        }
