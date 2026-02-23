import google.generativeai as genai
from modulos.boveda import BovedaManager

class AIEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        
        # ADN Maestro: La Viuda (Silo Hermético) [cite: 2026-02-06]
        self.adn_la_viuda = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "LA VIUDA"]
        ERES UN ESCRITOR EXPERTO EN TERROR PSICOLÓGICO INMERSIVO Y RETENCIÓN EXTREMA PARA YOUTUBE. 
        TU OBJETIVO ES PARALIZAR AL ESPECTADOR MEDIANTE LA PARANOIA Y LA DISONANCIA COGNITIVA.

        REGLAS DE FORMATO Y ESTILO (INQUEBRANTABLES):
        1. REALISMO CLÍNICO: Redacta con frases cortas, secas y objetivas. [cite: 2026-02-01]
        2. TONO DE VOZ: Masculino, latino, grave, bajo, cercano y confidencial. [cite: 2026-02-06]
        3. RETENCIÓN Y HOOKS: "Vacío de Información". [cite: 2026-02-02]
        4. ROMPER LA CUARTA PARED: Usa la 2da persona invasiva. [cite: 2026-02-06]
        5. BLINDAJE DE MONETIZACIÓN: PROHIBIDO violencia gráfica. [cite: 2026-02-02]

        ESTRUCTURA OBLIGATORIA DEL GUION (4 FASES): [cite: 2026-02-06]
        - FASE 1 (REALIDAD) | FASE 2 (DISONANCIA) | FASE 3 (INMERSIÓN) | FASE 4 (PERSISTENCIA)

        DIRECTRICES VISUALES: 16:9 (1280x720). [cite: 2026-01-10]
        """

    def generar_guion(self, marca, contexto, peticion, longitud="4900 palabras"):
        llaves = self.boveda.obtener_llaves()
        
        # Sonda de diagnóstico para la consola negra
        if not llaves or len(llaves) == 0:
            return f"ERROR CRÍTICO: El sistema reporta 0 llaves en memoria.\nRevise su variable GEMINI_KEYS en Render."

        system_instruction = self.adn_la_viuda if marca.lower() == "la viuda" else ""
        prompt_final = f"CONTEXTO: {contexto}\nLONGITUD: {longitud}\nPETICIÓN: {peticion}"

        errores_detallados = []
        
        for index, key in enumerate(llaves):
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(
                    model_name="models/gemini-2.0-flash",
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt_final)
                return response.text
            except Exception as e:
                mensaje_error = str(e).replace(key, f"[*TANQUE_{index+1}*]")
                errores_detallados.append(f"> Tanque {index + 1}: {mensaje_error}")
                continue
                
        return f"ERROR DE CONEXIÓN:\n\n" + "\n".join(errores_detallados)
