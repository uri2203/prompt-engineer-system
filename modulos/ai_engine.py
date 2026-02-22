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

        # MÓDULO 1: TRADUCTOR UNIVERSAL (Zero-Shot)
        if mod_id == 'mod_1':
            prompt = (f"[IDENTIDAD]: Actúa como un {d.get('rol')}.\n"
                      f"[CONTEXTO]: {d.get('contexto')}.\n"
                      f"[TAREA]: {d.get('texto')}.\n"
                      f"[RESTRICCIONES]: Actúa con profesionalismo ejecutivo. Sé directo y estratégico. Cero relleno.\n"
                      f"Si generas código, debe ser funcional y completo para copiar y pegar.\n"
                      f"[FORMATO DE SALIDA]: {d.get('formato')}.")

        # MÓDULO 2: INGENIERÍA DE GUIONES (Super Retención)
        elif mod_id == 'mod_2':
            adn = adn_completo.get(d.get('marca'), {})
            prompt = (f"[IDENTIDAD Y TONO]: Eres un guionista experto en retención. Arquetipo: {adn.get('identidad')}.\n"
                      f"[CONTEXTO DE MARCA]: Respeta los límites: {adn.get('reglas_duras')}.\n"
                      f"[TAREA]: Desarrolla un guion de {d.get('longitud')} sobre la premisa: {d.get('premisa')}.\n"
                      f"[ESTRUCTURA]: Aplica Super Retención. Prohibido iniciar con saludos.\n"
                      f"La primera línea debe atacar directamente la curiosidad intelectual o el vacío de información.\n"
                      f"[FORMATO DE SALIDA]: Guion dividido por bloques visuales lógicos.")

        # MÓDULO 4: EMPAQUETADO (CTR EXTREMO)
        elif mod_id == 'mod_4':
            adn = adn_completo.get(d.get('marca'), {})
            prompt = (f"[IDENTIDAD]: Estratega de contenido viral y experto en SEO audiovisual.\n"
                      f"[CONTEXTO]: Analiza este contenido: {d.get('guion')}.\n"
                      f"[TAREA]: Desarrolla el paquete para {d.get('plataforma')} maximizando CTR.\n"
                      f"[RESTRICCIONES]: Títulos con 'Vacío de Información' y enfoque {d.get('enfoque')}. Prohibido resumir la trama.\n"
                      f"Imagen: Resolución 1920x1080 (16:9), estilo {d.get('estilo')}.\n"
                      f"Reglas inquebrantables del proyecto: {adn.get('reglas_duras')}.\n"
                      f"[FORMATO DE SALIDA]: 5 Títulos, 1 Prompt de miniatura detallado en inglés (16:9), Descripción y Tags.")

        # MÓDULO 5: VENTAS UGC (Neuro-Marketing)
        elif mod_id == 'mod_5':
            prompt = (f"[ESTRATEGIA DE VENTAS]: {d.get('gatillo')}.\n"
                      f"[SECUENCIA]: Bloque {d.get('bloque')}, Duración {d.get('duracion')}.\n"
                      f"[FASE VISUAL]: {d.get('modalidad')}. Render 4K fotorrealista.\n"
                      f"[FORMATO DE SALIDA]: Prompt visual de video y Guion de venta directa aplicando sesgo cognitivo.")

        # --- BUCLE DE SUPERVIVENCIA ESTRICTO (SOLO MODELOS DE ALTO RAZONAMIENTO) ---
        modelos_disponibles = ['gemini-1.5-pro', 'gemini-pro']
        
        for nombre_modelo in modelos_disponibles:
            try:
                model = genai.GenerativeModel(nombre_modelo)
                response = model.generate_content(prompt)
                if response and response.text:
                    return {'resultado_ia': response.text}
            except Exception as e:
                print(f"Falla de cuota en {nombre_modelo}: {str(e)}")
                continue 
        
        return {'error': 'Saturación en modelos Pro. El sistema requiere pausa táctica para recuperar cuota de la API, o inyectar una API Key de facturación activa.'}
