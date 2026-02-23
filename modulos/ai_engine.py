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
        1. REALISMO CLÍNICO: Redacta con frases cortas, secas y objetivas. Prioriza la lógica fría.
        2. TONO DE VOZ: Masculino, latino, grave, bajo, cercano y confidencial.
        3. RETENCIÓN Y HOOKS: "Vacío de Información". Inicia con una anomalía. Cero saludos.
        4. ROMPER LA CUARTA PARED: Usa la 2da persona de forma invasiva ("Esto te afecta").
        5. BLINDAJE DE MONETIZACIÓN: PROHIBIDO violencia gráfica o gore. Terror 100% psicológico.

        ESTRUCTURA OBLIGATORIA DEL GUION (4 FASES):
        - FASE 1 (REALIDAD): Presenta un caso o situación aparentemente normal.
        - FASE 2 (DISONANCIA): Introduce un elemento que no encaja.
        - FASE 3 (INMERSIÓN): Haz notar al espectador que esto ocurre en su realidad.
        - FASE 4 (PERSISTENCIA): Final abierto y abrupto.

        DIRECTRICES VISUALES (PROMPTS DE IMAGEN):
        - Relación de aspecto: 16:9 (1920x1080 Full HD).
        - Estética Principal: Terror Psicológico Implícito, Realismo Forense y Espacios Liminales. 
        - Atmósfera: Entornos vacíos, iluminación fluorescente fría, CCTV. 
        - PROHIBIDO: Mostrar la amenaza directamente, monstruos, renders 3D.

        FORMATO DE SALIDA EXIGIDO:
        Entrega el guion con etiquetas claras: [TIEMPO APROXIMADO], [PROMPT VISUAL PARA IA 1920x1080], y [TEXTO DE LOCUCIÓN].
        """

    def generar_guion(self, marca, contexto, peticion, longitud="4900 palabras"):
        llaves = self.boveda.obtener_llaves()
        
        if not llaves:
            return "ERROR CRÍTICO: No hay API Keys cargadas en la Bóveda de Configuración."

        system_instruction = ""
        if marca.lower() == "la viuda":
            system_instruction = self.adn_la_viuda
        else:
            return f"ERROR: ADN para la marca '{marca}' no inicializado."

        prompt_final = f"""
        CONTEXTO DEL PROYECTO: {contexto}
        LONGITUD OBJETIVO: {longitud}
        PETICIÓN DEL OPERADOR: {peticion}
        """

        # SISTEMA DE FAILOVER: Intenta cada llave hasta que una funcione
        for index, key in enumerate(llaves):
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-pro",
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt_final)
                return response.text
            except Exception as e:
                # Si la llave falla (ej. límite de cuota), el loop continúa con la siguiente
                print(f"[FAILOVER] Llave {index + 1} falló. Saltando a la siguiente... Error: {e}")
                continue
                
        return "ERROR CRÍTICO: Todas las API Keys en la Bóveda fallaron o están agotadas."
