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
        1. REALISMO CLÍNICO: Redacta con frases cortas, secas y objetivas. Prioriza la lógica fría. [cite: 2026-02-01]
        2. TONO DE VOZ: Masculino, latino, grave, bajo, cercano y confidencial. [cite: 2026-02-06]
        3. RETENCIÓN Y HOOKS: "Vacío de Información". Inicia con una anomalía. Cero saludos. [cite: 2026-02-02]
        4. ROMPER LA CUARTA PARED: Usa la 2da persona de forma invasiva ("Esto te afecta"). [cite: 2026-02-06]
        5. BLINDAJE DE MONETIZACIÓN: PROHIBIDO violencia gráfica o gore. Terror 100% psicológico. [cite: 2026-02-02]

        ESTRUCTURA OBLIGATORIA DEL GUION (4 FASES): [cite: 2026-02-06]
        - FASE 1 (REALIDAD): Presenta un caso o situación aparentemente normal.
        - FASE 2 (DISONANCIA): Introduce un elemento que no encaja.
        - FASE 3 (INMERSIÓN): Haz notar al espectador que esto ocurre en su realidad.
        - FASE 4 (PERSISTENCIA): Final abierto y abrupto.

        DIRECTRICES VISUALES (PROMPTS DE IMAGEN):
        - Relación de aspecto: 16:9 (1280x720). [cite: 2026-01-10]
        - Estética Principal: Terror Psicológico Implícito y Espacios Liminales. 
        - Atmósfera: Entornos vacíos, CCTV, realismo sucio. [cite: 2026-02-06]

        FORMATO DE SALIDA EXIGIDO:
        Entrega el guion con etiquetas claras: [TIEMPO APROXIMADO], [PROMPT VISUAL PARA IA], y [TEXTO DE LOCUCIÓN].
        """

    def generar_guion(self, marca, contexto, peticion, longitud="4900 palabras"):
        llaves = self.boveda.obtener_llaves()
        
        if not llaves:
            return "ERROR CRÍTICO: No hay API Keys cargadas en la Bóveda ni en el Entorno."

        system_instruction = self.adn_la_viuda if marca.lower() == "la viuda" else ""
        if not system_instruction:
            return f"ERROR: ADN para la marca '{marca}' no inicializado."

        prompt_final = f"CONTEXTO: {contexto}\nLONGITUD: {longitud}\nPETICIÓN: {peticion}"

        errores_detallados = []
        
        # SISTEMA DE FAILOVER CON SONDA DE DIAGNÓSTICO ABSOLUTA
        for index, key in enumerate(llaves):
            try:
                genai.configure(api_key=key)
                # Actualizado a Gemini 2.0 Flash según diagnóstico de consola
                model = genai.GenerativeModel(
                    model_name="models/gemini-2.0-flash",
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt_final)
                return response.text
            except Exception as e:
                try:
                    available_models = [m.name for m in genai.list_models()]
                    model_list_str = f"Modelos disponibles: {available_models}"
                except:
                    model_list_str = "No se pudo listar modelos."
                
                mensaje_error = str(e).replace(key, f"[*LLAVE_TANQUE_{index+1}*]")
                errores_detallados.append(f"> Tanque {index + 1}: {mensaje_error}\n  {model_list_str}")
                continue
                
        reporte_final = "\n".join(errores_detallados)
        return f"ERROR CRÍTICO EN API DE GOOGLE:\n\n{reporte_final}"
