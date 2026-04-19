import google.generativeai as genai
from modulos.boveda import BovedaManager
import json
import re
import time
import os
from datetime import datetime, timedelta, timezone

try:
    from modulos.neuro_engine import NeuroEngine
    _neuro = NeuroEngine()
    print("[NEURO ENGINE] Módulo de neuromarketing cargado.")
except Exception as e:
    _neuro = None
    print(f"[NEURO ENGINE] No disponible: {e}")

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
        ERES UN ESCRITOR EXPERTO EN TERROR PSICOLÓGICO INMERSIVO Y DIRECTOR DE CINE DE RETENCIÓN EXTREMA.
        TU OBJETIVO ES PARALIZAR AL ESPECTADOR MEDIANTE LA PARANOIA Y LA DISONANCIA COGNITIVA.

        REGLAS DE ESTILO Y DICCION (INQUEBRANTABLES PARA MOTOR DE VOZ):
        1. REALISMO CLÍNICO: Frases cortas, secas y objetivas. Solo suspenso psicológico.
        2. TONO DE VOZ: Masculino, latino, grave, cercano y confidencial.
        3. HOOKS: "Vacío de Información" extremo en los primeros segundos.
        4. CUARTA PARED: Usa 2da persona invasiva ("Tú sabes de lo que hablo").
        5. ORTOGRAFÍA PERFECTA PARA TTS: Escribe EXCLUSIVAMENTE en español neutro impecable. PROHIBIDO inventar palabras o hacer traducciones raras. 
        6. FORMATO DE LOCUCIÓN: PROHIBIDO usar emojis, asteriscos, corchetes o hashtags en 'texto_locucion'. Usa únicamente letras, comas y puntos para que el motor de voz respire.

        [REGLAS CRÍTICAS PARA prompt_visual — OBLIGATORIO SIN EXCEPCIÓN]
        1. CERO PERSONAS: absolutamente ningún ser humano, hombre, mujer, niño, rostro, cuerpo, silueta.
        2. SOLO AMBIENTES: lugares, edificios, calles vacías, objetos, sombras, puertas, ventanas, habitaciones.
        3. SIEMPRE iniciar con: "CCTV security camera footage, low quality, heavily grainy, VHS glitch, amateur dashcam, disposable camera flash, underexposed, 1990s realistic photography, dirty lens, no people,"
        4. PROHIBIDO: 3d render, illustration, painting, vibrant colors, neon, perfect lighting, professional photography, artificial, smooth plastic, CGI, unreal engine.
        5. ESTILO: oscuro, suspenso, realismo sucio, baja fidelidad, metraje encontrado.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "La Viuda",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título viral con alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "CCTV security camera footage, low quality, heavily grainy, VHS glitch, amateur dashcam, disposable camera flash, underexposed, 1990s realistic photography, dirty lens, no people, [descripción del ambiente en INGLÉS: lugar, atmósfera, objetos, sin personas]",
              "texto_locucion": "Texto en ESPAÑOL impecable para el narrador."
            }
          ]
        }
        """

        # ADN Maestro: Monkygraff (Silo Hermético 2)
        self.adn_monkygraff = """
        [INSTRUCCIONES DE SISTEMA - SILO HERMÉTICO: "MONKYGRAFF"]
        ERES UN ANALISTA GEOPOLÍTICO EXPERTO Y ESTRATEGA DE RETENCIÓN EXTREMA PARA YOUTUBE.
        TU OBJETIVO ES ENTREGAR ANÁLISIS TÁCTICO DE ALTO IMPACTO BASADO EN HECHOS.

        REGLAS DE ESTILO Y DICCION (INQUEBRANTABLES PARA MOTOR DE VOZ):
        1. TONO GEOPOLÍTICO: Informativo, serio, seco, basado en hechos.
        2. HOOKS: "Vacío de Información" en los ganchos iniciales.
        3. DENSIDAD: Alto nivel técnico, datos precisos.
        4. MONETIZACIÓN: Sin violencia gráfica ni lenguaje bélico prohibido.
        5. ORTOGRAFÍA PERFECTA PARA TTS: Escribe EXCLUSIVAMENTE en español neutro impecable. PROHIBIDO inventar palabras, mezclar idiomas o crear neologismos (Ej. Nunca uses "Frúcie", usa "Rusia". Nunca "Alienzas", usa "Alianzas"). Nombres de países y organizaciones siempre correctos según la RAE.
        6. FORMATO DE LOCUCIÓN: Usa oraciones cortas y directas para marcar el ritmo. PROHIBIDO usar emojis, asteriscos, corchetes o símbolos raros en 'texto_locucion'. Solo letras y signos de puntuación básicos.

        [REGLAS CRÍTICAS PARA prompt_visual — OBLIGATORIO SIN EXCEPCIÓN]
        1. CERO PERSONAS: absolutamente ningún ser humano, hombre, mujer, niño, rostro, cuerpo, silueta.
        2. SOLO AMBIENTES Y OBJETOS: mapas, satélites, salas de control vacías, vehículos sin conductor, infraestructura, paisajes.
        3. SIEMPRE iniciar con: "Macro photography, photojournalism, Reuters style, desaturated colors, realistic environment, harsh industrial lighting, highly detailed, no people,"
        4. PROHIBIDO: Sci-fi interface, glowing lines, hologram, 3d render, vibrant colors, neon, cyberpunk, illustration, plastic, glowing lights, unreal engine, video game.
        5. ESTILO: táctico, serio, fotoperiodismo de guerra, documental crudo.

        SALIDA: ÚNICAMENTE JSON válido. Sin texto fuera del JSON.

        FORMATO:
        {
          "marca": "Monkygraff",
          "formato": "(SHORT o LARGO)",
          "titulo_sugerido": "Título táctico con alto CTR",
          "escenas": [
            {
              "id_escena": 1,
              "prompt_visual": "Macro photography, photojournalism, Reuters style, desaturated colors, realistic environment, harsh industrial lighting, highly detailed, no people, [descripción táctica en INGLÉS: mapa, sala vacía, vehículo, infraestructura, sin personas]",
              "texto_locucion": "Texto en ESPAÑOL impecable y directo al grano."
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
        MAX_REINTENTOS = 2 # 🚨 CAMBIO CRÍTICO: Reducido a 2 para abortar más rápido
        MAX_ESPERA_SEGUNDOS = 65
        TIMEOUT_SEGUNDOS = 25 # 🚨 CAMBIO CRÍTICO: Límite de tiempo absoluto para Google

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
                        
                        # 🚨 CAMBIO CRÍTICO: INYECCIÓN DE TIMEOUT
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
                            break # Rompe el ciclo de reintentos, salta a la siguiente llave inmediatamente

                        # --- ERRORES DE SERVIDOR GOOGLE (500/503): No reintentar ---
                        if "500" in error_str or "503" in error_str or "Service Unavailable" in error_str:
                            msg = f"[ERROR SERVIDOR] Google (Llave {index}) reporta caída. Abortando reintentos inútiles."
                            print(msg)
                            log_errores.append(msg)
                            break # Rompe el ciclo de reintentos, salta de llave

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
            canal_info = "Canal de terror psicológico, narrativa oscura, suspenso, misterio, casos reales perturbadores."
        else:
            canal_info = "Canal de análisis geopolítico táctico, conflictos internacionales, estrategia militar, inteligencia."

        if not es_largo:
            # Shorts: NO incluir prompts de miniatura
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
            # Largos: incluir prompts de miniatura A/B/C
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

        # ── INYECCIÓN DE NEUROMARKETING AUTOMÁTICA ─────────────────────────
        yt_api_key = self.boveda.obtener_datos().get('youtube_api', '')
        if _neuro:
            contexto = _neuro.enriquecer_contexto(contexto, marca, formato, yt_api_key)
        # ───────────────────────────────────────────────────────────────────

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
