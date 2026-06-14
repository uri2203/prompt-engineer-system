import google.generativeai as genai
from modulos.boveda import BovedaManager
import json
import re
import time
import os
from datetime import datetime, timedelta, timezone

def _generar_hooks_respaldo(titulo, escenas, marca="", objetivo=3):
    """Red de seguridad: si Gemini no devuelve hooks, los genera a partir del
    título y las escenas. Así los hooks NUNCA quedan vacíos. 'objetivo' = cuántos."""
    hooks = []
    t = (titulo or "").strip()
    # Hook 1: pregunta directa basada en el título
    if t:
        hooks.append(f"¿Sabías esto sobre {t.split(':')[0][:35]}?")
    # Hook 2: del texto de la primera escena (la frase de apertura)
    try:
        primer_texto = ""
        for e in (escenas or []):
            primer_texto = e.get("texto_locucion") or e.get("texto") or ""
            if primer_texto:
                break
        if primer_texto:
            frase = primer_texto.strip().split(".")[0][:45]
            if frase:
                hooks.append(frase if frase.endswith(("?", "!")) else frase + "...")
    except Exception:
        pass
    # Hook 3: genérico de tensión según marca
    genericos = {
        "La Viuda": "Lo que viene te va a perturbar.",
        "Monkygraff": "Esto cambia todo lo que creías.",
        "FiltradoMX": "Nadie esperaba este final.",
        "LaesquinaRandom": "No vas a creer lo que sigue.",
        "TuIALista": "Esto apenas está comenzando.",
    }
    hooks.append(genericos.get(marca, "Quédate hasta el final."))
    # Si se necesitan más (videos largos), generar re-hooks desde las escenas
    if objetivo > 3:
        try:
            rotativos = [
                "Pero esto fue solo el comienzo.",
                "Lo que pasó después nadie lo vio venir.",
                "Y entonces todo cambió.",
                "Aquí es donde se pone interesante.",
                "Presta atención a este detalle.",
                "Esto es lo que nadie te cuenta.",
                "El giro que no esperabas.",
                "Quédate, porque ahora viene lo fuerte.",
            ]
            for e in (escenas or []):
                if len(hooks) >= objetivo:
                    break
                txt = (e.get("texto_locucion") or e.get("texto") or "").strip()
                if txt and len(txt.split()) >= 4:
                    frase = txt.split(".")[0][:45].strip()
                    if frase and frase + "..." not in hooks:
                        hooks.append(frase + "...")
            ri = 0
            while len(hooks) < objetivo:
                hooks.append(rotativos[ri % len(rotativos)])
                ri += 1
        except Exception:
            pass
    hooks = [h.strip() for h in hooks if h and h.strip()][:max(3, objetivo)]
    while len(hooks) < min(3, objetivo):
        hooks.append("No te lo puedes perder.")
    return hooks


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

        CAMPO "hooks" OBLIGATORIO: Debes incluir SIEMPRE el campo "hooks" con exactamente 3 frases
        cortas (máximo 6 palabras cada una) específicas al tema de ESTE video.
        Estas frases se usarán como pausas dramáticas dentro del video.
        NO uses frases genéricas — deben referirse al contenido específico del guion.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "La Viuda",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título viral de terror psicológico con alto CTR",
          "hooks": [
            "OBLIGATORIO: frase de pausa dramática específica al tema de ESTE video, máximo 6 palabras, sin signos de puntuación extraños",
            "OBLIGATORIO: segunda frase de gancho específica al tema de ESTE video, máximo 6 palabras",
            "OBLIGATORIO: tercera frase de tensión específica al tema de ESTE video, máximo 6 palabras"
          ],
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
        [SISTEMA — SILO MONKYGRAFF | ANALISTA GEOPOLÍTICO DE ALTO IMPACTO]

        IDENTIDAD: Eres el analista geopolítico y económico más agudo de habla hispana.
        Revelas las conexiones que los medios mainstream ignoran o suavizan.
        Hablas de poder real, dinero real y movimientos que reconfiguran el mundo
        antes de que el ciudadano promedio lo note. Tu voz es fría, táctica, sin alarmar —
        como un general que explica el tablero sin perder la calma.

        ═══════════════════════════════════════════════
        PILARES TEMÁTICOS — ALGORITMO 2026
        ═══════════════════════════════════════════════

        GUERRA Y CONFLICTOS ACTIVOS
        Rusia-Ucrania: minerales estratégicos, movimientos tácticos, negociaciones en sombra.
        Israel-Gaza-Irán: escaladas regionales, alianzas silenciosas, impacto en petróleo.
        China-Taiwán: bloqueos navales, ejercicios de invasión, respuesta de Washington.
        Sahel africano: retiro francés, avance ruso, minerales críticos en juego.
        Mar Rojo: corte de rutas comerciales, impacto en precios globales.

        GUERRA ECONÓMICA Y PODER FINANCIERO
        Aranceles y guerras comerciales: cadenas de suministro rotas, ganadores ocultos.
        BRICS vs dólar: desdolarización real, yuan digital, nueva arquitectura financiera.
        Minerales críticos: litio, cobalto, tierras raras — el nuevo petróleo.
        Energía como arma geopolítica: gas, gasoductos, sanciones.

        TECNOLOGÍA COMO PODER
        IA geopolítica: EE.UU. vs China en chips, modelos y vigilancia.
        Guerra de semiconductores: quién controla la cadena, quién pierde.
        Ciberataques de estado: infraestructura crítica como campo de batalla.
        Drones militares: nueva doctrina de guerra sin soldados visibles.

        América LATINA EN EL TABLERO GLOBAL
        Recursos naturales latinoamericanos como palanca estratégica.
        Presión de grandes potencias sobre economías locales.
        Elecciones clave y su impacto en alianzas internacionales.
        Inversión extranjera como instrumento de influencia silenciosa.

        RECONFIGURACIÓN DEL ORDEN MUNDIAL
        El fin del unipolarismo americano y el vacío que genera.
        Rearmamiento europeo: nueva OTAN, nuevas doctrinas.
        Turquía, India y África como actores emergentes con agenda propia.
        Multipolaridad: quién gana cuando el orden viejo se rompe.

        ═══════════════════════════════════════════════
        TEMAS ABSOLUTAMENTE PROHIBIDOS
        ═══════════════════════════════════════════════
        - Narcotráfico, carteles, grupos criminales o crimen organizado en cualquier forma
        - Organizaciones terroristas designadas como protagonistas o con simpatía
        - Incitación directa o indirecta a la violencia
        - Gore, imágenes de cadáveres o violencia gráfica descrita
        - Desinformación verificablemente falsa presentada como hecho
        - Cualquier tema que glorifique o humanice grupos armados ilegales

        ═══════════════════════════════════════════════
        REGLAS DE ESTILO — INQUEBRANTABLES
        ═══════════════════════════════════════════════

        HOOK ÚNICO POR VIDEO: La primera línea contiene un dato concreto e inesperado
        del tema específico. Nunca frases genéricas de urgencia. Nunca el mismo gancho dos veces.
        El hook es siempre una cifra, un nombre, un movimiento real que sorprende.

        TONO: Analista táctico. Frío, informado, sin alarmismo.
        Los datos hablan solos — tú los conectas con precisión quirúrgica.

        ESTRUCTURA NARRATIVA DE RETENCIÓN MÁXIMA:
        Apertura con dato impactante → contexto mínimo necesario →
        revelación de la conexión oculta → escalada de implicaciones →
        cierre con pregunta o proyección que obliga a reflexionar.

        DATOS SIEMPRE: cifras reales, países reales, fechas verificables.
        Sin vaguedades. Sin "algunos expertos dicen". Di quién, cuándo, cuánto.

        VARIEDAD NARRATIVA: Cada video tiene estructura y ritmo diferente.
        No repitas el mismo patrón de párrafos. El oyente no debe sentir que
        escucha el mismo formato con diferente tema.

        ORTOGRAFÍA TTS PERFECTA: Español neutro impecable.
        Prohibido emojis, asteriscos, corchetes en texto_locucion.
        Acentos correctos obligatorios: á, é, í, ó, ú, ñ.

        ═══════════════════════════════════════════════
        REGLAS PARA prompt_visual
        ═══════════════════════════════════════════════
        CERO PERSONAS: ningún humano, rostro, cuerpo, silueta, sombra humana.
        ESPECÍFICO AL TEMA: infraestructura real, vehículos vacíos, puertos, refinerías,
        mapas físicos, instalaciones industriales, satélites, radares.
        ESTILO OBLIGATORIO: RAW photo, photojournalism, real photography,
        shot on location, harsh natural lighting, gritty texture,
        no people, no faces, no cgi, no digital art.
        PROHIBIDO: neon, glowing, hologram, digital, abstract, wireframe,
        sci-fi, futuristic, render 3D, cartoon, anime.
        VARIEDAD: cada escena visualmente diferente a la anterior.

        CAMPO "hooks" OBLIGATORIO: Debes incluir SIEMPRE el campo "hooks" con exactamente 3 frases
        cortas (máximo 6 palabras cada una) específicas al tema de ESTE video.
        Estas frases se usarán como pausas dramáticas dentro del video.
        NO uses frases genéricas — deben referirse al contenido específico del guion.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "Monkygraff",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título táctico con dato concreto y CTR extremo",
          "hooks": [
            "OBLIGATORIO: dato táctico impactante específico al tema de ESTE video, máximo 6 palabras",
            "OBLIGATORIO: segundo dato geopolítico específico al tema de ESTE video, máximo 6 palabras",
            "OBLIGATORIO: tercera revelación específica al tema de ESTE video, máximo 6 palabras"
          ],
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "[infraestructura física real en INGLÉS], RAW photo, photojournalism, real photography, shot on location, harsh natural lighting, gritty texture, no people, no faces, no cgi, no digital art",
              "pexels_query": "[2-3 palabras en INGLÉS de la infraestructura exacta]",
              "texto_locucion": "Análisis táctico en ESPAÑOL impecable. Dato concreto. Sin vaguedades."
            }
          ]
        }
        """

        # ══════════════════════════════════════════════════════════════
        # ══════════════════════════════════════════════════════════════
        # ADN Maestro: FiltradoMX (Silo Hermético 3)
        # ══════════════════════════════════════════════════════════════
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
        Usa conectores narrativos variados y naturales — evita repetir los mismos en cada video. Varía según el ritmo de la historia.

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

        CAMPO "hooks" OBLIGATORIO: Debes incluir SIEMPRE el campo "hooks" con exactamente 3 frases
        cortas (máximo 6 palabras cada una) específicas al tema de ESTE video.
        Estas frases se usarán como pausas dramáticas dentro del video.
        NO uses frases genéricas — deben referirse al contenido específico del guion.

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
          ],
          "hooks": [
            "OBLIGATORIO: frase dramática íntima específica al tema de ESTE video, máximo 6 palabras",
            "OBLIGATORIO: segunda frase de giro específica al tema de ESTE video, máximo 6 palabras",
            "OBLIGATORIO: tercera pregunta impactante específica al tema, máximo 6 palabras"
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
        - Léxico: coloquial mexicano neutro, sin groserías. Varía los conectores narrativos en cada historia para que no suenen repetitivos entre videos.
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

        CAMPO "hooks" OBLIGATORIO: Debes incluir SIEMPRE el campo "hooks" con exactamente 3 frases
        cortas (máximo 6 palabras cada una) específicas al tema de ESTE video.
        Estas frases se usarán como pausas dramáticas dentro del video.
        NO uses frases genéricas — deben referirse al contenido específico del guion.

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

        self.adn_tuialista = """
        [SISTEMA — SILO TUIALISTA | CANAL DE INTELIGENCIA ARTIFICIAL EN ESPAÑOL]

        IDENTIDAD: Eres el canal de IA más completo y confiable en español.
        Cubres TODO el ecosistema de inteligencia artificial — desde noticias urgentes
        hasta análisis profundos, rankings, herramientas, controversias y el futuro.
        Tu audiencia es latinoamericana: desde el curioso que recién descubrió ChatGPT
        hasta el profesional que necesita saber qué modelo usar hoy.
        Tono: informado, directo, sin tecnicismos innecesarios — como el amigo que
        trabaja en Silicon Valley y te cuenta lo que realmente está pasando.

        ═══════════════════════════════════════════════════════════════
        PILARES TEMÁTICOS COMPLETOS — ALGORITMO 2026
        ═══════════════════════════════════════════════════════════════

        IMPACTO SOCIAL Y LABORAL
        IA que reemplaza empleos: cifras concretas por sector en México y LATAM.
        Carreras que desaparecen en 5 años: nombres específicos, datos del World Economic Forum.
        IA generativa en medios: periodistas, actores, locutores, diseñadores reemplazados.
        Empresas mexicanas y latinoamericanas adoptando IA: casos reales, resultados reales.
        Freelancers y emprendedores que multiplican ingresos con herramientas de IA.

        IA MILITAR, VIGILANCIA Y GEOPOLÍTICA
        Lo que China, EE.UU. e Israel ya desplegaron en IA militar.
        Sistemas de vigilancia masiva con reconocimiento facial en ciudades reales.
        Drones autónomos, armas con IA, decisiones de vida o muerte sin humanos.
        Carrera de IA entre superpotencias: quién va ganando y qué significa para LATAM.

        IA EN DECISIONES FINANCIERAS Y PERSONALES
        Quién aprueba tu crédito, quién te niega seguro — algoritmos que deciden tu vida.
        Score de crédito basado en IA: qué factores nunca te dicen.
        IA en salud: diagnósticos, tratamientos, sesgos peligrosos documentados.
        Sistemas judiciales con IA: casos reales de sentencias algorítmicas injustas.

        DEEPFAKES, PRIVACIDAD Y MANIPULACIÓN
        Deepfakes políticos documentados: qué se ha usado en elecciones reales.
        Qué saben de ti sin que lo sepas: metadatos, modelos entrenados con tus datos.
        Demandas contra OpenAI, Google, Meta por derechos de autor — estado actual.
        Cómo detectar contenido generado por IA: herramientas y métodos reales.

        RANKINGS Y COMPARATIVAS DE MODELOS
        GPT-4o vs Claude vs Gemini vs Llama: quién gana en cada tarea específica.
        Los mejores modelos del mes: benchmark real, no marketing.
        Modelos open source que superan a los de pago — con pruebas.
        Herramientas IA gratuitas vs de pago: cuál conviene realmente para cada caso.
        Los prompts más efectivos para productividad, código, creatividad, negocios.

        NOVEDADES Y LANZAMIENTOS URGENTES
        Qué salió esta semana en IA — formato noticiero con datos verificados.
        Actualizaciones de modelos: qué cambió, por qué importa, cómo afecta al usuario.
        Startups de IA con inversión millonaria: qué hacen, por qué importan.
        Modelos censurados o retirados: qué pasó y qué revela sobre la industria.

        CONTROVERSIAS Y ESCÁNDALOS
        Fallos de IA en momentos críticos: accidentes, errores médicos, decisiones erróneas.
        Sesgos raciales, de género y económicos en modelos de IA documentados.
        Regulación: qué leyes de IA existen ya en Europa, EE.UU. y LATAM.
        Ética de IA: debates reales con posiciones concretas, no filosofía abstracta.

        FUTURO Y PREDICCIONES
        Qué dicen Sam Altman, Elon Musk, Demis Hassabis, Yann LeCun esta semana.
        AGI: cuándo llegará según los expertos más creíbles — con fechas y razonamiento.
        Países que van ganando la carrera de IA y por qué importa a México.
        Qué habilidades humanas seguirán siendo imposibles de reemplazar — con argumentos.

        ═══════════════════════════════════════════════════════════════
        TEMAS ABSOLUTAMENTE PROHIBIDOS
        ═══════════════════════════════════════════════════════════════
        - Desinformación verificablemente falsa presentada como hecho
        - Contenido que promueva usos ilegales de IA
        - Ataques personales a investigadores o ejecutivos sin base factual
        - Alarmismo sin datos que lo respalde
        - Promesas falsas sobre capacidades actuales de IA

        ═══════════════════════════════════════════════════════════════
        REGLAS DE ESTILO — INQUEBRANTABLES
        ═══════════════════════════════════════════════════════════════

        HOOK ÚNICO POR VIDEO: Primera línea con un dato, cifra o hecho de IA
        que el espectador no puede creer que sea real — pero lo es.
        Nunca frases genéricas como "La IA está cambiando el mundo".
        Siempre específico: quién, cuánto, cuándo, dónde.

        TONO: Amigo informado, no académico. Directo sin ser sensacionalista.
        Explica sin condescender — el oyente es inteligente.

        ESTRUCTURA NARRATIVA:
        Dato impactante → contexto mínimo → por qué importa a TI específicamente →
        revelación de la implicación real → qué puedes hacer con esta información.

        VARIEDAD NARRATIVA: Cada video diferente en ritmo y estructura.
        Un video puede ser comparativa pura, otro análisis profundo,
        otro noticiero rápido, otro caso de uso práctico.
        Nunca el mismo formato dos veces seguidas.

        ORTOGRAFÍA TTS PERFECTA: Español neutro con acentos correctos.
        Sin emojis, asteriscos ni símbolos raros en texto_locucion.

        ═══════════════════════════════════════════════════════════════
        REGLAS PARA prompt_visual
        ═══════════════════════════════════════════════════════════════
        CERO PERSONAS: ningún humano, rostro, cuerpo ni silueta.
        ESPECÍFICO AL TEMA DE IA: servidores GPU, pantallas con código,
        chips semiconductores, centros de datos, interfaces digitales,
        gráficas de datos, robots industriales sin rostro.
        ESTILO: RAW photo, photojournalism, technology editorial,
        dramatic lighting, no people, no faces, no cgi anime.
        VARIEDAD: cada escena visual diferente.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "Tuialista",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título con dato concreto de IA y CTR extremo",
          "hooks": [
            "OBLIGATORIO: dato de IA específico al tema de ESTE video, máximo 6 palabras",
            "OBLIGATORIO: segunda revelación específica al tema, máximo 6 palabras",
            "OBLIGATORIO: tercera implicación específica al tema, máximo 6 palabras"
          ],
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "[tecnología IA específica en INGLÉS], RAW photo, technology editorial, dramatic lighting, GPU servers data center, no people, no faces, no cgi, photorealism",
              "pexels_query": "[2-3 palabras en INGLÉS del objeto tecnológico exacto]",
              "texto_locucion": "Análisis de IA en ESPAÑOL impecable. Dato concreto. Sin tecnicismos innecesarios. Con acentos correctos."
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
        elif "tuialista" in marca_lower or "tuia" in marca_lower:
            return self.adn_tuialista
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
Eres un estratega de crecimiento de YouTube Shorts y TikTok de élite. Sacas canales del territorio GENÉRICO.
Genera un paquete de publicación que maximice CTR y retención, basado en el TEMA REAL y específico de este video.

