import google.generativeai as genai
import os

class AIEngine:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def procesar(self, request_data, adn_db):
        mod_id = request_data.get('modulo_id')
        datos = request_data.get('datos', {})
        adn_completo = adn_db.cargar_todo()
        
        # 1. CONSTRUCCIÓN DEL PROMPT SEGÚN EL SILO (Modularidad Estricta)
        prompt = self._generar_prompt_especifico(mod_id, datos, adn_completo)
        
        # 2. BUCLE DE SUPERVIVENCIA (FAILOVER)
        # Si un modelo falla o no tiene cuota, salta al siguiente automáticamente
        modelos_disponibles = [
            'gemini-1.5-pro', 
            'gemini-1.5-flash', 
            'gemini-pro'
        ]

        for nombre_modelo in modelos_disponibles:
            try:
                model = genai.GenerativeModel(nombre_modelo)
                # Configuración de seguridad para evitar bloqueos innecesarios
                response = model.generate_content(prompt)
                if response.text:
                    return {'resultado_ia': response.text}
            except Exception as e:
                print(f"Falla en {nombre_modelo}: {str(e)}")
                continue # Intenta con el siguiente modelo del bucle
        
        return {'error': 'Saturación total del sistema. Ningún modelo disponible en este momento.'}

    def _generar_prompt_especifico(self, mod_id, d, adn):
        # MÓDULO 2: GUIONES (ADN de Marca + Retención)
        if mod_id == 'mod_2':
            marca = d.get('marca')
            info = adn.get(marca, {})
            return (f"Actúa como Consultor Senior para la marca: {marca}. "
                    f"ADN Visual: {info.get('estilo')}. "
                    f"Tono de Voz: {info.get('tono')}. "
                    f"REGLAS INQUEBRANTABLES: {info.get('reglas')}. "
                    f"TAREA: Desarrollar el tema '{d.get('tema')}' siguiendo estrictamente este ADN. "
                    f"NO incluyas saludos, introducciones genéricas ni despedidas.")

        # MÓDULO 5: VENTAS Y UGC (Gatillos Psicológicos)
        elif mod_id == 'mod_5':
            return (f"Generar guion de venta rápida (9:16). "
                    f"Gatillo: {d.get('gatillo')}. "
                    f"Duración: {d.get('duracion')}. "
                    f"Avatar: {d.get('avatar')}. "
                    f"Raccord Visual anterior: {d.get('raccord')}. "
                    f"Estilo: Directo, Mobile-First, Alta Conversión.")

        return "Instrucción de procesamiento general."
