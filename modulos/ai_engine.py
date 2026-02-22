import google.generativeai as genai
import os

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key: genai.configure(api_key=self.api_key)

    def procesar(self, request_data, adn_db):
        mod_id = request_data.get('modulo_id')
        d = request_data.get('datos', {})
        
        if mod_id == 'mod_1':
            prompt = (f"[IDENTIDAD]: Actúa como un {d.get('rol')}.\n"
                      f"[CONTEXTO]: {d.get('contexto')}.\n"
                      f"[TAREA]: {d.get('texto')}.\n"
                      f"[RESTRICCIONES]: Profesionalismo ejecutivo. Cero relleno.")
        # ... lógica de otros módulos
        
        for m in ['gemini-1.5-pro', 'gemini-1.5-flash']:
            try:
                model = genai.GenerativeModel(m)
                return {'resultado_ia': model.generate_content(prompt).text}
            except: continue
        return {'error': 'Saturación total.'}
