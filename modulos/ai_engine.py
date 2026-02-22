import google.generativeai as genai
import os

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key: genai.configure(api_key=self.api_key)

    def procesar(self, request_data, adn_db):
        mod_id = request_data.get('modulo_id')
        d = request_data.get('datos', {})
        
        # [SOURCE 12] ESTRUCTURA DEL PROMPT MÓDULO 1
        if mod_id == 'mod_1':
            prompt = (f"[IDENTIDAD]: Actúa como un {d.get('rol')}.\n"
                      f"[CONTEXTO]: Considera los siguientes datos como base inamovible: {d.get('contexto')}.\n"
                      f"[TAREA]: Ejecuta la siguiente orden: {d.get('texto')}.\n"
                      f"[RESTRICCIONES]: Actúa con profesionalismo ejecutivo. Sé directo y estratégico. Cero relleno.\n"
                      f"[FORMATO DE SALIDA]: Entrega el resultado estrictamente como {d.get('formato')}.")
        
        # [SOURCE 49] ESTRUCTURA DEL PROMPT MÓDULO 2
        elif mod_id == 'mod_2':
            adn = adn_db.cargar_todo().get(d.get('marca'), {})
            prompt = (f"[IDENTIDAD Y TONO]: Eres un guionista experto en retención. Escribe bajo este arquetipo: {adn.get('tono')}.\n"
                      f"[CONTEXTO DE MARCA]: Respeta los siguientes límites: {adn.get('reglas')}.\n"
                      f"[TAREA]: Desarrolla un guion de {d.get('longitud')} basado en: {d.get('premisa')}.\n"
                      f"[ESTRUCTURA]: Aplica Super Retención. Prohibido iniciar con saludos. La primera línea debe atacar la curiosidad.\n"
                      f"[FORMATO DE SALIDA]: Entrega el guion dividido por bloques visuales lógicos.")

        # Bucle de Failover
        for m in ['gemini-1.5-pro', 'gemini-1.5-flash']:
            try:
                model = genai.GenerativeModel(m)
                return {'resultado_ia': model.generate_content(prompt).text}
            except: continue
        return {'error': 'Error de cuota total.'}
