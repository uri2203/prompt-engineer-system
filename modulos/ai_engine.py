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
        
        prompt = ""

        # MÓDULO 1: TRADUCTOR UNIVERSAL (Zero-Shot) [cite: 1, 13]
        if mod_id == 'mod_1':
            prompt = (f"[IDENTIDAD]: Actúa como un {d.get('rol')}. [cite: 14]\n"
                      f"[CONTEXTO]: {d.get('contexto')}. [cite: 15]\n"
                      f"[TAREA]: {d.get('texto')}. [cite: 16]\n"
                      f"[RESTRICCIONES]: Actúa con profesionalismo ejecutivo. Sé directo y estratégico. Cero relleno. [cite: 17]\n"
                      f"Si generas código, debe ser funcional y completo para copiar y pegar. [cite: 18]\n"
                      f"[FORMATO DE SALIDA]: {d.get('formato')}. [cite: 19]")

        # MÓDULO 2: INGENIERÍA DE GUIONES (Super Retención) [cite: 37, 50]
        elif mod_id == 'mod_2':
            adn = adn_completo.get(d.get('marca'), {})
            prompt = (f"[IDENTIDAD Y TONO]: Eres un guionista experto en retención. Arquetipo: {adn.get('identidad')}. [cite: 51]\n"
                      f"[CONTEXTO DE MARCA]: Respeta los límites: {adn.get('reglas_duras')}. [cite: 52]\n"
                      f"[TAREA]: Guion de {d.get('longitud')} sobre la premisa: {d.get('premisa')}. [cite: 53]\n"
                      f"[ESTRUCTURA]: Aplica Super Retención. Prohibido iniciar con saludos. [cite: 47, 54]\n"
                      f"La primera línea debe atacar directamente la curiosidad intelectual. [cite: 47]\n"
                      f"[FORMATO DE SALIDA]: Guion dividido por bloques visuales lógicos. [cite: 56]")

        # MÓDULO 4: EMPAQUETADO (CTR EXTREMO) [cite: 111, 126]
        elif mod_id == 'mod_4':
            adn = adn_completo.get(d.get('marca'), {})
            prompt = (f"[IDENTIDAD]: Estratega de contenido viral y experto en SEO. [cite: 127]\n"
                      f"[CONTEXTO]: Analiza este contenido: {d.get('guion')}. [cite: 129]\n"
                      f"[TAREA]: Desarrolla el paquete para {d.get('plataforma')} maximizando CTR. [cite: 130]\n"
                      f"[RESTRICCIONES]: Títulos con 'Vacío de Información' y enfoque {d.get('enfoque')}. [cite: 120, 132]\n"
                      f"Imagen: Resolución 1920x1080 (16:9), estilo {d.get('estilo')}. [cite: 122, 133]\n"
                      f"Reglas inquebrantables del proyecto: {adn.get('reglas_duras')}. [cite: 124]\n"
                      f"[FORMATO DE SALIDA]: 5 Títulos, 1 Prompt de miniatura detallado en inglés (16:9), Descripción y Tags. [cite: 135, 138]")

        # MÓDULO 5: VENTAS UGC (Neuro-Marketing) [cite: 142, 156]
        elif mod_id == 'mod_5':
            prompt = (f"[ESTRATEGIA DE VENTAS]: {d.get('gatillo')}. [cite: 157, 158]\n"
                      f"[SECUENCIA]: Bloque {d.get('bloque')}, Duración {d.get('duracion')}. [cite: 160]\n"
                      f"[FASE VISUAL]: {d.get('modalidad')}. Render 4K fotorrealista. [cite: 161, 163]\n"
                      f"[FORMATO DE SALIDA]: Prompt visual de video y Guion de venta directa. [cite: 164, 166]")

        # Bucle de Supervivencia (Failover)
        for m in ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']:
            try:
                model = genai.GenerativeModel(m)
                response = model.generate_content(prompt)
                return {'resultado_ia': response.text}
            except:
                continue
        return {'error': 'Saturación total de modelos.'}
