import google.generativeai as genai
import os

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key: genai.configure(api_key=self.api_key)

    def procesar(self, request_data, adn_db):
        mod_id = request_data.get('modulo_id')
        d = request_data.get('datos', {})
        
        # MÓDULO 1: TRADUCTOR UNIVERSAL (Reglas Estrictas)
        if mod_id == 'mod_1':
            filtro = "Actúa con profesionalismo ejecutivo. Prohibido lenguaje genérico o relleno. Sé directo y estratégico. Código completo y final." [cite: 11]
            prompt = (f"[IDENTIDAD]: Actúa como un {d.get('rol')}. [cite: 14]\n"
                      f"[CONTEXTO]: Base inamovible: {d.get('contexto')}. [cite: 15]\n"
                      f"[TAREA]: {d.get('texto')}. [cite: 16]\n"
                      f"[RESTRICCIONES]: {filtro}. [cite: 17]\n"
                      f"[FORMATO DE SALIDA]: {d.get('formato')}." [cite: 19])
        # ... Resto de módulos ...

        # Bucle de Failover inyectado
        for m in ['gemini-1.5-pro', 'gemini-1.5-flash']:
            try:
                model = genai.GenerativeModel(m)
                return {'resultado_ia': model.generate_content(prompt).text}
            except: continue
        return {'error': 'Falla de cuota.'}
