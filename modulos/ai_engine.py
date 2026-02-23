import google.generativeai as genai
from modulos.boveda import BovedaManager

class AIEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        
        # ADN Maestro: La Viuda (Silo Hermético)
        self.adn_la_viuda = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "LA VIUDA"]
        ERES UN ESCRITOR EXPERTO EN TERROR PSICOLÓGICO INMERSIVO Y RETENCIÓN EXTREMA PARA YOUTUBE. 
        TU OBJETIVO ES PARALIZAR AL ESPECTADOR MEDIANTE LA PARANOIA Y LA DISONANCIA COGNITIVA.

        REGLAS DE FORMATO Y ESTILO (INQUEBRANTABLES):
        1. REALISMO CLÍNICO: Redacta con frases cortas, secas y objetivas.
        2. TONO DE VOZ: Masculino, latino, grave, bajo, cercano y confidencial.
        3. RETENCIÓN Y HOOKS: "Vacío de Información".
        4. ROMPER LA CUARTA PARED: Usa la 2da persona invasiva.
        5. BLINDAJE DE MONETIZACIÓN: PROHIBIDO violencia gráfica.

        ESTRUCTURA OBLIGATORIA DEL GUION (4 FASES):
        - FASE 1 (REALIDAD) | FASE 2 (DISONANCIA) | FASE 3 (INMERSIÓN) | FASE 4 (PERSISTENCIA)

        DIRECTRICES VISUALES: 16:9 (1920x1080).
        """

    def generar_guion(self, marca, contexto, peticion, longitud="4900 palabras"):
        llaves = self.boveda.obtener_llaves()
        
        if not llaves:
            return "ERROR CRÍTICO: No hay API Keys cargadas en la Bóveda ni en el Entorno."

        system_instruction = self.adn_la_viuda if marca.lower() == "la viuda" else ""
        prompt_final = f"CONTEXTO: {contexto}\nLONGITUD: {longitud}\nPETICIÓN: {peticion}"

        modelos_prioridad = [
            "models/gemini-2.5-flash", 
            "models/gemini-2.0-flash", 
            "models/gemini-2.0-flash-lite"
        ]
        errores_detallados = []
        
        for modelo in modelos_prioridad:
            for index, key in enumerate(llaves):
                try:
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel(
                        model_name=modelo,
                        system_instruction=system_instruction
                    )
                    response = model.generate_content(prompt_final)
                    return response.text
                except Exception as e:
                    mensaje_error = str(e).replace(key, f"[*TANQUE_{index+1}*]")
                    if "429" in mensaje_error:
                        errores_detallados.append(f"> {modelo} | Tanque {index + 1}: CUOTA AGOTADA (429)")
                    else:
                        errores_detallados.append(f"> {modelo} | Tanque {index + 1}: {mensaje_error}")
                    continue
                
        return "BLOQUEO TOTAL DE CUOTA (NIVEL 2.5):\nGoogle ha restringido todas las llaves y modelos por hoy.\n\n" + "\n".join(errores_detallados)
