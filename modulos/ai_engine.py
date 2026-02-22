import google.generativeai as genai
import os

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def ejecutar_failover(self, prompt):
        # Bucle de supervivencia estricto
        modelos_disponibles = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        
        for nombre_modelo in modelos_disponibles:
            try:
                model = genai.GenerativeModel(nombre_modelo)
                response = model.generate_content(prompt)
                if response and response.text:
                    return {'resultado_ia': response.text}
            except Exception as e:
                print(f"Falla de cuota en {nombre_modelo}: {str(e)}")
                continue 
        
        return {'error': 'Saturación en todos los modelos. Requiere pausa táctica.'}
