import google.generativeai as genai
import os

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key: genai.configure(api_key=self.api_key)

    def procesar(self, request_data, adn_db):
        mod_id = request_data.get('modulo_id')
        d = request_data.get('datos', {})
        adn_completo = adn_db.cargar_todo()
        
        # MÓDULO 1: TRADUCTOR UNIVERSAL [cite: 1]
        if mod_id == 'mod_1':
            prompt = (f"[IDENTIDAD]: Actúa como un {d.get('rol')}. [cite: 14]\n"
                      f"[CONTEXTO]: {d.get('contexto')}. [cite: 15]\n"
                      f"[TAREA]: {d.get('texto')}. [cite: 16]\n"
                      f"[RESTRICCIONES]: Profesionalismo ejecutivo. Cero relleno. [cite: 17]\n"
                      f"[FORMATO DE SALIDA]: {d.get('formato')}. [cite: 19]")

        # MÓDULO 2: INGENIERÍA DE GUIONES [cite: 37]
        elif mod_id == 'mod_2':
            adn = adn_completo.get(d.get('marca'), {})
            prompt = (f"[IDENTIDAD Y TONO]: Arquetipo {adn.get('tono')}. [cite: 51]\n"
                      f"[CONTEXTO DE MARCA]: Reglas: {adn.get('reglas')}. [cite: 52]\n"
                      f"[TAREA]: Guion de {d.get('longitud')} sobre {d.get('premisa')}. [cite: 53]\n"
                      f"[ESTRUCTURA]: {d.get('framework')}. Prohibido saludar. [cite: 47, 54]")

        # MÓDULO 5: VENTAS UGC [cite: 142]
        elif mod_id == 'mod_5':
            prompt = (f"[ESTRATEGIA DE VENTAS]: {d.get('gatillo')}. [cite: 157, 158]\n"
                      f"[SECUENCIA]: Bloque {d.get('bloque')}, Duración {d.get('duracion')}. [cite: 160]\n"
                      f"[FASE VISUAL]: {d.get('modalidad')}. Render 4K. [cite: 161, 163]")

        # Bucle de Failover (Supervivencia)
        for m in ['gemini-1.5-pro', 'gemini-1.5-flash']:
            try:
                model = genai.GenerativeModel(m)
                return {'resultado_ia': model.generate_content(prompt).text}
            except: continue
        return {'error': 'Saturación de modelos.'}
