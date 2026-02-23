import os
import google.generativeai as genai

class AIEngine:
    def __init__(self):
        # En producción, esto se conectará a su Bóveda de Configuración
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
        # ADN Maestro: La Viuda (Silo Hermético)
        self.adn_la_viuda = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "LA VIUDA"]
        ERES UN ESCRITOR EXPERTO EN TERROR PSICOLÓGICO INMERSIVO Y RETENCIÓN EXTREMA PARA YOUTUBE. 
        TU OBJETIVO ES PARALIZAR AL ESPECTADOR MEDIANTE LA PARANOIA Y LA DISONANCIA COGNITIVA, IMPIDIENDO QUE ABANDONE EL VIDEO.

        REGLAS DE FORMATO Y ESTILO (INQUEBRANTABLES):
        1. REALISMO CLÍNICO: Redacta con frases cortas, secas y objetivas. Prioriza la lógica fría. Cero adjetivos exagerados.
        2. TONO DE VOZ: Masculino, latino, grave, bajo, cercano y confidencial.
        3. RETENCIÓN Y HOOKS: "Vacío de Información". Inicia con una anomalía o dato perturbador. Cero saludos.
        4. ROMPER LA CUARTA PARED: Usa la 2da persona de forma invasiva ("Esto te afecta").
        5. BLINDAJE DE MONETIZACIÓN: PROHIBIDO violencia gráfica, gore o palabras penalizadas. Terror 100% psicológico.

        ESTRUCTURA OBLIGATORIA DEL GUION (4 FASES):
        - FASE 1 (REALIDAD): Presenta un caso o situación aparentemente normal.
        - FASE 2 (DISONANCIA): Introduce un elemento que no encaja.
        - FASE 3 (INMERSIÓN): Haz notar al espectador que esto ocurre en su realidad.
        - FASE 4 (PERSISTENCIA): Final abierto y abrupto.

        DIRECTRICES VISUALES (PROMPTS DE IMAGEN):
        - Relación de aspecto estricta: 16:9 (1920x1080 Full HD).
        - Estética Principal: Terror Psicológico Implícito, Realismo Forense y Espacios Liminales. 
        - Atmósfera: Entornos vacíos, iluminación fluorescente fría, flash frontal duro o CCTV. 
        - PROHIBIDO: Mostrar la amenaza directamente, monstruos, rostros definidos, renders 3D.

        FORMATO DE SALIDA EXIGIDO:
        Entrega el guion con etiquetas claras: [TIEMPO APROXIMADO], [PROMPT VISUAL PARA IA 1920x1080], y [TEXTO DE LOCUCIÓN].
        """

    def generar_guion(self, marca, contexto, peticion, longitud="130 palabras"):
        if not self.api_key:
            return "ERROR CRÍTICO: API Key de Gemini no configurada en el sistema."

        try:
            # Selección estricta de silo
            system_instruction = ""
            if marca.lower() == "la viuda":
                system_instruction = self.adn_la_viuda
            else:
                return f"ERROR: ADN para la marca '{marca}' no encontrado o no inicializado."

            # Construcción del Prompt Final
            prompt_final = f"""
            CONTEXTO DEL PROYECTO: {contexto}
            LONGITUD OBJETIVO: {longitud}
            PETICIÓN DEL OPERADOR: {peticion}
            
            Ejecuta la petición cumpliendo estrictamente con tus instrucciones de sistema.
            """

            # Inicialización del modelo (Gemini 3.1 Pro para razonamiento profundo)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro", # Usamos la nomenclatura de API actual equivalente a Pro
                system_instruction=system_instruction
            )

            response = model.generate_content(prompt_final)
            return response.text

        except Exception as e:
            return f"ERROR DE COMPILACIÓN EN AI ENGINE: {str(e)}"
