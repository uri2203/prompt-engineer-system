import google.generativeai as genai
import os

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def procesar(self, request_data, adn_db):
        mod_id = request_data.get('modulo_id')
        d = request_data.get('datos', {})
        adn_completo = adn_db.cargar_todo()
        
        # MÓDULO 1: TRADUCTOR UNIVERSAL [cite: 1]
        if mod_id == 'mod_1':
            prompt = (f"[IDENTIDAD]: Actúa como un {d.get('rol')}.\n"
                      f"[CONTEXTO]: {d.get('contexto')}.\n"
                      f"[TAREA]: {d.get('texto')}.\n"
                      f"[RESTRICCIONES]: Profesionalismo ejecutivo. Cero relleno.")

        # MÓDULO 2: GUIONES [cite: 37]
        elif mod_id == 'mod_2':
            adn = adn_completo.get(d.get('marca'), {})
            prompt = (f"[IDENTIDAD Y TONO]: {adn.get('identidad')}.\n"
                      f"[CONTEXTO]: Reglas: {adn.get('reglas_duras')}.\n"
                      f"[TAREA]: Guion de {d.get('longitud')} sobre {d.get('premisa')}.")

        # Bucle de Failover Profesional
        for m in ['gemini-1.5-pro', 'gemini-1.5-flash']:
            try:
                model = genai.GenerativeModel(m)
                return {'resultado_ia': model.generate_content(prompt).text}
            except: continue
        return {'error': 'Saturación total de cuota.'}
