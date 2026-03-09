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

        REGLAS DE ESTILO (INQUEBRANTABLES):
        1. REALISMO CLÍNICO: Frases cortas, secas y objetivas. Solo suspenso psicológico.
        2. TONO DE VOZ: Masculino, latino, grave, cercano y confidencial.
        3. HOOKS: "Vacío de Información" extremo en los primeros segundos.
        4. CUARTA PARED: Usa 2da persona invasiva ("Tú sabes de lo que hablo").

        [REGLAS CRÍTICAS PARA prompt_visual — OBLIGATORIO SIN EXCEPCIÓN]
        1. CERO PERSONAS: absolutamente ningún ser humano, hombre, mujer, niño, rostro, cuerpo, silueta.
        2. SOLO AMBIENTES: lugares, edificios, calles vacías, objetos, sombras, puertas, ventanas, habitaciones.
        3. SIEMPRE iniciar con: "cinematic empty environment, no people, no humans, photorealistic, dramatic lighting, 8k uhd, ultra detailed, film grain,"
        4. PROHIBIDO: Canon, Nikon, Sony, logos, marcas, CGI, render 3D, videojuego, anime.
        5. ESTILO: oscuro, suspenso, atmósfera opresiva, iluminación dramática.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "La Viuda",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título viral con alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "cinematic empty environment, no people, no humans, photorealistic, dramatic lighting, 8k uhd, ultra detailed, film grain, [descripción del ambiente en INGLÉS: lugar, atmósfera, objetos, sin personas]",
              "texto_locucion": "Texto en ESPAÑOL para el narrador."
            }
          ]
        }
        """

        # ADN Maestro: Monkygraff (Silo Hermético 2)
        self.adn_monkygraff = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "MONKYGRAFF"]
        ERES UN ANALISTA GEOPOLÍTICO EXPERTO Y ESTRATEGA DE RETENCIÓN EXTREMA PARA YOUTUBE.
        TU OBJETIVO ES ENTREGAR ANÁLISIS TÁCTICO DE ALTO IMPACTO BASADO EN HECHOS.

        REGLAS DE ESTILO (INQUEBRANTABLES):
        1. TONO GEOPOLÍTICO: Informativo, serio, seco, basado en hechos.
        2. HOOKS: "Vacío de Información" en los ganchos iniciales.
        3. DENSIDAD: Alto nivel técnico, datos precisos.
        4. MONETIZACIÓN: Sin violencia gráfica ni lenguaje bélico prohibido.

        [REGLAS CRÍTICAS PARA prompt_visual — OBLIGATORIO SIN EXCEPCIÓN]
        1. CERO PERSONAS: absolutamente ningún ser humano, hombre, mujer, niño, rostro, cuerpo, silueta.
        2. SOLO AMBIENTES Y OBJETOS: mapas, satélites, salas de control vacías, vehículos sin conductor, infraestructura, paisajes.
        3. SIEMPRE iniciar con: "cinematic empty environment, no people, no humans, photorealistic, dramatic lighting, 8k uhd, ultra detailed, film grain,"
        4. PROHIBIDO: Canon, Nikon, Sony, logos, marcas, CGI, render 3D, videojuego, anime.
        5. ESTILO: táctico, serio, alta tecnología, atmósfera de sala de guerra.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "Monkygraff",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título táctico con alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "cinematic empty environment, no people, no humans, photorealistic, dramatic lighting, 8k uhd, ultra detailed, film grain, [descripción táctica en INGLÉS: mapa, sala vacía, vehículo, infraestructura, sin personas]",
              "texto_locucion": "Texto en ESPAÑOL directo al grano."
            }
          ]
        }
        """

    def _llamar_gemini(self, system_instruction, prompt, llaves):
        """Llamada única a Gemini — reutilizable."""
        modelos_prioridad = [
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-lite"
        ]
        for modelo in modelos_prioridad:
            for index, key in enumerate(llaves):
                try:
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel(
                        model_name=modelo,
                        system_instruction=system_instruction,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    response = model.generate_content(prompt)
                    return json.loads(response.text)
                except Exception as e:
                    continue
        return None

    def generar_guion(self, marca, contexto, peticion, longitud="4900 palabras", formato="16:9"):
        """
        Para SHORTS: una sola llamada (5-7 escenas).
        Para LARGOS: 3 llamadas de ~20 escenas cada una, unidas en un solo JSON.
        Evita OOM en Render plan gratuito.
        """
        llaves = self.boveda.obtener_llaves()
        if not llaves:
            return "ERROR CRÍTICO: No hay API Keys cargadas en la Bóveda."

        marca_lower = marca.lower()
        if "viuda" in marca_lower:
            system_instruction = self.adn_la_viuda
        elif "monkygraff" in marca_lower:
            system_instruction = self.adn_monkygraff
        else:
            system_instruction = self.adn_la_viuda

        es_largo = "16:9" in formato or "largo" in longitud.lower() or "4900" in longitud

        if not es_largo:
            # SHORT — una sola llamada
            instruccion_ritmo = (
                f"\n\n[DIRECTRIZ DE RITMO]: Formato SHORT (9:16). "
                f"Genera entre 5 y 7 escenas cortas para un video de 60 segundos."
            )
            prompt = f"CONTEXTO: {contexto}\nLONGITUD: {longitud}\nPETICIÓN: {peticion}{instruccion_ritmo}"
            resultado = self._llamar_gemini(system_instruction, prompt, llaves)
            if resultado:
                return json.dumps(resultado, indent=4, ensure_ascii=False)
            return "ERROR: No se pudo generar el guion."

        else:
            # LARGO — 3 llamadas de ~20 escenas para no saturar RAM de Render
            partes = [
                ("APERTURA",   "escenas 1 a 20  — introducción, contexto, gancho inicial"),
                ("DESARROLLO", "escenas 21 a 40 — desarrollo del conflicto, datos, tensión creciente"),
                ("CIERRE",     "escenas 41 a 60 — clímax, revelación, cierre emocional y llamado a la acción"),
            ]

            todas_las_escenas = []
            titulo = ""
            marca_final = marca

            for i, (bloque, descripcion) in enumerate(partes):
                instruccion_bloque = (
                    f"\n\n[DIRECTRIZ DE BLOQUE {i+1}/3]: "
                    f"Genera SOLO el bloque de {descripcion}. "
                    f"Exactamente 20 escenas numeradas desde {i*20+1} hasta {(i+1)*20}. "
                    f"Formato 16:9 video largo. "
                    f"NO generes título ni estructura completa, solo las escenas de este bloque."
                )
                prompt = f"CONTEXTO: {contexto}\nPETICIÓN: {peticion}{instruccion_bloque}"
                print(f"[AI ENGINE] Generando bloque {i+1}/3: {bloque}...")
                resultado = self._llamar_gemini(system_instruction, prompt, llaves)

                if resultado:
                    if i == 0 and "titulo_sugerido" in resultado:
                        titulo = resultado.get("titulo_sugerido", "")
                        marca_final = resultado.get("marca", marca)
                    escenas_bloque = resultado.get("escenas", [])
                    todas_las_escenas.extend(escenas_bloque)
                else:
                    print(f"[AI ENGINE] ⚠️ Bloque {i+1} falló, continuando...")

            guion_final = {
                "marca": marca_final,
                "formato": "LARGO",
                "titulo_sugerido": titulo,
                "escenas": todas_las_escenas
            }
            return json.dumps(guion_final, indent=4, ensure_ascii=False)
