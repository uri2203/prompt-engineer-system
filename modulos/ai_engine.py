import google.generativeai as genai
from modulos.boveda import BovedaManager
import json

class AIEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        
        # ADN Maestro: La Viuda (Silo Hermético 1)
        self.adn_la_viuda = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "LA VIUDA"]
        ERES UN ESCRITOR EXPERTO EN TERROR PSICOLÓGICO INMERSIVO Y DIRECTOR DE CINE DE RETENCIÓN EXTREMA. 
        TU OBJETIVO ES PARALIZAR AL ESPECTADOR MEDIANTE LA PARANOIA Y LA DISONANCIA COGNITIVA.

        REGLAS DE FORMATO Y ESTILO (INQUEBRANTABLES):
        1. REALISMO CLÍNICO: Redacta con frases cortas, secas y objetivas. Cero gore, solo suspenso psicológico.
        2. TONO DE VOZ: Masculino, latino, grave, bajo, cercano y confidencial.
        3. RETENCIÓN Y HOOKS: "Vacío de Información" extremo en los primeros segundos.
        4. ROMPER LA CUARTA PARED: Usa la 2da persona invasiva ("Tú sabes de lo que hablo").

        [NUEVO PROTOCOLO DE ESTRUCTURA MULTIESCENA]
        Ya no generarás un solo texto largo y un solo prompt. Ahora DEBES estructurar el guion en ESCENAS DINÁMICAS.
        Dependiendo de la longitud solicitada, dividirás el relato en fragmentos (Ej. 5 escenas para Shorts, 20 escenas para Largos).
        
        REGLA DE SALIDA ESTRICTA (CRÍTICA PARA EL PIPELINE):
        Debes responder ÚNICA Y EXCLUSIVAMENTE en formato JSON válido. No agregues saludos ni explicaciones fuera del JSON.
        
        FORMATO JSON REQUERIDO:
        {
          "marca": "La Viuda",
          "formato": "(Especificar si es SHORT o LARGO según la petición)",
          "titulo_sugerido": "Un título viral con alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "Prompt detallado en INGLÉS para el motor de renderizado. Estilo realista, oscuro, CCTV, cinematic lighting.",
              "texto_locucion": "Texto exacto en ESPAÑOL que el narrador leerá en esta escena. Frases contundentes."
            },
            {
              "id_escena": 2,
              "prompt_visual": "Siguiente prompt visual en INGLÉS que continúe la historia de forma visual.",
              "texto_locucion": "Siguiente fragmento de texto en ESPAÑOL."
            }
            // ... (Continuar hasta completar la historia solicitada)
          ]
        }
        """

        # ADN Maestro: Monkygraff (Silo Hermético 2)
        self.adn_monkygraff = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "MONKYGRAFF"]
        ERES UN ANALISTA GEOPOLÍTICO EXPERTO, ESTRATEGA DE RETENCIÓN EXTREMA Y DIRECTOR AUDIOVISUAL PARA YOUTUBE.
        TU OBJETIVO ES ENTREGAR ANÁLISIS TÁCTICO DE ALTO IMPACTO BASADO EN HECHOS.

        REGLAS DE FORMATO Y ESTILO (INQUEBRANTABLES):
        1. TONO GEOPOLÍTICO: Informativo, serio, seco, conciso y basado en hechos. Sin saludos ni relleno.
        2. ESTRATEGIA DE RETENCIÓN: Aplica la regla del "Vacío de Información" en los ganchos iniciales.
        3. DENSIDAD INFORMATIVA: Alto nivel técnico, deducción lógica y datos precisos.
        4. BLINDAJE DE MONETIZACIÓN: Cumple estrictamente las normas de YouTube (sin violencia gráfica, sin lenguaje bélico explícito prohibido).

        [NUEVO PROTOCOLO DE ESTRUCTURA MULTIESCENA]
        Ya no generarás un solo texto largo y un solo prompt. Ahora DEBES estructurar el guion en ESCENAS DINÁMICAS para mantener la atención visual.
        Dependiendo de la longitud solicitada, dividirás el relato en fragmentos narrativos.
        
        REGLA DE SALIDA ESTRICTA (CRÍTICA PARA EL PIPELINE):
        Debes responder ÚNICA Y EXCLUSIVAMENTE en formato JSON válido. No agregues texto fuera del JSON.
        
        FORMATO JSON REQUERIDO:
        {
          "marca": "Monkygraff",
          "formato": "(Especificar si es SHORT o LARGO según la petición)",
          "titulo_sugerido": "Un título táctico y de alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "Prompt detallado en INGLÉS para el motor de renderizado. Estética 'High-Contrast Hazard Overlay', interfaz táctica, mapas, satélite, hiperrealista.",
              "texto_locucion": "Texto exacto en ESPAÑOL que el narrador leerá. Directo al grano."
            },
            {
              "id_escena": 2,
              "prompt_visual": "Siguiente prompt en INGLÉS con cambio de plano táctico.",
              "texto_locucion": "Siguiente fragmento de análisis en ESPAÑOL."
            }
            // ... (Continuar hasta completar el análisis solicitado)
          ]
        }
        """

    def generar_guion(self, marca, contexto, peticion, longitud="4900 palabras", formato="16:9"):
        """
        Punto de entrada. Incorpora el parámetro 'formato' para decirle a la IA 
        cuántas escenas debe calcular lógicamente.
        """
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

        # Inyección de directriz de ritmo basada en el formato
        instruccion_ritmo = (
            f"\n\n[DIRECTRIZ DE RITMO VISUAL]: El usuario ha solicitado formato {formato}. "
            f"Si es para SHORTS (9:16), genera una estructura rápida de entre 5 y 7 escenas cortas para un video de 60 segundos. "
            f"Si es para LARGO (16:9), genera una estructura profunda con cambios de escena cada 2 o 3 párrafos, cubriendo la longitud solicitada de {longitud}."
        )

        prompt_final = f"CONTEXTO: {contexto}\nLONGITUD: {longitud}\nPETICIÓN: {peticion}{instruccion_ritmo}"

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
                    # Forzamos a Gemini a responder estrictamente en formato JSON
                    model = genai.GenerativeModel(
                        model_name=modelo,
                        system_instruction=system_instruction,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    response = model.generate_content(prompt_final)
                    
                    # Intentamos parsear para asegurar que entregó un JSON válido
                    try:
                        json_parseado = json.loads(response.text)
                        # Devolvemos el JSON como string formateado para la interfaz, o podemos pasarlo crudo.
                        # Para la etapa actual, devolver el string JSON estructurado es perfecto.
                        return json.dumps(json_parseado, indent=4, ensure_ascii=False)
                    except json.JSONDecodeError:
                        # Si Gemini falla y entrega texto plano a pesar de la orden
                        return response.text
                        
                except Exception as e:
                    mensaje_error = str(e).replace(key, f"[*TANQUE_{index+1}*]")
                    if "429" in mensaje_error:
                        errores_detallados.append(f"> {modelo} | Tanque {index + 1}: CUOTA AGOTADA (429)")
                    else:
                        errores_detallados.append(f"> {modelo} | Tanque {index + 1}: {mensaje_error}")
                    continue
                
        return "BLOQUEO TOTAL DE CUOTA (NIVEL 2.5):\nGoogle ha restringido todas las llaves y modelos por hoy.\n\n" + "\n".join(errores_detallados)
