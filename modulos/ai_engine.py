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
            system_instruction = self.adn_la_viuda  # Fallback de seguridad

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
                    model = genai.GenerativeModel(
                        model_name=modelo,
                        system_instruction=system_instruction,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    response = model.generate_content(prompt_final)
                    
                    try:
                        json_parseado = json.loads(response.text)
                        return json.dumps(json_parseado, indent=4, ensure_ascii=False)
                    except json.JSONDecodeError:
                        return response.text
                        
                except Exception as e:
                    mensaje_error = str(e).replace(key, f"[*TANQUE_{index+1}*]")
                    if "429" in mensaje_error:
                        errores_detallados.append(f"> {modelo} | Tanque {index + 1}: CUOTA AGOTADA (429)")
                    else:
                        errores_detallados.append(f"> {modelo} | Tanque {index + 1}: {mensaje_error}")
                    continue
                
        return "BLOQUEO TOTAL DE CUOTA (NIVEL 2.5):\nGoogle ha restringido todas las llaves y modelos por hoy.\n\n" + "\n".join(errores_detallados)
