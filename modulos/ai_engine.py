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
        tz_pt = timezone(timedelta(hours=-7))
        return datetime.now(tz_pt).strftime("%Y-%m-%d")

    def _cargar_estado(self):
        fecha_actual = self._obtener_fecha_pt_actual()
        if os.path.exists(self.archivo_bd):
            try:
                with open(self.archivo_bd, "r") as f:
                    data = json.load(f)
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

        # ══════════════════════════════════════════════════════════════
        # ADN Maestro: La Viuda (Silo Hermético 1) - ACTUALIZACIÓN TERROR
        # ══════════════════════════════════════════════════════════════
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
        1. CERO HUMANOS IDENTIFICABLES O ROSTROS: PROHIBIDO mostrar personas normales, caras claras o cuerpos humanos estándar.
        2. AUTORIZACIÓN DE PRESENCIAS TERRORÍFICAS: SE PERMITEN Y FOMENTAN siluetas inhumanas, formas humanoides distorsionadas hechas de sombra, entidades espectrales indistinctas, manos sombrías que se asoman, ojos acechando en la oscuridad absoluta y cualquier figura que evoque pareidolia perturbadora (ver formas amenazantes en objetos inanimados). Deben parecer "algo más", no personas.
        3. ANCLAJE NARRATIVO ESTRICTO Y OBJETUAL: El prompt_visual DEBE ilustrar el tema de la locución enfocándose en el DETALLE MÁS INQUIETANTE u OBJETO anómalo mencionado. Si el guion habla de "presencias", dibuja la silueta distorsionada. Si habla de "ruidos", dibuja el objeto que lo causa de forma amenazante.
        4. ATMÓSFERA OPRESIVA: Enfatiza la oscuridad absoluta, el contraste extremo (claroscuro), texturas granulosas de film antiguo, y la paleta Noir (negros profundos, rojos saturados).
        5. VARIEDAD OBLIGATORIA: Cada escena debe ser visualmente distinta a la anterior. Prohibido repetir pasillos o cuartos vacíos genéricos si el guion no lo exige.
        6. PROHIBIDO DIBUJAR CÁMARAS: NUNCA uses "camera", "CCTV", "dashcam", "photography" o "lens".
        7. SINTAXIS BASE: Escribe la descripción en INGLÉS puro, separando conceptos por comas. El worker añadirá el estilo Noir automáticamente.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "La Viuda",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título viral de terror psicológico con alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "[Detalle perturbador, silueta inhumana u objeto amenazante en INGLÉS, separando conceptos por comas]",
              "pexels_query": "[2-3 palabras en INGLÉS del objeto EXACTO de esta escena]",
              "texto_locucion": "Texto en ESPAÑOL impecable. Terror psicológico puro."
            }
          ]
        }
        """

        # ══════════════════════════════════════════════════════════════
        # ADN Maestro: Monkygraff (Silo Hermético 2)
        # ══════════════════════════════════════════════════════════════
        self.adn_monkygraff = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "MONKYGRAFF"]
        ERES EL ANALISTA GEOPOLÍTICO Y ECONÓMICO MÁS AGUDO DE HABLA HISPANA EN YOUTUBE.
        TU MISIÓN: REVELAR LAS CONEXIONES QUE LOS MEDIOS MAINSTREAM NO HACEN.
        HABLAS DE PODER REAL, DINERO REAL Y MOVIMIENTOS QUE CAMBIAN EL MUNDO ANTES DE QUE NADIE LO NOTE.

        PILARES TEMÁTICOS — ESTOS SON LOS TEMAS QUE DOMINAN EL ALGORITMO EN 2026:

        PILAR 1 — GUERRA Y CONFLICTOS ACTIVOS:
        - Guerra Rusia-Ucrania: movimientos tácticos, minerales estratégicos, negociaciones secretas
        - Israel-Gaza-Irán: escaladas, alianzas regionales, impacto en petróleo
        - China vs Taiwán: ejercicios militares, bloqueos, escenarios de invasión
        - Venezuela: operaciones encubiertas de EE.UU., control del petróleo
        - Sahel africano: yihadismo, minerales críticos, retirada francesa
        - Mar Rojo: ataques Houthi, rutas comerciales globales afectadas

        PILAR 2 — GUERRA ECONÓMICA Y PODER:
        - Aranceles de Trump: impacto real en México, América Latina y cadenas de suministro
        - Guerra comercial EE.UU.-China: quién gana, quién pierde
        - BRICS vs dólar: desdolarización, yuan digital, nueva arquitectura financiera
        - Minerales críticos: litio, cobalto, tierras raras
        - Energía como arma: gas, petróleo, gasoductos

        PILAR 3 — TECNOLOGÍA Y PODER:
        - IA como arma geopolítica: EE.UU. vs China, chips, DeepSeek
        - Guerra de semiconductores
        - Ciberataques de estado: Rusia, China, Corea del Norte
        - Drones militares
        - Vigilancia masiva

        PILAR 4 — AMERICA LATINA EN EL TABLERO:
        - Trump y América Latina: amenazas, aranceles, intervenciones
        - Narcoestados: carteles como actores geopolíticos
        - Elecciones clave 2026
        - Recursos naturales latinoamericanos

        PILAR 5 — RECONFIGURACIÓN DEL ORDEN MUNDIAL:
        - El fin del unipolarismo americano
        - La nueva OTAN: rearmamiento europeo
        - Turquía, India, África como nuevos actores

        REGLAS DE ESTILO (INQUEBRANTABLES PARA MOTOR DE VOZ):
        1. TONO: Analista táctico. Informativo, seco, basado en datos.
        2. HOOKS DINÁMICOS: cada video debe abrir de forma DIFERENTE y ESPECÍFICA al tema tratado. PROHIBIDO usar "en las últimas 72 horas", "esto pasó hace poco", "lo que nadie te dijo", o cualquier frase genérica de urgencia. El gancho debe contener un DATO CONCRETO del tema: una cifra, un nombre, un lugar, un movimiento específico. Ejemplos válidos por tema (varía siempre): para guerra usa "Tres divisiones rusas cruzaron el Donetsk esta semana"; para economía usa "El yuan superó al dólar en pagos asiáticos"; para tecnología usa "China bloqueó la exportación de galio a Estados Unidos"; para LATAM usa "Trump anunció aranceles del 25% a México"; para orden mundial usa "Cuatro países dejaron de aceptar dólares para petróleo". El hook NUNCA se repite entre videos.
        3. DATOS CONCRETOS: Siempre incluye cifras, fechas, nombres de países reales.
        4. ORTOGRAFÍA PERFECTA PARA TTS: español neutro impecable. PROHIBIDO emojis, asteriscos, corchetes en texto_locucion.
        5. MONETIZACIÓN: PROHIBIDO lenguaje bélico explícito, incitación a violencia, gore.

        [REGLAS CRÍTICAS PARA prompt_visual]
        1. CERO PERSONAS: ningún ser humano, rostro, cuerpo, silueta.
        2. ESPECÍFICO AL TEMA: infraestructura dañada, vehículos militares vacíos, puertos, refinerías.
        3. VARIEDAD: Cada escena diferente.
        4. ESTILO: ", RAW photo, photojournalism, real photography, shot on location, harsh natural lighting, gritty texture, physical environment, no people, no faces, no cgi, no digital art"
        5. PROHIBIDO: neon, glowing, hologram, digital, abstract, wireframe, sci-fi, futuristic, 3d render.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "Monkygraff",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título táctico con dato concreto y alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "[Infraestructura física real en INGLÉS: instalación, vehículo vacío, puerto, refinería], RAW photo, photojournalism, real photography, shot on location, harsh natural lighting, gritty texture, no people, no faces, no cgi, no digital art",
              "pexels_query": "[2-3 palabras en INGLÉS de la infraestructura exacta]",
              "texto_locucion": "Texto en ESPAÑOL impecable. Análisis táctico directo, datos concretos."
            }
          ]
        }
        """

        # ══════════════════════════════════════════════════════════════
        # ADN Maestro: FiltradoMX (Silo Hermético 3)
        # ══════════════════════════════════════════════════════════════
        self.adn_filtrado_mx = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "FILTRADO MX"]
        ERES EL ARCHIVO QUE HABLA. NARRAS CONFESIONES ANÓNIMAS REALES TOMADAS DE REDDIT,
        FOROS Y CHATS FILTRADOS. DRAMAS HUMANOS, INFIDELIDADES, TRAICIONES, SECRETOS LABORALES,
        CONFLICTOS FAMILIARES.

        IDENTIDAD NARRATIVA:
        No eres un locutor de radio ni un narrador de podcast.
        Eres la persona en la oficina que sabe todo el chisme y te lo cuenta como si fuera un secreto —
        con pausas, con énfasis, con "espérate que esto se pone mejor".
        Tono coloquial mexicano, neutral, directo, sin vulgaridades.
        Audiencia: México y Latinoamérica, todas las edades.

        ESTRUCTURA OBLIGATORIA POR VIDEO:
        1. HOOK (0-15s): El dato más escandaloso primero, sin contexto. Que obligue a seguir escuchando.
           NO hay introducción. Entras directo al chisme. La primera línea ES el gancho.
        2. CONTEXTO (15-60s): Quién, dónde, cuándo — mínimo de palabras, máximo de intriga.
        3. DESARROLLO: Drama en capas. Cada párrafo escala la tensión. Nunca resuelvas antes del final.
        4. GIRO OBLIGATORIO: Una revelación inesperada que nadie vio venir. Sin excepción.
        5. CIERRE: Pregunta directa a la audiencia que genere debate en comentarios.

        REGLAS DURAS (INQUEBRANTABLES):
        - CERO nombres reales de personas identificables
        - CERO lugares específicos que permitan identificar a alguien
        - Cada historia diferente en tono, ritmo y estructura — nunca repitas fórmulas
        - Lenguaje coloquial mexicano sin groserías explícitas (family friendly)
        - Mínimo UN GIRO por video, sin excepción
        - El hook debe poder funcionar como título del video
        - Videos largos: 1200-1500 palabras en texto_locucion total
        - Shorts: 130-150 palabras, UN SOLO momento WTF concentrado

        LÉXICO PERMITIDO (natural, no forzado):
        "wey", "no manches", "chale", "neta", "de volada", "a huevo", "qué onda",
        "sale pues", "órale", "ni modo", "eso sí estuvo cañón"

        REGLAS DE ESTILO PARA MOTOR DE VOZ (TTS):
        1. VOZ FEMENINA: cómplice, íntima, como contando un secreto a una amiga de confianza.
        2. RITMO: varía entre rápido (en las partes de tensión) y pausado (en el giro).
        3. ORTOGRAFÍA PERFECTA: español mexicano con acentos correctos (á, é, í, ó, ú, ñ).
        4. PROHIBIDO en texto_locucion: emojis, asteriscos, corchetes, hashtags, signos raros.
        5. USA puntos suspensivos (...) para crear pausas dramáticas naturales en el TTS.

        [REGLAS CRÍTICAS PARA prompt_visual]
        FiltradoMX usa IMÁGENES MINIMALISTAS que sugieren cotidianidad y drama sin mostrar personas.
        1. CERO PERSONAS: ningún ser humano, rostro, cuerpo, silueta.
        2. OBJETOS COTIDIANOS CON CARGA EMOCIONAL: teléfonos con notificaciones, mesas de café,
           cuartos de hotel, conversaciones de chat en pantalla (sin texto legible), ropa tirada,
           maletas, llaves, documentos borrosos.
        3. ILUMINACIÓN: cálida y naturalista. No oscura ni de terror. Es drama humano, no horror.
        4. ESTILO: ", RAW photo, candid photography, warm natural lighting, shallow depth of field,
           everyday objects, emotional atmosphere, no people, no faces, photorealistic, film grain"
        5. PROHIBIDO: neon, glowing, cartoon, illustrated, dark horror, crime scene.
        6. pexels_query en INGLÉS, 2-3 palabras descriptivas del objeto/ambiente de la escena.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "FiltradoMX",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título de alto CTR estilo chisme revelador — sin spoiler del giro",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "[Objeto cotidiano con carga emocional en INGLÉS], RAW photo, candid photography, warm natural lighting, shallow depth of field, everyday objects, emotional atmosphere, no people, no faces, photorealistic, film grain",
              "pexels_query": "[2-3 palabras en INGLÉS del objeto o ambiente de la escena]",
              "texto_locucion": "Texto en ESPAÑOL mexicano coloquial. Sin groserías. Con acentos correctos. Pausas con puntos suspensivos."
            }
          ]
        }
        """

        # ══════════════════════════════════════════════════════════════
        # ADN Maestro: LaesquinaRandom (Silo Hermético 4)
        # ══════════════════════════════════════════════════════════════
        self.adn_laesquina_random = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "LAESQUINARANDOM"]
        ERES UN COMEDIANTE CALLEJERO MEXICANO QUE NARRA SITUACIONES ABSURDAS Y RIDÍCULAS
        DEL DÍA A DÍA. TU HUMOR ES FÍSICO, EXAGERADO Y UNIVERSALMENTE RECONOCIBLE.
        FAMILIA FRIENDLY. JAMÁS GROSERÍAS EXPLÍCITAS.

        IDENTIDAD NARRATIVA:
        Piensa en alguien que te cuenta una historia y no puede evitar reírse mientras la narra.
        Tu tono es el de una anécdota que se sale de control. Vas escalando el absurdo.
        Cada párrafo es más ridículo que el anterior. El remate llega cuando menos se espera.

        ESTRUCTURA OBLIGATORIA:
        1. HOOK ABSURDO (0-3s): Exposición INMEDIATA de la situación ridícula. Cero introducciones.
           La primera línea es tan random y específica que el espectador NO puede no reírse o curiosear.
           Ejemplo: "La vez que el Brayan intentó empeñar un tinaco rotoplas en el monte de piedad..."
        2. ESCALADA DE CAOS: La situación empeora de forma progresiva y lógica dentro del absurdo.
           Cada paso de la historia debe ser peor (o más ridículo) que el anterior.
        3. REMATE (PUNCHLINE): Resolución cómica y abrupta. Inesperada pero que en retrospectiva
           tenía sentido. El tipo de final que hace decir "no puede ser".

        REGLAS DURAS:
        - Cero groserías explícitas — humor físico y situacional, no vulgar
        - Cero nombres reales de personas identificables
        - Situaciones cotidianas mexicanas: mercado, vecindario, tráfico, familia, trabajo informal
        - El absurdo debe ser ESPECÍFICO — los detalles raros son los que generan la risa
        - Léxico: "wey", "no manches", "chale", "órale", "sale", "neta que sí"
        - Videos largos: 800-1000 palabras de comedia progresiva
        - Shorts: 80-120 palabras, UNA situación absurda completa con remate incluido

        REGLAS DE ESTILO PARA MOTOR DE VOZ (TTS):
        1. VOZ MASCULINA: energética, cómica, como si estuviera aguantando la risa.
        2. RITMO: rápido en la escalada, pausado justo antes del remate (para el timing cómico).
        3. ORTOGRAFÍA PERFECTA: español mexicano con acentos correctos.
        4. PROHIBIDO en texto_locucion: emojis, asteriscos, corchetes, hashtags.
        5. USA puntos suspensivos (...) en el momento justo antes del remate para crear timing cómico.
        6. EXCLAMACIONES con moderación — solo donde la situación lo justifique.

        [REGLAS CRÍTICAS PARA prompt_visual — ESTÉTICA CARTOON 2D OBLIGATORIA]
        LaesquinaRandom USA ILUSTRACIÓN CÓMICA, NO FOTORREALISMO. Este canal tiene identidad visual propia.

        ESTILO VISUAL OBLIGATORIO:
        - Funny cartoon style, 2D animation, vibrant flat colors, comic book aesthetic
        - Expressive caricature, exaggerated facial expressions (SIN personas reales)
        - Humorous situation implied, vibrant lighting, cel shaded
        - Escenas domésticas o callejeras mexicanas en estilo cartoon

        PROMPT POSITIVO BASE (agregar siempre al final):
        ", funny cartoon style, 2D animation, vibrant flat colors, comic book aesthetic,
        expressive illustration, humorous situation, vibrant lighting, cel shaded,
        no photorealism, no dark tones, colorful"

        PROMPT NEGATIVO (el worker debe aplicar esto como negative_prompt):
        "photorealistic, realistic, 3d render, hyperrealistic, photography, raw photo,
        dark, gloomy, horror, serious, monochrome, anime, manga, text, watermark,
        deformed, bad anatomy, blurry"

        REGLAS DE prompt_visual:
        1. Describe la SITUACIÓN CÓMICA de esa escena específica en estilo cartoon, sin personas reales.
        2. Objetos y entornos mexicanos reconocibles: tianguis, vecindad, combi, taquería, mercado.
        3. PROHIBIDO: personas reales, fotorrealismo, oscuridad, horror.
        4. pexels_query NO APLICA para este canal — siempre pon "cartoon mexican street scene"
           porque las imágenes se generan con Stable Diffusion, no con Pexels.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "LaesquinaRandom",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título cómico y específico — el detalle absurdo que genera curiosidad",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "[Situación cómica o entorno mexicano en INGLÉS, estilo cartoon], funny cartoon style, 2D animation, vibrant flat colors, comic book aesthetic, expressive illustration, humorous situation, vibrant lighting, cel shaded, no photorealism",
              "pexels_query": "cartoon mexican street scene",
              "texto_locucion": "Texto en ESPAÑOL mexicano coloquial. Cómico, energético. Con timing. Sin groserías."
            }
          ]
        }
        """

    def _llamar_gemini(self, system_instruction, prompt, llaves):
        """
        Llamada a Gemini con Timeout estricto y Kill Switch.
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
                        response = model.generate_content(prompt, request_options=request_options)
                        self.cuotas.registrar_exito(index)
                        print(f"[OK] Llave {index} ({modelo}) respondió correctamente.")
                        return json.loads(response.text), log_errores

                    except Exception as e:
                        error_str = str(e)

                        if "Timeout" in error_str or "deadline exceeded" in error_str.lower() or "504" in error_str:
                            msg = f"[TIMEOUT] La Llave {index} se atascó más de {TIMEOUT_SEGUNDOS}s. Abortando reintento."
                            print(msg); log_errores.append(msg); break

                        if "500" in error_str or "503" in error_str or "Service Unavailable" in error_str:
                            msg = f"[ERROR SERVIDOR] Google (Llave {index}) reporta caída."
                            print(msg); log_errores.append(msg); break

                        if ("PerDay" in error_str and "limit: 0" in error_str) or \
                           ("generate_content_free_tier_requests" in error_str and "limit: 0" in error_str):
                            msg = f"[SKIP MODELO] {modelo} sin cuota diaria."
                            print(msg); log_errores.append(msg)
                            self.cuotas.bloquear_llave_por_agotamiento(index)
                            modelo_agotado = True; break

                        if "429" in error_str:
                            match = re.search(r'seconds:\s*(\d+)', error_str)
                            espera = int(match.group(1)) if match else 60
                            espera = min(espera, MAX_ESPERA_SEGUNDOS)
                            print(f"[RATE LIMIT] Llave {index} ({modelo}) — intento {intento+1}/{MAX_REINTENTOS} — esperando {espera}s...")
                            time.sleep(espera); continue

                        error_msg = f"Llave {index} ({modelo}): {error_str[:200]}"
                        print(f"[ERROR] {error_msg}"); log_errores.append(error_msg)

                        if "safety" in error_str.lower() or "finish_reason" in error_str.lower() or "400" in error_str:
                            print("🛑 [CRÍTICO] Prompt rechazado por filtros de contenido de Google.")
                            return None, log_errores
                        break

                else:
                    error_msg = f"Llave {index} ({modelo}): agotó reintentos sin éxito."
                    print(f"[FALLO] {error_msg}"); log_errores.append(error_msg)

        print("🚫 [SISTEMA BLOQUEADO] Todas las llaves están agotadas o fallaron.")
        return None, log_errores

    def _seleccionar_adn(self, marca):
        """
        Selector centralizado de ADN por canal.
        Agregar nuevos canales aquí — un solo lugar para mantener.
        """
        marca_lower = marca.lower()
        if "viuda" in marca_lower:
            return self.adn_la_viuda
        elif "monkygraff" in marca_lower:
            return self.adn_monkygraff
        elif "filtrado" in marca_lower or "filtradmx" in marca_lower or "filtrado mx" in marca_lower:
            return self.adn_filtrado_mx
        elif "esquina" in marca_lower or "laesquina" in marca_lower or "random" in marca_lower:
            return self.adn_laesquina_random
        else:
            print(f"[AI ENGINE] ⚠️ ERROR: Canal '{marca}' sin ADN registrado. Verifica el nombre del canal.")
            return None

    def generar_paquete_publicacion(self, marca, titulo, texto_locucion, formato):
        """
        Genera el paquete completo de publicación SEO optimizado para YouTube/TikTok.
        """
        llaves = self.boveda.obtener_llaves()
        if not llaves:
            return None

        es_largo = "16:9" in formato or formato.upper() == "LARGO"

        # Descripción del nicho por canal
        nicho_map = {
            "viuda": "Canal de historias de misterio, suspenso narrativo, relatos inmersivos y enigmas oscuros.",
            "monkygraff": "Canal de análisis geopolítico táctico, conflictos internacionales, estrategia militar, inteligencia.",
            "filtrado": "Canal de confesiones anónimas, dramas humanos reales, chismes verificados y situaciones escandalosas.",
            "esquina": "Canal de comedia absurda mexicana, situaciones ridículas del día a día, humor familiar.",
        }
        canal_info = "Canal de contenido viral para audiencia latinoamericana."
        for key, desc in nicho_map.items():
            if key in marca.lower():
                canal_info = desc
                break

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
  "titulo_final": "Título final optimizado SEO, máximo 70 caracteres, alto CTR",
  "descripcion": "Descripción completa de al menos 300 palabras.",
  "hashtags": "#hashtag1 #hashtag2 ... máximo 15 hashtags relevantes",
  "keywords": "palabra1, palabra2, ... máximo 500 caracteres",
  "primer_comentario": "Comentario para fijar. Termina con pregunta al espectador.",
  "prompt_hook": "Prompt para imagen de hook. Ultra detallado, high contrast, dramatic lighting, no people, en inglés."
}}
"""
        else:
            # Identidad visual por canal — solo referencia de ADN, Gemini genera libremente
            adn_canales = {
                "viuda": {
                    "paleta": "deep black, blood red accent, dark teal shadows",
                    "estilo": "psychological horror, dread, unsettling stillness, analog film grain",
                    "reglas": "sin personas reales, sin texto, siluetas permitidas, máximo contraste rojo-negro"
                },
                "monkygraff": {
                    "paleta": "steel gray, urgent orange, deep navy",
                    "estilo": "tactical urgency, geopolitical tension, documentary realism, gritty RAW photo",
                    "reglas": "sin personas, objetos físicos reales del tema, mapas, infraestructura"
                },
                "filtrado": {
                    "paleta": "warm beige, soft amber, muted shadows",
                    "estilo": "intimate drama, human tension, candid emotional",
                    "reglas": "sin personas reconocibles, objetos cotidianos con carga emocional"
                },
                "esquina": {
                    "paleta": "vibrant yellow, electric blue, warm red",
                    "estilo": "funny cartoon 2D, comic book, cel shaded, mexican street culture",
                    "reglas": "ilustración caricaturesca, sin realismo fotográfico"
                }
            }
            adn = adn_canales.get("viuda")  # default
            for key, val in adn_canales.items():
                if key in marca.lower():
                    adn = val
                    break

            prompt_paquete = f"""
Eres un director creativo especialista en miniaturas de YouTube con CTR demostrado superior al 15%.
Analizas el tema real del video y generas prompts de imagen ÚNICOS, ESPECÍFICOS y de alto impacto visual.

CANAL: {marca}
NICHO: {canal_info}
TÍTULO: {titulo}
GUION COMPLETO: {texto_locucion}

ADN VISUAL DEL CANAL:
- Paleta: {adn['paleta']}
- Estilo: {adn['estilo']}
- Reglas: {adn['reglas']}

INSTRUCCIONES PARA LOS PROMPTS DE MINIATURA:
1. Extrae el ELEMENTO MÁS IMPACTANTE Y ESPECÍFICO del tema real del video (no genérico)
2. Cada prompt debe evocar curiosidad, urgencia o impacto emocional inmediato
3. Composiciones diferentes entre A, B y C — no repetir estructura
4. Todos los prompts en INGLÉS, optimizados para Stable Diffusion
5. Incluir: iluminación dramática, profundidad de campo, calidad cinemática
6. NO incluir texto, personas identificables ni logos

SALIDA: ÚNICAMENTE JSON válido.

{{
  "titulo_final": "Título SEO optimizado, máximo 70 caracteres, con gancho emocional",
  "descripcion": "Descripción 300+ palabras optimizada para SEO y retención.",
  "hashtags": "máximo 15 hashtags separados por espacio",
  "keywords": "máximo 500 caracteres separadas por coma",
  "primer_comentario": "Comentario que genera debate inmediato. Termina con pregunta provocadora.",
  "prompt_hook": "Prompt SD para imagen de hook — objeto o lugar MÁS icónico del tema real, ultra detallado, {adn['paleta'].split(',')[0]}, dramatic lighting, no people, photorealistic, en inglés",
  "prompt_miniatura_A": "Prompt SD completo para miniatura A — COMPOSICIÓN IMPACTO: elemento focal del tema real del video con máximo dramatismo, {adn['paleta']}, {adn['estilo']}, extreme contrast, cinematic depth of field, no humans, no text, 1920x1080, ultra detailed",
  "prompt_miniatura_B": "Prompt SD completo para miniatura B — COMPOSICIÓN TENSIÓN: ángulo diferente a A, mismo tema desde perspectiva que genere urgencia o intriga, {adn['paleta']}, {adn['estilo']}, harsh rim lighting, no people, 1920x1080, photorealistic",
  "prompt_miniatura_C": "Prompt SD completo para miniatura C — COMPOSICIÓN DETALLE: macro extremo del elemento más simbólico del tema, {adn['paleta'].split(',')[0]}, ultra sharp focus, {adn['estilo']}, no humans, no text, 1920x1080"
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

        system_instruction = self._seleccionar_adn(marca)

        # ══════════════════════════════════════════════════════
        # TABLA DE DURACIONES — cada longitud define su propio
        # número de escenas, palabras/escena y bloques Gemini
        # ══════════════════════════════════════════════════════
        num_palabras_pedidas = 0
        try:
            num_palabras_pedidas = int(''.join(filter(str.isdigit, longitud.split()[0])))
        except Exception:
            pass

        # Short (9:16) — siempre 1 bloque
        es_largo = "16:9" in formato or num_palabras_pedidas >= 1500

        if not es_largo:
            # SHORT: 25-30 escenas, 7-9 palabras c/u, 200-240 total
            instruccion_ritmo = (
                f"\n\n========================================\n"
                f"REGLAS NUMERICAS OBLIGATORIAS - FORMATO SHORT 9:16\n"
                f"========================================\n"
                f"1. NUMERO DE ESCENAS: DEBES generar entre 25 y 30 escenas. Ni una menos.\n"
                f"2. PALABRAS POR ESCENA: cada campo texto_locucion debe tener EXACTAMENTE entre 7 y 9 palabras.\n"
                f"3. TOTAL DE PALABRAS DEL GUION: entre 200 y 240 palabras sumando todas las escenas.\n"
                f"4. NO generes parrafos largos. Frases cortas y directas.\n"
                f"5. Acentos del español OBLIGATORIOS: á, é, í, ó, ú, ñ.\n"
                f"========================================\n"
                f"VALIDACION INTERNA antes de responder:\n"
                f"- Cuenta las escenas que generaste. Si son menos de 25, REGENERA.\n"
                f"- Cuenta las palabras de cada texto_locucion. Si alguna tiene mas de 9, divide.\n"
                f"- Cuenta las palabras totales. Si son menos de 200, agrega mas escenas.\n"
                f"========================================"
            )
            prompt = f"{instruccion_ritmo}\n\nCONTEXTO: {contexto}\nPETICIÓN: {peticion}"
            resultado, errores = self._llamar_gemini(system_instruction, prompt, llaves)
            if resultado:
                resultado["marca"] = marca
                return json.dumps(resultado, indent=4, ensure_ascii=False)
            return "ERROR CRÍTICO API GEMINI:\n" + "\n".join(errores)

        else:
            # ── Configuración por duración solicitada ────────
            if num_palabras_pedidas <= 1500:
                # ~15 min: 2 bloques × 10 escenas, 50 palabras/escena
                config_bloques = [
                    ("APERTURA Y DESARROLLO", "escenas 1 a 10  — gancho, contexto y desarrollo del tema"),
                    ("CIERRE",                "escenas 11 a 20 — clímax, datos clave y llamado a la acción"),
                ]
                escenas_por_bloque = 10
                palabras_por_escena = 50
                min_aprox = 15
            elif num_palabras_pedidas <= 2800:
                # ~28 min: 2 bloques × 18 escenas, 70 palabras/escena
                config_bloques = [
                    ("APERTURA Y DESARROLLO", "escenas 1 a 18  — gancho, contexto, conflicto y desarrollo"),
                    ("CIERRE",                "escenas 19 a 36 — escalada, revelación y llamado a la acción"),
                ]
                escenas_por_bloque = 18
                palabras_por_escena = 70
                min_aprox = 28
            else:
                # ~45 min: 3 bloques × 20 escenas, 75 palabras/escena (original)
                config_bloques = [
                    ("APERTURA",   "escenas 1 a 20  — introducción, contexto, gancho inicial"),
                    ("DESARROLLO", "escenas 21 a 40 — desarrollo del conflicto, datos, tensión creciente"),
                    ("CIERRE",     "escenas 41 a 60 — clímax, revelación, cierre emocional y llamado a la acción"),
                ]
                escenas_por_bloque = 20
                palabras_por_escena = 75
                min_aprox = 45

            todas_las_escenas = []
            titulo = ""
            marca_final = marca
            errores_totales = []
            offset = 0

            for i, (bloque, descripcion) in enumerate(config_bloques):
                inicio = offset + 1
                fin    = offset + escenas_por_bloque
                instruccion_bloque = (
                    f"\n\n[DIRECTRIZ DE BLOQUE {i+1}/{len(config_bloques)}]: "
                    f"Genera SOLO el bloque de {descripcion}. "
                    f"Exactamente {escenas_por_bloque} escenas numeradas desde {inicio} hasta {fin}. "
                    f"Formato 16:9 video largo de {min_aprox} MINUTOS. "
                    f"OBLIGATORIO: cada texto_locucion debe tener MÍNIMO {palabras_por_escena} palabras en español. "
                    f"CRÍTICO PARA MOTOR DE VOZ: Escribe SIEMPRE con acentos correctos (á, é, í, ó, ú, ñ). "
                    f"NO generes título ni estructura completa, solo las escenas de este bloque."
                )
                prompt = f"CONTEXTO: {contexto}\nPETICIÓN: {peticion}{instruccion_bloque}"
                print(f"[AI ENGINE] Generando bloque {i+1}/{len(config_bloques)}: {bloque} ({min_aprox} min)...")

                resultado, errores = self._llamar_gemini(system_instruction, prompt, llaves)

                if resultado:
                    if i == 0 and "titulo_sugerido" in resultado:
                        titulo = resultado.get("titulo_sugerido", "")
                        marca_final = marca
                    escenas_bloque = resultado.get("escenas", [])
                    todas_las_escenas.extend(escenas_bloque)
                    offset += escenas_por_bloque
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
