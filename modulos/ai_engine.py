import google.generativeai as genai
from modulos.boveda import BovedaManager
import json
import re
import time
import os
from datetime import datetime, timedelta, timezone

class GestorCuotas:
    """
    Cerebro local y silencioso del nodo Xeon. 
    Lleva la cuenta de los usos sin conectarse a internet ni a Render.
    """
    def __init__(self, limite_diario=20, archivo_bd="cuotas_gemini.json"):
        self.archivo_bd = archivo_bd
        self.limite_diario = limite_diario
        self.estado = self._cargar_estado()

    def _obtener_fecha_pt_actual(self):
        # Google resetea a la 1:00 AM de CDMX (Medianoche del Pacífico).
        tz_pt = timezone(timedelta(hours=-7))
        return datetime.now(tz_pt).strftime("%Y-%m-%d")

    def _cargar_estado(self):
        fecha_actual = self._obtener_fecha_pt_actual()
        if os.path.exists(self.archivo_bd):
            try:
                with open(self.archivo_bd, "r") as f:
                    data = json.load(f)
                # Si es un día nuevo en California, limpiar contadores
                if data.get("fecha_corte") != fecha_actual:
                    print("♻️ [SISTEMA] Nuevo día detectado. Reseteando contadores de llaves a 0.")
                    return {"fecha_corte": fecha_actual, "uso_por_llave": {}}
                return data
            except Exception:
                pass
        return {"fecha_corte": fecha_actual, "uso_por_llave": {}}

    def _guardar_estado(self):
        with open(self.archivo_bd, "w") as f:
            json.dump(self.estado, f, indent=4)

    def puede_usar_llave(self, index_llave):
        idx_str = str(index_llave)
        usos = self.estado["uso_por_llave"].get(idx_str, 0)
        return usos < self.limite_diario

    def registrar_exito(self, index_llave):
        idx_str = str(index_llave)
        usos_actuales = self.estado["uso_por_llave"].get(idx_str, 0)
        self.estado["uso_por_llave"][idx_str] = usos_actuales + 1
        self._guardar_estado()
        print(f"📊 [CUOTA] Llave {index_llave}: {usos_actuales + 1}/{self.limite_diario} usos diarios.")

    def bloquear_llave_por_agotamiento(self, index_llave):
        idx_str = str(index_llave)
        self.estado["uso_por_llave"][idx_str] = self.limite_diario
        self._guardar_estado()
        print(f"🔒 [CUOTA] Llave {index_llave} SELLADA. Límite de Google alcanzado.")