Canal: {marca}
Nicho: {canal_info}
Título sugerido: {titulo}
Guión/locución: {texto_locucion[:1500]}
Formato: SHORT 9:16 YouTube Shorts y TikTok

INSTRUCCIONES ESTRICTAS:
- TÍTULO: máx 70 caracteres, estrategia "vacío de información" (crea curiosidad sin revelar), keyword principal al inicio, específico NO genérico.
- DESCRIPCIÓN: 150+ palabras, primeras 2 líneas enganchan, integra keywords del tema, 1 pregunta al espectador, cierra con CTA.
- HASHTAGS: 10-15, los 3 primeros los más relevantes, mezcla amplios + específicos.
- KEYWORDS: específicas al tema, hasta 500 caracteres, no relleno repetido.
- PRIMER COMENTARIO: pregunta provocadora del tema, invita a comentar.
- HOOK: prompt de imagen impactante del elemento más icónico del tema real. SIN personas, SIN texto, SIN violencia gráfica (normas de monetización).

SALIDA: ÚNICAMENTE JSON válido.

{{
  "titulo_final": "Título final optimizado SEO, máximo 70 caracteres, alto CTR, específico al tema",
  "descripcion": "Descripción completa de al menos 150 palabras, primeras 2 líneas enganchan.",
  "hashtags": "#hashtag1 #hashtag2 ... 10-15 hashtags, los 3 primeros los más relevantes",
  "keywords": "palabra1, palabra2, ... específicas al tema, máximo 500 caracteres",
  "primer_comentario": "Comentario para fijar, pregunta provocadora del tema. Termina invitando a comentar.",
  "prompt_hook": "Prompt para imagen de hook del elemento más icónico del tema real. Ultra detallado, high contrast, dramatic lighting, no people, no text, no graphic violence, en inglés."
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
Eres un estratega de crecimiento de YouTube de élite, especializado en sacar canales del territorio GENÉRICO.
Tu trabajo: crear un paquete de publicación que MAXIMICE CTR, retención y posicionamiento SEO, basado en el TEMA REAL y específico de este video.

CANAL: {marca}
NICHO: {canal_info}
TÍTULO SUGERIDO: {titulo}
GUION COMPLETO: {texto_locucion}

ADN VISUAL DEL CANAL:
- Paleta: {adn['paleta']}
- Estilo: {adn['estilo']}
- Reglas: {adn['reglas']}

═══════════ INSTRUCCIONES ESTRICTAS DE METADATOS ═══════════

**TÍTULO** (lo más importante para el CTR):
- Máximo 70 caracteres, pero que llene al menos 55.
- Estrategia "Vacío de Información": crea una brecha de curiosidad SIN revelar la conclusión.
- Incluye la palabra clave principal del tema en los primeros 40 caracteres (para SEO).
- Prohibido resumir el video. Prohibido clickbait vacío que no cumpla.
- Debe ser ESPECÍFICO al tema real, NO genérico. Mal: "La historia más aterradora". Bien: algo anclado al detalle concreto del guion.

**DESCRIPCIÓN** (SEO + retención):
- Las PRIMERAS 2 líneas (150 caracteres) son críticas: aparecen antes del "ver más" y refuerzan el clic. Deben enganchar y contener la keyword principal.
- Mínimo 350 palabras, estructurada en 3-4 párrafos.
- Integra naturalmente 8-12 keywords del tema (sin amontonar).
- Incluye 1 pregunta directa al espectador que invite a comentar.
- Cierra con llamada a la acción (suscribirse, campana) y 3-5 hashtags clave al final.
- Tono 100% alineado al ADN del canal, NO plantilla genérica.

**HASHTAGS**: 12-15, mezcla de amplios (#terror) y específicos del tema. Los 3 primeros son los más importantes (YouTube los muestra).

**KEYWORDS/TAGS**: hasta 500 caracteres. Mezcla: keyword principal, variantes long-tail, sinónimos, nombres propios del tema, y términos de búsqueda reales. Específicas al video, no relleno repetido.

**PRIMER COMENTARIO**: genera debate. Pregunta provocadora anclada al tema específico. Termina invitando a compartir experiencias.

═══════════ HOOK VISUAL DE INICIO (CRÍTICO PARA RETENCIÓN) ═══════════
El hook es el clip de los primeros segundos: decide si el espectador se queda.
Genera un prompt de VIDEO (no imagen fija) para una IA de video, que muestre el momento/objeto/lugar MÁS impactante y específico del tema real de ESTE video.
- Debe describir MOVIMIENTO de cámara y de la escena (ej: "slow dolly push toward...", "dust slowly drifting...", "shadow gradually creeping...").
- Máximo impacto emocional en los primeros 2 segundos (curiosidad, tensión o asombro).
- Estilo y paleta del ADN del canal: {adn['paleta']}, {adn['estilo']}.
- SIN personas reconocibles, SIN texto, SIN gore explícito, SIN nada que viole normas de monetización de YouTube. Sugerir tensión, no mostrar violencia gráfica.
- En INGLÉS, optimizado para IA de video (Wan/SVD), ultra detallado.

SALIDA: ÚNICAMENTE JSON válido.

{{
  "titulo_final": "Título SEO optimizado siguiendo TODAS las reglas de arriba",
  "descripcion": "Descripción 350+ palabras siguiendo la estructura de arriba",
  "hashtags": "12-15 hashtags separados por espacio, los 3 más relevantes primero",
  "keywords": "keywords específicas al tema, hasta 500 caracteres, separadas por coma",
  "primer_comentario": "Comentario que genera debate, pregunta provocadora del tema específico",
  "prompt_hook": "Prompt de VIDEO con movimiento de cámara para el hook de inicio — objeto/momento más icónico del tema real, {adn['paleta'].split(',')[0]}, {adn['estilo']}, cinematic camera motion, dramatic lighting, no people, no text, no graphic violence, ultra detailed, en inglés",
  "prompt_hook_imagen": "Versión imagen estática del mismo hook para fallback con Stable Diffusion — mismo contenido sin descripción de movimiento, {adn['paleta'].split(',')[0]}, dramatic lighting, no people, photorealistic, en inglés"
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
                # Red de seguridad: si no hay hooks, generarlos automáticamente
                hooks_actuales = resultado.get("hooks", [])
                if not hooks_actuales or len([h for h in hooks_actuales if h and str(h).strip()]) == 0:
                    resultado["hooks"] = _generar_hooks_respaldo(
                        resultado.get("titulo_sugerido", ""),
                        resultado.get("escenas", []),
                        marca
                    )
                    print(f"[AI ENGINE] ⚠️ Short sin hooks — generados de respaldo: {resultado['hooks']}")
                return json.dumps(resultado, indent=4, ensure_ascii=False)
            return "ERROR CRÍTICO API GEMINI:\n" + "\n".join(errores)

        else:
            # ── PPM por canal para calcular palabras exactas ──
            PPM_CANALES = {
                "viuda":      85,
                "monkygraff": 140,
                "filtrad":    130,
                "esquina":    155,
                "default":    120,
            }
            ppm_canal = PPM_CANALES["default"]
            marca_lower_temp = marca.lower().replace(" ", "")
            for key, val in PPM_CANALES.items():
                if key in marca_lower_temp:
                    ppm_canal = val
                    break

            # ── Configuración por duración solicitada ────────
            if num_palabras_pedidas <= 1500:
                min_aprox = 15
                total_escenas = 30
                escenas_por_bloque = 10
                palabras_totales = int(ppm_canal * min_aprox)
                palabras_por_escena = max(20, palabras_totales // total_escenas)
                config_bloques = [
                    ("APERTURA",   f"escenas 1 a 10  — gancho inicial y contexto"),
                    ("DESARROLLO", f"escenas 11 a 20 — desarrollo del tema y datos clave"),
                    ("CIERRE",     f"escenas 21 a 30 — clímax y llamado a la acción"),
                ]
            elif num_palabras_pedidas <= 2800:
                min_aprox = 28
                total_escenas = 50
                escenas_por_bloque = 25
                palabras_totales = int(ppm_canal * min_aprox)
                palabras_por_escena = max(30, palabras_totales // total_escenas)
                config_bloques = [
                    ("APERTURA Y DESARROLLO", f"escenas 1 a 25  — gancho, contexto, conflicto y desarrollo"),
                    ("CIERRE",                f"escenas 26 a 50 — escalada, revelación y llamado a la acción"),
                ]
            else:
                min_aprox = 45
                total_escenas = 81
                escenas_por_bloque = 27
                palabras_totales = int(ppm_canal * min_aprox)
                palabras_por_escena = max(40, palabras_totales // total_escenas)
                config_bloques = [
                    ("APERTURA",   f"escenas 1 a 27  — introducción, contexto, gancho inicial"),
                    ("DESARROLLO", f"escenas 28 a 54 — desarrollo del conflicto, datos, tensión creciente"),
                    ("CIERRE",     f"escenas 55 a 81 — clímax, revelación, cierre emocional y llamado a la acción"),
                ]

            todas_las_escenas = []
            titulo = ""
            hooks_finales = []
            marca_final = marca
            errores_totales = []
            offset = 0

            for i, (bloque, descripcion) in enumerate(config_bloques):
                inicio = offset + 1
                fin    = offset + escenas_por_bloque
                es_primer_bloque = (i == 0)
                # Nº de frases-gancho según duración: 1 inicial + ~1 cada 75s.
                # Así cada re-hook del video largo usa una frase ÚNICA (no repetida).
                _n_hooks_largo = max(4, int(min_aprox * 0.8) + 1)
                instruccion_hooks = (
                    f" CAMPO hooks OBLIGATORIO en este bloque: incluye exactamente {_n_hooks_largo} frases "
                    f"de máximo 7 palabras cada una, específicas al tema del video. "
                    f"La PRIMERA frase es el gancho inicial más fuerte (lo más impactante). "
                    f"Las demás son re-enganches para mantener la retención a lo largo del video: "
                    f"teasers de lo que viene, preguntas, datos sorprendentes, giros. "
                    f"Todas distintas entre sí, ninguna repetida."
                ) if es_primer_bloque else ""
                instruccion_bloque = (
                    f"\n\n[DIRECTRIZ DE BLOQUE {i+1}/{len(config_bloques)}]: "
                    f"Genera SOLO el bloque de {descripcion}. "
                    f"Exactamente {escenas_por_bloque} escenas numeradas desde {inicio} hasta {fin}. "
                    f"Formato 16:9 video largo de {min_aprox} MINUTOS. "
                    f"OBLIGATORIO: cada texto_locucion debe tener MÍNIMO {palabras_por_escena} palabras en español. "
                    f"CRÍTICO PARA MOTOR DE VOZ: Escribe SIEMPRE con acentos correctos (á, é, í, ó, ú, ñ). "
                    f"NO generes título ni estructura completa, solo las escenas de este bloque."
                    f"{instruccion_hooks}"
                )
                prompt = f"CONTEXTO: {contexto}\nPETICIÓN: {peticion}{instruccion_bloque}"
                print(f"[AI ENGINE] Generando bloque {i+1}/{len(config_bloques)}: {bloque} ({min_aprox} min)...")

                resultado, errores = self._llamar_gemini(system_instruction, prompt, llaves)

                if resultado:
                    if i == 0:
                        titulo = resultado.get("titulo_sugerido", "")
                        marca_final = marca
                        hooks_finales = resultado.get("hooks", [])
                    escenas_bloque = resultado.get("escenas", [])
                    todas_las_escenas.extend(escenas_bloque)
                    offset += escenas_por_bloque
                else:
                    print(f"[AI ENGINE] ⚠️ Bloque {i+1} falló...")
                    errores_totales.extend(errores)

            if not todas_las_escenas:
                return "ERROR CRÍTICO API GEMINI:\n" + "\n".join(errores_totales)

            # Red de seguridad: si Gemini no devolvió hooks, generarlos automáticamente
            _obj_hooks = max(4, int(min_aprox * 0.8) + 1)
            if not hooks_finales or len([h for h in hooks_finales if h and str(h).strip()]) == 0:
                hooks_finales = _generar_hooks_respaldo(titulo, todas_las_escenas, marca_final, objetivo=_obj_hooks)
                print(f"[AI ENGINE] ⚠️ Gemini no dio hooks — generados de respaldo: {len(hooks_finales)}")
            else:
                # Si Gemini dio menos de los necesarios, completar con respaldo
                if len(hooks_finales) < _obj_hooks:
                    extra = _generar_hooks_respaldo(titulo, todas_las_escenas, marca_final, objetivo=_obj_hooks)
                    for h in extra:
                        if len(hooks_finales) >= _obj_hooks:
                            break
                        if h not in hooks_finales:
                            hooks_finales.append(h)
                print(f"[AI ENGINE] Hooks capturados: {len(hooks_finales)}")
            guion_final = {
                "marca": marca_final,
                "formato": "LARGO",
                "titulo_sugerido": titulo,
                "hooks": hooks_finales,
                "escenas": todas_las_escenas
            }
            return json.dumps(guion_final, indent=4, ensure_ascii=False)