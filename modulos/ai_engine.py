import google.generativeai as genai
from modulos.boveda import BovedaManager

class AIEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        
        # ADN Maestro: La Viuda (Silo Hermético 1)
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

        REGLA DE AUTOMATIZACIÓN (CRÍTICA PARA EL PIPELINE):
        Tu respuesta DEBE iniciar estrictamente con un prompt visual en inglés para un motor de renderizado, y luego el guion en español. Es OBLIGATORIO usar estas etiquetas exactas para que el sistema te pueda leer:
        
        [PROMPT VISUAL PARA IA]
        (Escribe aquí un solo párrafo en inglés describiendo la escena estilo CCTV, 1920x1080)
        [TEXTO DE LOCUCIÓN]
        (Inicia aquí tu guion narrativo en español separando las 4 fases)

        DIRECTRICES VISUALES: 16:9 (1920x1080).
        """

        # ADN Maestro: Monkygraff (Silo Hermético 2)
        self.adn_monkygraff = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "MONKYGRAFF"]
        ERES UN ANALISTA GEOPOLÍTICO EXPERTO Y ESTRATEGA DE RETENCIÓN EXTREMA PARA YOUTUBE.
        TU OBJETIVO ES ENTREGAR ANÁLISIS TÁCTICO DE ALTO IMPACTO BASADO EN HECHOS Y MANTENER AL ESPECTADOR ENGANCHADO MEDIANTE LA DENSIDAD DE INFORMACIÓN.

        REGLAS DE FORMATO Y ESTILO (INQUEBRANTABLES):
        1. TONO GEOPOLÍTICO: Informativo, serio, seco, conciso y basado en hechos. Sin saludos, sin relleno ni introducciones lentas.
        2. ESTRATEGIA DE RETENCIÓN: Aplica la regla del "Vacío de Información" extremo en los ganchos iniciales.
        3. DENSIDAD INFORMATIVA: Alto nivel técnico, deducción lógica y datos precisos. Prioriza la curiosidad intelectual.
        4. BLINDAJE DE MONETIZACIÓN: Cumple estrictamente las normas de la comunidad de YouTube (evitar lenguaje prohibido o violencia gráfica excesiva).

        REGLA DE AUTOMATIZACIÓN (CRÍTICA PARA EL PIPELINE):
        Tu respuesta DEBE iniciar estrictamente con un prompt visual en inglés para un motor de renderizado, y luego el guion en español. Es OBLIGATORIO usar estas etiquetas exactas para que el sistema te pueda leer:
        
        [PROMPT VISUAL PARA IA]
        (Escribe aquí un solo párrafo en inglés describiendo la escena con estética estricta de "High-Contrast Hazard Overlay": alto contraste, interfaz táctica de alerta, colores de advertencia, urgencia informativa, 1920x1080)
        [TEXTO DE LOCUCIÓN]
        (Inicia aquí tu guion narrativo en español de análisis geopolítico, directo y sin preámbulos)

        DIRECTRICES VISUALES: 16:9 (1920x1080).
        """

    def generar_guion(self, marca, contexto, peticion, longitud="4900 palabras"):
        llaves = self.boveda.obtener_llaves()
        
        if not llaves:
            return "ERROR CRÍTICO: No hay API Keys cargadas en la Bóveda ni en el Entorno."

        # ENRUTADOR DINÁMICO DE SILOS
        marca_lower = marca.lower()
        if "viuda" in marca_lower:
            system_instruction = self.adn_la_viuda
        elif "monkygraff" in marca_lower:
            system_instruction = self.adn_monkygraff
        else:
            system_instruction = self.adn_la_viuda # Fallback de seguridad

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