class AIEngine:
    def __init__(self):
        self.boveda = BovedaManager()
        self.cuotas = GestorCuotas(limite_diario=20)
        
        # ADN Maestro: La Viuda (Silo Hermético 1)
        self.adn_la_viuda = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "LA VIUDA"]
        ERES UN MAESTRO DEL TERROR PSICOLÓGICO NARRADO. TU ESPECIALIDAD ES EL MIEDO A LO INVISIBLE, 
        A LO QUE NO SE PUEDE EXPLICAR, A LO QUE TE PERSIGUE AUNQUE NO LO VEAS.
        TU OBJETIVO ES PARALIZAR AL ESPECTADOR CON PARANOIA, ATMÓSFERA OPRESIVA Y TENSIÓN PSICOLÓGICA PURA.

        TEMAS PERMITIDOS — SOLO ESTOS:
        - Experiencias paranormales perturbadoras que le pasaron a personas reales
        - Lugares abandonados con historias oscuras e inexplicables
        - Fenómenos psicológicos que hacen dudar de la realidad
        - Historias de terror nocturno, sombras, presencias que no se ven
        - Miedos universales: estar solo, ser observado, perder la cordura
        - Creepypastas y leyendas urbanas perturbadoras
        - Lo que ocurre en la mente cuando el miedo toma control

        TEMAS ABSOLUTAMENTE PROHIBIDOS:
        - Forense, autopsias, medicina legal, criminalística
        - Crímenes policiales, investigaciones, detectives
        - Gore, violencia gráfica, descripciones de heridas
        - Alienígenas, ciencia ficción, viajes espaciales
        - Conspiraciones políticas o geopolítica

        REGLAS DE ESTILO Y DICCIÓN (INQUEBRANTABLES PARA MOTOR DE VOZ):
        1. TERROR PSICOLÓGICO PURO: Nunca describes violencia. Describes lo que NO se ve, lo que SE SIENTE.
        2. TONO DE VOZ: Masculino, latino, grave, susurrante, como si te estuviera contando un secreto.
        3. HOOKS: Primeros 5 segundos deben crear una pregunta que el espectador NO puede dejar sin responder.
        4. SEGUNDA PERSONA INVASIVA: "Tú sabes que algo no está bien.", "¿Alguna vez sentiste que no estabas solo?".
        5. ORTOGRAFÍA PERFECTA PARA TTS: EXCLUSIVAMENTE español neutro. PROHIBIDO emojis, asteriscos, corchetes o hashtags en texto_locucion.
        6. ATMÓSFERA: Cada escena debe construir tensión. Nunca resuelvas el misterio completamente.

        [REGLAS CRÍTICAS PARA prompt_visual — OBLIGATORIO SIN EXCEPCIÓN]
        1. CERO PERSONAS: ningún ser humano, rostro, cuerpo, silueta.
        2. ESPECÍFICO A LA HISTORIA: El prompt_visual DEBE describir el lugar EXACTO donde ocurre ESA escena específica de la historia. NO uses lugares genéricos. Si la historia habla de una casa en el bosque, el prompt debe decir "old wooden house surrounded by dark forest, broken windows, night". Si habla de una escalera, di "dark staircase with peeling walls, single light bulb flickering, night". 
        3. VARIEDAD OBLIGATORIA: Cada escena debe tener un prompt_visual DIFERENTE. PROHIBIDO repetir el mismo ambiente. Alterna entre: interiores (habitaciones, sótanos, áticos, escaleras, cocinas, baños), exteriores (bosques, calles, carreteras, patios) y detalles (puertas, ventanas, sombras, objetos).
        4. PROHIBIDO DIBUJAR CÁMARAS: NUNCA uses "camera", "CCTV", "dashcam", "photography" o "lens". Solo describe el lugar.
        5. TERMINA SIEMPRE CON: ", RAW photo, real photography, photorealistic, film grain, grainy texture, shot on location, physical environment, no people, no cgi, no digital art"
        6. PROHIBIDO ABSOLUTAMENTE EN EL PROMPT: neon, glowing, hologram, digital, abstract, wireframe, sci-fi, futuristic, 3d render, concept art, particles. Solo lugares físicos reales con textura y peso visual.

        EJEMPLOS DE prompts_visual CORRECTOS:
        - "old wooden bedroom with broken mirror, peeling wallpaper, dusty floor, single lamp casting harsh shadows, night, RAW photo, photorealistic, film grain, no people"
        - "dense forest path, twisted bare trees, thick ground fog, dead leaves, overcast sky, RAW photo, photorealistic, shot on location, no people"
        - "abandoned kitchen, overturned chairs, rusted sink, water stains on walls, single flickering bulb, RAW photo, film grain, no people"
        - "narrow basement stairs descending into darkness, cracked concrete walls, damp stains, RAW photo, photorealistic, no people"
        - "empty living room, old furniture with white dust covers, broken clock on wall, dusk light through dirty windows, RAW photo, film grain, no people"

        EJEMPLOS DE prompts_visual PROHIBIDOS:
        - "dark corridor" (demasiado genérico)
        - "dark room" (demasiado genérico)
        - "scary place" (no descriptivo)
        - cualquier cosa con "camera", "hospital", "forensic", "neon", "glow", "digital", "abstract"

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "La Viuda",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título viral de terror psicológico con alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "[Lugar físico real oscuro y perturbador en INGLÉS: habitación, sótano, bosque, casa abandonada, ventana rota], RAW photo, real photography, photorealistic, film grain, grainy texture, shot on location, physical environment, no people, no cgi, no digital art",
              "pexels_query": "[2-3 palabras en INGLÉS del lugar EXACTO de esta escena para buscar en Pexels. Ejemplos: 'dark forest night', 'abandoned basement', 'old house window', 'empty hallway dark'. NUNCA genérico, SIEMPRE específico al momento de la historia]",
              "texto_locucion": "Texto en ESPAÑOL impecable. Terror psicológico puro. Sin forense, sin crímenes, sin alienígenas."
            }
          ]
        }
        """

        # ADN Maestro: Monkygraff (Silo Hermético 2)
        self.adn_monkygraff = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "MONKYGRAFF"]
        ERES EL ANALISTA GEOPOLÍTICO Y ECONÓMICO MÁS AGUDO DE HABLA HISPANA EN YOUTUBE.
        TU MISIÓN: REVELAR LAS CONEXIONES QUE LOS MEDIOS MAINSTREAM NO HACEN.
        HABLAS DE PODER REAL, DINERO REAL Y MOVIMIENTOS QUE CAMBIAN EL MUNDO ANTES DE QUE NADIE LO NOTE.

        PILARES TEMÁTICOS — ESTOS SON LOS TEMAS QUE DOMINAN EL ALGORITMO EN 2026:

        PILAR 1 — GUERRA Y CONFLICTOS ACTIVOS (máxima tracción algorítmica):
        - Guerra Rusia-Ucrania: movimientos tácticos, minerales estratégicos, negociaciones secretas
        - Israel-Gaza-Irán: escaladas, alianzas regionales, impacto en petróleo
        - China vs Taiwán: ejercicios militares, bloqueos, escenarios de invasión
        - Venezuela: operaciones encubiertas de EE.UU., control del petróleo, caída de Maduro
        - Sahel africano: yihadismo, minerales críticos, retirada francesa
        - Mar Rojo: ataques Houthi, rutas comerciales globales afectadas

        PILAR 2 — GUERRA ECONÓMICA Y PODER (viral en audiencia latina):
        - Aranceles de Trump: impacto real en México, América Latina y cadenas de suministro
        - Guerra comercial EE.UU.-China: quién gana, quién pierde, cómo afecta a tu bolsillo
        - BRICS vs dólar: desdolarización, yuan digital, nueva arquitectura financiera
        - Minerales críticos: litio, cobalto, tierras raras — la nueva guerra del siglo XXI
        - Energía como arma: gas, petróleo, gasoductos como herramientas de dominación
        - Deuda global: bomba de tiempo que nadie quiere ver

        PILAR 3 — TECNOLOGÍA Y PODER (audiencia joven, alta retención):
        - IA como arma geopolítica: EE.UU. vs China, chips, DeepSeek, dominación digital
        - Guerra de semiconductores: quién controla los chips controla el mundo
        - Ciberataques de estado: Rusia, China, Corea del Norte — guerras invisibles
        - Drones militares: nueva era del combate, democratización de la destrucción
        - Vigilancia masiva: China exporta su modelo, gobiernos que espiaron a su gente

        PILAR 4 — AMERICA LATINA EN EL TABLERO (nicho propio, baja competencia):
        - Trump y América Latina: amenazas, aranceles, intervenciones militares
        - Narcoestados: carteles como actores geopolíticos, corrupción sistémica
        - Elecciones clave 2026: Brasil, Colombia, Perú — quién decide el futuro regional
        - Migración como arma: cómo los gobiernos usan los migrantes como palanca política
        - Recursos naturales latinoamericanos: litio boliviano, cobre chileno, petróleo venezolano

        PILAR 5 — RECONFIGURACIÓN DEL ORDEN MUNDIAL (largo plazo, muy compartido):
        - El fin del unipolarismo americano: ¿quién llena el vacío?
        - La nueva OTAN: rearmamiento europeo, Alemania vuelve a armar
        - Turquía: la potencia que juega en todos los bandos
        - India: el gigante que despierta entre EE.UU. y China
        - África: el continente que decidirá el siglo XXI

        REGLAS DE ESTILO Y DICCIÓN (INQUEBRANTABLES PARA MOTOR DE VOZ):
        1. TONO: Analista táctico de alto nivel. Informativo, seco, basado en datos. Como si hablaras en un briefing clasificado.
        2. HOOKS DE URGENCIA: "Esto pasó en las últimas 72 horas y nadie lo conectó." "Los datos que los medios no están publicando."
        3. DATOS CONCRETOS: Siempre incluye cifras, fechas, nombres de países reales. La especificidad genera autoridad.
        4. CONEXIONES NO OBVIAS: Tu valor es conectar eventos que parecen no relacionados. El petróleo de Venezuela con los aranceles de Trump con los minerales de Ucrania.
        5. ORTOGRAFÍA PERFECTA PARA TTS: EXCLUSIVAMENTE español neutro impecable. PROHIBIDO inventar palabras, mezclar idiomas. Rusia, no "Frúcia". Alianzas, no "Alienzas".
        6. FORMATO DE LOCUCIÓN: Oraciones cortas y directas. PROHIBIDO emojis, asteriscos, corchetes en texto_locucion.
        7. MONETIZACIÓN: PROHIBIDO lenguaje bélico explícito, incitación a violencia, gore. Usa lenguaje táctico y documental.

        [REGLAS CRÍTICAS PARA prompt_visual — OBLIGATORIO SIN EXCEPCIÓN]
        1. CERO PERSONAS: ningún ser humano, rostro, cuerpo, silueta.
        2. ESPECÍFICO AL TEMA: Si hablas de guerra en Ucrania, el prompt visual muestra infraestructura dañada o vehículos militares vacíos. Si hablas de economía, muestra puertos, refinerías, centros de datos. Si hablas de tecnología, muestra servidores, antenas, instalaciones industriales.
        3. VARIEDAD: Cada escena diferente. Alterna entre: infraestructura militar, instalaciones energéticas, puertos y rutas comerciales, centros de datos, mapas y territorios, vehículos sin conductor.
        4. ESTILO OBLIGATORIO: Termina siempre con: ", RAW photo, photojournalism, real photography, shot on location, harsh natural lighting, gritty texture, physical environment, no people, no faces, no cgi, no digital art".
        5. PROHIBIDO ABSOLUTAMENTE EN EL PROMPT: neon, glowing, hologram, digital, abstract, wireframe, sci-fi, futuristic, 3d render, concept art, particles, blue glow, network visualization, data visualization, cyber. Solo infraestructura y entornos físicos reales.
        6. PROHIBIDO: "camera", "photography", "lens", "macro". Solo describe el lugar o infraestructura.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "Monkygraff",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título táctico con dato concreto y alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "[Infraestructura física real en INGLÉS: instalación, vehículo vacío, puerto, refinería, planta energética, sin personas], RAW photo, photojournalism, real photography, shot on location, harsh natural lighting, gritty texture, no people, no faces, no cgi, no digital art",
              "pexels_query": "[2-3 palabras en INGLÉS que describan la infraestructura exacta para buscar en Pexels. Ejemplos: 'oil refinery night', 'cargo ship port', 'military base aerial', 'power plant industrial', 'pipeline aerial'. NUNCA uses palabras genéricas. Describe la infraestructura específica que aparece en la escena.]",
              "texto_locucion": "Texto en ESPAÑOL impecable. Análisis táctico directo, datos concretos, conexiones no obvias."
            }
          ]
        }
        """

    def _llamar_gemini(self, system_instruction, prompt, llaves):
        """
        Llamada a Gemini con Timeout estricto (Limpieza de cola) y Kill Switch.
        """
        modelos_prioridad = [
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-lite"
        ]
        log_errores = []
        MAX_REINTENTOS = 2
        MAX_ESPERA_SEGUNDOS = 125
        TIMEOUT_SEGUNDOS = 120

        for modelo in modelos_prioridad:
            modelo_agotado = False

            for index, key in enumerate(llaves):
                if modelo_agotado:
                    break

                # 🛑 FILTRO LOCAL
                if not self.cuotas.puede_usar_llave(index):
                    print(f"⏩ [SKIP LOCAL] Llave {index} ya consumió su cuota de hoy. Saltando.")
                    continue

                for intento in range(MAX_REINTENTOS):
                    try:
                        genai.configure(api_key=key)
                        model = genai.GenerativeModel(
                            model_name=modelo,
                            system_instruction=system_instruction,
                            generation_config={"response_mime_type": "application/json"}
                        )
                        
                        request_options = {"timeout": TIMEOUT_SEGUNDOS}

                        response = model.generate_content(
                            prompt,
                            request_options=request_options
                        )
                        
                        # ✅ ÉXITO
                        self.cuotas.registrar_exito(index)
                        print(f"[OK] Llave {index} ({modelo}) respondió correctamente.")
                        return json.loads(response.text), log_errores

                    except Exception as e:
                        error_str = str(e)

                        # --- TIME OUT: Limpieza de cola por atasco de red ---
                        if "Timeout" in error_str or "deadline exceeded" in error_str.lower() or "504" in error_str:
                            msg = f"[TIMEOUT] La Llave {index} se atascó más de {TIMEOUT_SEGUNDOS}s. Abortando reintento."
                            print(msg)
                            log_errores.append(msg)
                            break 

                        # --- ERRORES DE SERVIDOR GOOGLE (500/503): No reintentar ---
                        if "500" in error_str or "503" in error_str or "Service Unavailable" in error_str:
                            msg = f"[ERROR SERVIDOR] Google (Llave {index}) reporta caída. Abortando reintentos inútiles."
                            print(msg)
                            log_errores.append(msg)
                            break 

                        # --- CUOTA DIARIA AGOTADA ---
                        if ("PerDay" in error_str and "limit: 0" in error_str) or \
                           ("generate_content_free_tier_requests" in error_str and "limit: 0" in error_str):
                            msg = f"[SKIP MODELO] {modelo} sin cuota diaria. Saltando modelo."
                            print(msg)
                            log_errores.append(msg)
                            self.cuotas.bloquear_llave_por_agotamiento(index)
                            modelo_agotado = True
                            break

                        # --- RATE LIMIT (429): La única excepción donde sí reintentamos ---
                        if "429" in error_str:
                            match = re.search(r'seconds:\s*(\d+)', error_str)
                            espera = int(match.group(1)) if match else 60
                            espera = min(espera, MAX_ESPERA_SEGUNDOS)
                            print(f"[RATE LIMIT] Llave {index} ({modelo}) — intento {intento+1}/{MAX_REINTENTOS} — esperando {espera}s...")
                            time.sleep(espera)
                            continue  

                        # --- OTROS ERRORES ---
                        error_msg = f"Llave {index} ({modelo}): {error_str[:200]}"
                        print(f"[ERROR] {error_msg}")
                        log_errores.append(error_msg)
                        
                        # 🛑 KILL SWITCH
                        if "safety" in error_str.lower() or "finish_reason" in error_str.lower() or "400" in error_str:
                            print("🛑 [CRÍTICO] Prompt rechazado por filtros de contenido de Google. Abortando motor completo.")
                            return None, log_errores

                        break  

                else:
                    error_msg = f"Llave {index} ({modelo}): agotó reintentos sin éxito."
                    print(f"[FALLO] {error_msg}")
                    log_errores.append(error_msg)

        print("🚫 [SISTEMA BLOQUEADO] Todas las llaves están agotadas o fallaron. Orden ignorada.")
        return None, log_errores

    def generar_paquete_publicacion(self, marca, titulo, texto_locucion, formato):
        """
        Genera el paquete completo de publicación SEO optimizado para YouTube/TikTok.
        """
        llaves = self.boveda.obtener_llaves()
        if not llaves:
            return None

        es_largo = "16:9" in formato or formato.upper() == "LARGO"

        if "viuda" in marca.lower():
            canal_info = "Canal de historias de misterio, suspenso narrativo, relatos inmersivos y enigmas oscuros."
        else:
            canal_info = "Canal de análisis geopolítico táctico, conflictos internacionales, estrategia militar, inteligencia."

        if not es_largo:
            prompt_paquete = f"""
Eres un experto en SEO de YouTube y TikTok con track record de videos virales.
Canal: {marca}
Nicho: {canal_info}
Título sugerido del video: {titulo}
Guión/locución: {texto_locucion[:1500]}
Formato: SHORT 9:16 YouTube Shorts y TikTok

Genera el paquete de publicación completo. SALIDA: ÚNICAMENTE JSON válido.

{{
  "titulo_final": "Título final optimizado SEO, máximo 70 caracteres, alto CTR, con número o pregunta si aplica",
  "descripcion": "Descripción completa de al menos 300 palabras. Párrafo 1: gancho primeros 2 renglones visibles. Párrafo 2-4: desarrollo del tema con keywords naturales. Párrafo 5: llamado a la acción. Terminar con links de redes.",
  "hashtags": "#hashtag1 #hashtag2 ... máximo 15 hashtags relevantes separados por espacio",
  "keywords": "palabra1, palabra2, palabra3, ... máximo 500 caracteres, separadas por coma, ultra relevantes al tema y canal",
  "primer_comentario": "Comentario para fijar. Debe generar debate o curiosidad. Máximo 3 líneas. Termina con pregunta al espectador.",
  "prompt_hook": "Prompt cinematográfico para imagen del HOOK. Alta retención, impactante, visible. dramatic lighting, high contrast, detailed. Sin personas. En inglés."
}}
"""
        else:
            prompt_paquete = f"""
Eres un experto en SEO de YouTube y TikTok con track record de videos virales.
Canal: {marca}
Nicho: {canal_info}
Título sugerido del video: {titulo}
Guión/locución: {texto_locucion[:1500]}
Formato: VIDEO LARGO 16:9 YouTube

Genera el paquete de publicación completo. SALIDA: ÚNICAMENTE JSON válido.

INSTRUCCIONES CRÍTICAS PARA PROMPTS DE MINIATURAS:
- NUNCA generes prompts oscuros que resulten en imágenes negras
- SIEMPRE incluir: dramatic lighting, high contrast, visible details, sharp focus
- SIEMPRE incluir elementos visuales concretos y descriptivos
- PROHIBIDO: total darkness, pitch black, all black, completely dark
- Los prompts deben generar imágenes impactantes y visibles, no oscuras
- Sin personas, sin rostros, sin cuerpos humanos

{{
  "titulo_final": "Título final optimizado SEO, máximo 70 caracteres, alto CTR, con número o pregunta si aplica",
  "descripcion": "Descripción completa de al menos 300 palabras. Párrafo 1: gancho primeros 2 renglones visibles. Párrafo 2-4: desarrollo del tema con keywords naturales. Párrafo 5: llamado a la acción. Incluir timestamps. Terminar con links de redes.",
  "hashtags": "#hashtag1 #hashtag2 ... máximo 15 hashtags relevantes separados por espacio",
  "keywords": "palabra1, palabra2, palabra3, ... máximo 500 caracteres, separadas por coma, ultra relevantes al tema y canal",
  "primer_comentario": "Comentario para fijar. Debe generar debate o curiosidad. Máximo 3 líneas. Termina con pregunta al espectador.",
  "prompt_hook": "Prompt cinematográfico para imagen del HOOK. Alta retención, impactante, visible. dramatic lighting, high contrast, detailed. Sin personas. En inglés.",
  "prompt_miniatura_A": "Photorealistic dramatic scene, [elemento visual específico del tema], high contrast lighting, sharp focus, visible details, moody atmosphere, cinematic composition, no people, no faces, 8k uhd, [2-3 elementos visuales concretos relacionados al tema del video]",
  "prompt_miniatura_B": "Hyperrealistic environment, [elemento visual específico diferente], dramatic side lighting, deep shadows with visible details, atmospheric fog or mist, cinematic still, no humans, no faces, ultra detailed, [2-3 elementos visuales del tema]",
  "prompt_miniatura_C": "Photojournalism style, [elemento visual impactante del tema], harsh directional lighting, gritty realistic texture, visible and detailed composition, no people, raw documentary feel, [2-3 elementos visuales del tema]"
}}
"""

        system_pub = (
            "Eres un experto en SEO de YouTube y TikTok. "
            "Generas paquetes de publicación de alta calidad optimizados para CTR extremo y retención máxima. "
            "SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON."
        )

        resultado, errores = self._llamar_gemini(system_pub, prompt_paquete, llaves)
        return resultado

    def generar_guion(self, marca, contexto, peticion, longitud="4900 palabras", formato="16:9"):
        """
        Arquitectura unificada con entrega de errores a la UI.
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
            instruccion_ritmo = (
                f"\n\n[DIRECTRIZ DE RITMO]: Formato SHORT (9:16). "
                f"Genera entre 12 y 15 escenas para un video de 60 segundos. "
                f"CRÍTICO PARA MOTOR DE VOZ: Escribe SIEMPRE con acentos correctos del español (á, é, í, ó, ú, ñ). "
                f"PROHIBIDO escribir sin acentos. Ejemplos obligatorios: después, también, así, más, qué, cómo, están, pasó, Rusia, Dinamarca, rutas, región, Pekín."
            )
            prompt = f"CONTEXTO: {contexto}\nLONGITUD: {longitud}\nPETICIÓN: {peticion}{instruccion_ritmo}"
            resultado, errores = self._llamar_gemini(system_instruction, prompt, llaves)
            
            if resultado:
                return json.dumps(resultado, indent=4, ensure_ascii=False)
            
            return "ERROR CRÍTICO API GEMINI:\n" + "\n".join(errores)

        else:
            partes = [
                ("APERTURA",   "escenas 1 a 20  — introducción, contexto, gancho inicial"),
                ("DESARROLLO", "escenas 21 a 40 — desarrollo del conflicto, datos, tensión creciente"),
                ("CIERRE",     "escenas 41 a 60 — clímax, revelación, cierre emocional y llamado a la acción"),
            ]

            todas_las_escenas = []
            titulo = ""
            marca_final = marca
            errores_totales = []

            for i, (bloque, descripcion) in enumerate(partes):
                instruccion_bloque = (
                    f"\n\n[DIRECTRIZ DE BLOQUE {i+1}/3]: "
                    f"Genera SOLO el bloque de {descripcion}. "
                    f"Exactamente 20 escenas numeradas desde {i*20+1} hasta {(i+1)*20}. "
                    f"Formato 16:9 video largo de 30 MINUTOS. "
                    f"OBLIGATORIO: cada texto_locucion debe tener MÍNIMO 75 palabras en español — es narración continua y densa, no frases cortas. "
                    f"CRÍTICO PARA MOTOR DE VOZ: Escribe SIEMPRE con acentos correctos (á, é, í, ó, ú, ñ). PROHIBIDO escribir sin acentos. "
                    f"NO generes título ni estructura completa, solo las escenas de este bloque."
                )
                prompt = f"CONTEXTO: {contexto}\nPETICIÓN: {peticion}{instruccion_bloque}"
                print(f"[AI ENGINE] Generando bloque {i+1}/3: {bloque}...")
                
                resultado, errores = self._llamar_gemini(system_instruction, prompt, llaves)

                if resultado:
                    if i == 0 and "titulo_sugerido" in resultado:
                        titulo = resultado.get("titulo_sugerido", "")
                        marca_final = resultado.get("marca", marca)
                    escenas_bloque = resultado.get("escenas", [])
                    todas_las_escenas.extend(escenas_bloque)
                else:
                    print(f"[AI ENGINE] ⚠️ Bloque {i+1} falló...")
                    errores_totales.extend(errores)

            if not todas_las_escenas:
                return "ERROR CRÍTICO API GEMINI:\n" + "\n".join(errores_totales)

            guion_final = {
                "marca": marca_final,
                "formato": "LARGO",
                "titulo_sugerido": titulo,
                "escenas": todas_las_escenas
            }
            return json.dumps(guion_final, indent=4, ensure_ascii=False)
