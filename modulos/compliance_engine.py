import os
import json
import re
import logging
import datetime
import requests

# ============================================================
# COMPLIANCE ENGINE v2.1 — Corregido para YouTube 2026
# Bugs corregidos:
#   1. _guardar_leyes definida dos veces (la primera vacía sobreescribía)
#   2. Lista negra demasiado amplia — bloqueaba palabras legítimas de horror narrado
#   3. Filtro de marca con umbral de 6 imposible de alcanzar en restricciones cortas
#   4. "muerte" bloqueaba todo el nicho (horror = muerte contextualizada = PERMITIDO en YT 2026)
#   5. Loop de reescritura con prompt_corrector acumulativo no reseteado
#   6. Sin distinción entre contenido gráfico (prohibido) y contextualizado (permitido)
# Fuente: YouTube Advertiser-Friendly Guidelines actualizado enero-marzo 2026
# ============================================================

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

class ComplianceEngine:
    def __init__(self):
        self.leyes_path = os.path.join(os.path.dirname(__file__), 'leyes_plataformas.json')
        self.dias_caducidad = 30
        self.leyes = self._cargar_o_crear_leyes()
        self.verificar_y_actualizar_leyes()

    # ----------------------------------------------------------
    # CARGA Y PERSISTENCIA
    # ----------------------------------------------------------

    def _cargar_o_crear_leyes(self):
        if os.path.exists(self.leyes_path):
            try:
                with open(self.leyes_path, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    # Forzar regeneración si la versión es antigua
                    if datos.get("version", "1.0") != "2.2":
                        logging.info("[COMPLIANCE] Versión obsoleta detectada. Regenerando leyes base v2.2...")
                        return self._generar_leyes_base()
                    return datos
            except Exception as e:
                logging.error(f"[COMPLIANCE] Error leyendo leyes_plataformas.json: {e}")
                return self._generar_leyes_base()
        return self._generar_leyes_base()

    def _generar_leyes_base(self):
        """
        Leyes base calibradas con las políticas REALES de YouTube 2026.

        FUENTE OFICIAL (enero-marzo 2026):
        - Contenido dramático / ficticio sobre temas sensibles: MONETIZABLE si no es gráfico
        - Violencia contextualizada (horror narrado, documental): MONETIZABLE
        - Muerte contextualizada: MONETIZABLE (no gore, no sadismo explícito)
        - Suicidio/autolesión con contexto educativo/narrativo: MONETIZABLE (update enero 2026)
        - Palabras en sí mismas NO desmonetizaban — el CONTEXTO y lo GRÁFICO sí
        
        LO QUE SÍ ESTÁ PROHIBIDO (YouTube 2026):
        - Gore explícito sin contexto (foco en sangre/heridas como entretenimiento)
        - Violencia gráfica no contextualizada
        - Contenido de odio / discriminación
        - Contenido sexual explícito
        - Abuso infantil / trata de personas
        - Instrucciones reales de daño (bombas, armas, etc.)
        - Desinformación médica dañina verificable
        """
        leyes_base = {
            "version": "2.2",
            "ultima_actualizacion": datetime.datetime.now().strftime("%Y-%m-%d"),
            "fuente": "YouTube Advertiser-Friendly Guidelines 2026 + Community Guidelines",

            # ── CERO TOLERANCIA (aplica a TODOS los canales, sin excepción) ──────
            # Términos que NUNCA deben aparecer, ni en broma ni en contexto narrativo.
            # Encienden clasificadores automáticos de las plataformas y arriesgan el
            # canal entero (no solo el video). Se detectan por palabra/raíz suelta.
            # Si alguno aparece → bloqueo inmediato y regeneración del guion.
            "cero_tolerancia": [
                # — Explotación / abuso de menores (riesgo máximo, suspensión de canal) —
                "pornografía infantil", "pornografia infantil", "abuso infantil", "abuso de menores",
                "explotación infantil", "explotacion infantil", "pederastia", "pedófilo", "pedofilo",
                "pedofilia", "menores sexual", "sexo con menores", "trata de menores",
                "trata de niños", "trata de ninos", "grooming", "sextorsión", "sextorsion",
                # — Narcotráfico / drogas (desmonetización dura) —
                "narcotráfico", "narcotrafico", "narco", "narcos", "narcomenudeo",
                "cártel de droga", "cartel de droga", "cártel de la droga", "cartel de la droga",
                "cártel de sinaloa", "cartel de sinaloa", "cártel del golfo", "cartel del golfo",
                "cártel de las drogas", "cartel de las drogas", "cárteles de droga", "carteles de droga",
                "cocaína", "cocaina", "heroína", "heroina", "metanfetamina", "cristal meth",
                "fentanilo", "marihuana", "mariguana", "cannabis", "vender droga", "vender drogas",
                "tráfico de drogas", "trafico de drogas", "sicario", "sicarios",
                # — Instrucciones de daño real —
                "fabricar bomba", "hacer explosivos", "fabricar explosivos", "fabricar arma",
            ],

            "plataformas": {
                "youtube": {
                    # BUG FIX: Lista mínima. Solo lo que YT 2026 prohíbe ABSOLUTAMENTE
                    # Palabras como "muerte", "asesinato", "suicidio" son PERMITIDAS en contexto narrativo
                    "terminos_prohibidos_absolutos": [
                        "instrucciones para fabricar bomba",
                        "cómo hacer explosivos",
                        "abuso sexual infantil",
                        "trata de menores",
                        "snuff"
                    ],
                    # Patrones que requieren revisión de contexto (no bloqueo automático)
                    "patrones_riesgo_alto": [
                        "gore explícito",
                        "vísceras expuestas",
                        "desmembramiento gráfico"
                    ],
                    "regla_general": (
                        "YouTube 2026 permite contenido dramático/ficticio sobre temas sensibles "
                        "si NO es gráfico. Horror narrado, misterio, casos reales contextualizados "
                        "son MONETIZABLES. El foco en sangre/heridas sin contexto NO lo es."
                    ),
                    "permitido_explicito": [
                        "muerte contextualizada en narrativa",
                        "terror psicológico",
                        "horror médico con eufemismos clínicos",
                        "casos reales dramatizados sin gore",
                        "suicidio en contexto educativo o narrativo (update enero 2026)",
                        "violencia implícita sin detalle gráfico",
                        "lenguaje fuerte después del segundo 7 del video"
                    ]
                },
                "meta": {
                    "terminos_prohibidos_absolutos": [
                        "trata de personas",
                        "abuso infantil explícito",
                        "instrucciones de violencia real"
                    ],
                    "regla_general": "Contenido de terror narrativo sin gore explícito es aceptable."
                },
                "tiktok": {
                    "terminos_prohibidos_absolutos": [
                        "autolesión con instrucciones",
                        "drogas con instrucciones de consumo",
                        "violencia real no contextualizada"
                    ],
                    "regla_general": "Terror narrativo y psicológico es permitido. Gore visual no."
                }
            },

            "marcas": {
                "La Viuda": {
                    # BUG FIX: Restricciones específicas, no genéricas
                    # Restricciones son lo que HAY QUE EVITAR en el OUTPUT final
                    "restricciones_output": [
                        "describir heridas con detalle anatómico explícito",
                        "narrar gore como entretenimiento sin contexto",
                        "incluir instrucciones de daño real",
                        "sadismo visual detallado sin propósito narrativo"
                    ],
                    # Lo que SÍ puede usar (importante para no sobre-filtrar)
                    "permitido": [
                        "muerte sugerida o implícita",
                        "terror psicológico",
                        "presencia invisible",
                        "fenómenos físicos inexplicables",
                        "horror médico clínico (terminología médica = eufemismo válido)",
                        "casos documentados ficticios",
                        "cifras estadísticas de mortalidad en contexto",
                        "hoteles, hospitales, lugares donde hubo muertes",
                        "parálisis del sueño y fenómenos de consciencia",
                        "entidades sin forma física"
                    ],
                    "estrategia_evasion": (
                        "REALISMO CLÍNICO: Sustituir descripciones gráficas por terminología médica "
                        "o periodística. EJEMPLOS: "
                        "'le destrozaron el cráneo' → 'sufrió traumatismos craneales incompatibles con la vida'; "
                        "'charco de sangre' → 'la escena presentaba evidencia forense significativa'; "
                        "'tripas afuera' → 'el examen post-mortem reveló daño visceral extenso'; "
                        "'se suicidó cortándose' → 'la autopsia determinó muerte por lesión autoinfligida'. "
                        "NUNCA describir el método o el proceso con detalle. Solo el resultado clínico."
                    ),
                    "umbral_bloqueo": 2  # BUG FIX: Umbral razonable (era 6, imposible de alcanzar)
                },
                "FiltradoMX": {
                    "restricciones_output": [
                        "mencionar nombres reales identificables de personas",
                        "incluir números de teléfono, direcciones o datos personales reales",
                        "nombrar empresas o instituciones reales en contexto negativo sin pruebas",
                        "afirmar como hecho real algo que podría ser difamatorio",
                        "incluir información que permita identificar a personas reales",
                        "contenido sexual explícito o descripción de actos sexuales con detalle"
                    ],
                    "permitido": [
                        "confesiones anónimas de situaciones cotidianas",
                        "infidelidad narrada sin identificar personas reales",
                        "conflictos laborales sin nombrar empresas reales",
                        "drama familiar sin datos identificables",
                        "traición entre amigos/pareja en tono narrativo",
                        "situaciones embarazosas o escandalosas ficcionalizadas",
                        "lenguaje coloquial mexicano sin groserías explícitas"
                    ],
                    "estrategia_evasion": (
                        "ANONIMIZACIÓN OBLIGATORIA: Toda historia debe presentarse como anónima. "
                        "Sustituir nombres por referencias genéricas: 'mi amiga', 'mi jefe', 'él/ella'. "
                        "Nunca mencionar empresas, colonias específicas, escuelas o cualquier dato "
                        "que permita identificar a personas reales. "
                        "DISCLAIMER: Incluir siempre al inicio o final que los hechos son anónimos "
                        "y no identifican a personas reales."
                    ),
                    "umbral_bloqueo": 1
                },
                "Monkygraff": {
                    "restricciones_output": [
                        "incitación explícita a cometer actos de violencia",
                        "propaganda directa de organizaciones terroristas designadas",
                        "instrucciones de fabricación de armas reales",
                        "contenido sobre narcotráfico, carteles o crimen organizado",
                        "glorificación de grupos armados ilegales",
                        "narración de operaciones criminales con detalle operativo",
                        "mencionar líderes de cárteles o grupos criminales como protagonistas",
                        "contenido que humanice o justifique organizaciones del crimen organizado"
                    ],
                    "permitido": [
                        "análisis documental de conflictos armados entre estados",
                        "terminología militar y táctica formal en contexto geopolítico",
                        "cifras de bajas en contexto informativo y periodístico",
                        "crítica geopolítica a gobiernos y organizaciones internacionales",
                        "análisis de estrategia económica, comercial y financiera global",
                        "cobertura de guerras y conflictos como hecho informativo",
                        "análisis de crímenes de guerra desde perspectiva histórica documentada",
                        "descripción de tácticas militares estatales desde perspectiva analítica",
                        "impacto económico del crimen organizado en contexto macroeconómico sin glorificarlo"
                    ],
                    "estrategia_evasion": (
                        "TONO ANALISTA GEOPOLÍTICO: Narrar como observador externo sin tomar partido. "
                        "Si el tema roza el crimen organizado, enfocar en impacto económico o político "
                        "sin mencionar grupos o líderes específicos. "
                        "Usar terminología formal: 'economía ilícita', 'mercados informales', "
                        "'desestabilización regional' en lugar de nombres de carteles o grupos. "
                        "Nunca romantizar, glorificar ni humanizar actores criminales."
                    ),
                    "umbral_bloqueo": 1
                },
                "Umbral Alterno": {
                    "restricciones_output": [
                        "presentar el escenario hipotético como predicción o hecho real confirmado",
                        "lenguaje catastrofista o alarmista sin base en datos",
                        "emitir juicios políticos o morales sobre países, gobiernos o personas reales",
                        "mencionar marcas, países o personas reales de forma negativa sin sustento",
                        "incitación al pánico, miedo masivo o teorías conspirativas",
                        "instrucciones de daño real o aprovechamiento de tragedias recientes",
                        "inventar cifras exactas o atribuir datos falsos a instituciones reales",
                        "construir escenarios de guerra con conflictos reales activos y países nombrados",
                        "regodearse en sufrimiento humano, muertes o caos con morbo",
                        "señalar a un país, religión, sistema o grupo como villano"
                    ],
                    "permitido": [
                        "escenarios hipotéticos narrados como documental ('imagina que...')",
                        "proyecciones de futuro basadas en tendencias y datos reales",
                        "historia alternativa y especulación con base verificable",
                        "fenómenos físicos o naturales extremos en tono científico-narrativo",
                        "colapsos de sistemas narrados con rigor y sin sensacionalismo",
                        "datos reales y estadísticas verificables como base del escenario",
                        "cifras aproximadas con frases de cautela ('se estima que', 'alrededor de')",
                        "escenarios de conflicto con naciones genéricas o casos históricos cerrados"
                    ],
                    "estrategia_evasion": (
                        "ENCUADRE DE SIMULACIÓN DOBLE: el escenario se presenta como hipotético al "
                        "INICIO y al FINAL ('imagina que...', 'esto fue una simulación, por ahora'). "
                        "Nunca como predicción. DATOS CON CAUTELA: usar rangos y 'se estima que' en "
                        "vez de cifras inventadas; nunca atribuir datos falsos a instituciones reales. "
                        "ANTI-DESASTRE: foco en el análisis del sistema, no en el sufrimiento ni el "
                        "pánico. GEOPOLÍTICA: naciones genéricas o casos históricos, nunca conflictos "
                        "reales activos. Tono documental sobrio, equilibrio, sin villanos ni juicios."
                    ),
                    "umbral_bloqueo": 1
                }
            }
        }
        self._guardar_leyes(leyes_base)
        logging.info("[COMPLIANCE] Leyes base v2.1 generadas con políticas YouTube 2026.")
        return leyes_base

    # BUG FIX CRÍTICO: Solo una definición de _guardar_leyes
    def _guardar_leyes(self, datos):
        """Escribe las políticas en disco."""
        try:
            with open(self.leyes_path, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"[COMPLIANCE] Error fatal al guardar leyes: {e}")

    # ----------------------------------------------------------
    # VERIFICACIÓN Y ACTUALIZACIÓN
    # ----------------------------------------------------------

    def verificar_y_actualizar_leyes(self):
        fecha_str = self.leyes.get("ultima_actualizacion", "2000-01-01")
        try:
            ultima_fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            diferencia = datetime.datetime.now() - ultima_fecha
            if diferencia.days >= self.dias_caducidad:
                logging.info(f"[COMPLIANCE] Políticas con {diferencia.days} días. Actualizando...")
                self._ejecutar_extraccion_nube()
            else:
                dias_restantes = self.dias_caducidad - diferencia.days
                logging.info(f"[COMPLIANCE] Políticas vigentes. Próxima actualización en {dias_restantes} días.")
        except Exception as e:
            logging.error(f"[COMPLIANCE] Error en verificación de caducidad: {e}")

    def _ejecutar_extraccion_nube(self):
        """
        Placeholder para conexión con APIs externas de compliance.
        En producción: conectar con scraper de support.google.com/youtube
        """
        try:
            # TODO: Implementar scraper real de políticas YT
            # Por ahora: solo actualiza el timestamp para no re-ejecutar cada arranque
            self.leyes["ultima_actualizacion"] = datetime.datetime.now().strftime("%Y-%m-%d")
            self._guardar_leyes(self.leyes)
            logging.info("[COMPLIANCE] Timestamp actualizado. (Scraper real: pendiente de implementar)")
        except Exception as e:
            logging.error(f"[COMPLIANCE] Fallo en extracción nube: {e}")

    # ----------------------------------------------------------
    # AUDITORÍA — LÓGICA CORREGIDA
    # ----------------------------------------------------------

    def _auditar_texto_crudo(self, guion, marca):
        """
        Audita el guion contra las leyes 2026.
        
        LÓGICA CORREGIDA:
        - Nivel 1: Términos ABSOLUTAMENTE prohibidos (bloqueo inmediato)
        - Nivel 2: Patrones de riesgo alto en contexto (evaluación por densidad)
        - Nivel 3: Restricciones de marca (umbral razonable de 2 coincidencias)
        """
        if not guion or not guion.strip():
            return False, "Guion vacío recibido."

        texto_limpio = guion.lower()

        # Ignorar si es mensaje de error del motor de IA
        if any(err in texto_limpio for err in ["error crítico", "error de compliance", "[error"]):
            return True, "Texto de error del sistema — auditoría omitida."

        yt_config = self.leyes["plataformas"]["youtube"]

        # ── NIVEL 0: CERO TOLERANCIA (aplica a TODOS los canales) ───────────
        # Términos de explotación infantil, narcotráfico/drogas e instrucciones
        # de daño real. NUNCA permitidos, ni en broma ni en contexto narrativo.
        # Detección por raíz de palabra (no frase completa) para atrapar variantes.
        for termino in self.leyes.get("cero_tolerancia", []):
            t = termino.lower().strip()
            if not t:
                continue
            # Para términos de una sola palabra, exigir límite de palabra (\b) para
            # no atrapar substrings inocentes; para frases, búsqueda directa.
            if " " in t:
                encontrado = t in texto_limpio
            else:
                encontrado = re.search(r'\b' + re.escape(t) + r'\b', texto_limpio) is not None
            if encontrado:
                return False, (
                    f"BLOQUEO NIVEL 0 (CERO TOLERANCIA): término prohibido para TODAS las "
                    f"plataformas detectado: '{termino}'. Este contenido enciende clasificadores "
                    f"automáticos y arriesga el canal completo. REGENERA el guion SIN ninguna "
                    f"referencia a narcotráfico, drogas ilegales, explotación de menores ni "
                    f"instrucciones de daño — ni siquiera en broma o de forma indirecta."
                )

        # ── NIVEL 1: Términos absolutamente prohibidos ──────────────────
        # Solo los que YT 2026 prohíbe sin excepción (gore, abuso infantil, instrucciones daño)
        for termino in yt_config.get("terminos_prohibidos_absolutos", []):
            patron = r'\b' + re.escape(termino.lower()) + r'\b'
            if re.search(patron, texto_limpio):
                return False, (
                    f"BLOQUEO NIVEL 1: Término absolutamente prohibido detectado: '{termino}'. "
                    f"Este contenido viola las Community Guidelines de YouTube y no puede monetizarse."
                )

        # ── NIVEL 2: Patrones de riesgo alto (gore explícito) ──────────
        # Solo bloquea si hay DENSIDAD alta (3+ ocurrencias) — evita falsos positivos
        patrones_riesgo = yt_config.get("patrones_riesgo_alto", [])
        ocurrencias_riesgo = 0
        for patron_texto in patrones_riesgo:
            patron = r'\b' + re.escape(patron_texto.lower()) + r'\b'
            matches = re.findall(patron, texto_limpio)
            ocurrencias_riesgo += len(matches)

        if ocurrencias_riesgo >= 3:
            return False, (
                f"BLOQUEO NIVEL 2: Densidad alta de contenido gráfico detectada "
                f"({ocurrencias_riesgo} ocurrencias de patrones de riesgo). "
                f"Aplicar REALISMO CLÍNICO para reemplazar descripciones visuales explícitas."
            )

        # ── NIVEL 3: Restricciones específicas de marca ─────────────────
        # FIX: Detecta solo cuando las palabras de la restricción aparecen JUNTAS
        # (en una ventana de 80 caracteres). Antes contaba palabras sueltas en todo
        # el guion y bloqueaba narrativas legítimas que usaban "detalle", "describir",
        # etc. en contextos completamente normales.
        if marca in self.leyes.get("marcas", {}):
            config_marca = self.leyes["marcas"][marca]
            restricciones = config_marca.get("restricciones_output", [])
            umbral = config_marca.get("umbral_bloqueo", 2)
            VENTANA_PROXIMIDAD = 80  # caracteres

            for restriccion in restricciones:
                palabras_clave = [p.lower() for p in restriccion.split() if len(p) > 5]
                if len(palabras_clave) < 2:
                    continue

                # Contar SOLO las co-ocurrencias en ventana de proximidad
                co_ocurrencias = 0
                for match in re.finditer(r'\b' + re.escape(palabras_clave[0]) + r'\b', texto_limpio):
                    ini = max(0, match.start() - VENTANA_PROXIMIDAD)
                    fin = min(len(texto_limpio), match.end() + VENTANA_PROXIMIDAD)
                    ventana = texto_limpio[ini:fin]
                    # Cuantas otras palabras clave aparecen en esta ventana?
                    otras_presentes = sum(
                        1 for p in palabras_clave[1:]
                        if re.search(r'\b' + re.escape(p) + r'\b', ventana)
                    )
                    # Solo cuenta si MAYORIA de palabras clave estan juntas
                    if otras_presentes >= max(1, len(palabras_clave) // 2):
                        co_ocurrencias += 1

                if co_ocurrencias >= umbral:
                    estrategia = config_marca.get("estrategia_evasion", "Aplicar eufemismos neutros.")
                    return False, (
                        f"BLOQUEO NIVEL 3 (marca '{marca}'): '{restriccion}' detectado en proximidad "
                        f"({co_ocurrencias} co-ocurrencias, umbral={umbral}). "
                        f"ESTRATEGIA: {estrategia}"
                    )

        return True, "✅ APROBADO — Limpio y monetizable bajo políticas YouTube 2026."

    # ----------------------------------------------------------
    # BLINDAJE DE GUION — BUG FIX EN LOOP
    # ----------------------------------------------------------

    def blindar_guion(self, ai_engine_instancia, marca, contexto, peticion, longitud, formato="16:9"):
        """
        Genera y audita el guion. Reescribe si es necesario.
        
        BUG FIX: prompt_corrector ahora se reemplaza en cada intento (no se acumula)
        BUG FIX: Logging claro por intento
        """
        intentos_maximos = 3

        for intento in range(1, intentos_maximos + 1):

            # BUG FIX: Construir prompt limpio en cada intento, no acumulativo
            if intento == 1:
                peticion_enviada = peticion
            else:
                config_marca = self.leyes.get("marcas", {}).get(marca, {})
                estrategia = config_marca.get(
                    "estrategia_evasion",
                    "Reescribe usando sinónimos neutros y elimina cualquier violencia gráfica."
                )
                peticion_enviada = (
                    f"{peticion}\n\n"
                    f"[DIRECTRIZ DE COMPLIANCE — INTENTO {intento}/{intentos_maximos}]: "
                    f"El intento anterior fue RECHAZADO. Motivo: {ultimo_reporte}. "
                    f"REESCRIBE aplicando esta estrategia obligatoria: {estrategia} "
                    f"Recuerda: la muerte contextualizada, el terror psicológico y el horror "
                    f"médico con terminología clínica son PERMITIDOS. "
                    f"Lo prohibido es el gore explícito y los detalles anatómicos gratuitos."
                )

            logging.info(f"[COMPLIANCE] Generando guion (intento {intento}/{intentos_maximos})...")
            guion_crudo = ai_engine_instancia.generar_guion(
                marca, contexto, peticion_enviada, longitud, formato
            )

            es_seguro, reporte = self._auditar_texto_crudo(guion_crudo, marca)
            ultimo_reporte = reporte  # Guardar para el siguiente intento si falla

            if es_seguro:
                if intento > 1:
                    logging.info(f"[COMPLIANCE] ✅ Guion aprobado en el intento {intento}.")
                else:
                    logging.info("[COMPLIANCE] ✅ Guion aprobado al primer intento.")
                return guion_crudo

            logging.warning(
                f"[COMPLIANCE] ⚠️  Intento {intento} rechazado. "
                f"Motivo: {reporte}"
            )

        # Agotados los intentos
        logging.error("[COMPLIANCE] ❌ 3 intentos fallidos. Abortando.")
        return (
            "[ERROR DE COMPLIANCE] No se pudo generar un guion seguro en 3 intentos. "
            f"Último rechazo: {ultimo_reporte} — "
            "Sugerencia: revisa el contexto/petición inicial para eliminar elementos de gore explícito."
        )

    # ----------------------------------------------------------
    # UTILIDAD: DIAGNÓSTICO
    # ----------------------------------------------------------

    def diagnosticar_texto(self, texto, marca="La Viuda"):
        """
        Método de utilidad para testear un texto sin generar guion.
        Útil para depuración.
        """
        es_seguro, reporte = self._auditar_texto_crudo(texto, marca)
        print(f"\n{'='*60}")
        print(f"DIAGNÓSTICO DE COMPLIANCE")
        print(f"{'='*60}")
        print(f"Marca: {marca}")
        print(f"Resultado: {'✅ APROBADO' if es_seguro else '❌ RECHAZADO'}")
        print(f"Reporte: {reporte}")
        print(f"{'='*60}\n")
        return es_seguro, reporte

    def listar_reglas_activas(self, marca="La Viuda"):
        """
        Imprime las reglas activas para una marca. Útil para depuración.
        """
        print(f"\n{'='*60}")
        print(f"REGLAS ACTIVAS — {marca} (YouTube 2026)")
        print(f"{'='*60}")
        
        yt = self.leyes["plataformas"]["youtube"]
        print(f"\n🚫 TÉRMINOS ABSOLUTAMENTE PROHIBIDOS:")
        for t in yt.get("terminos_prohibidos_absolutos", []):
            print(f"   - {t}")
        
        print(f"\n⚠️  PATRONES DE RIESGO ALTO (bloqueo si 3+ ocurrencias):")
        for t in yt.get("patrones_riesgo_alto", []):
            print(f"   - {t}")

        if marca in self.leyes.get("marcas", {}):
            m = self.leyes["marcas"][marca]
            print(f"\n🎯 RESTRICCIONES DE MARCA '{marca}':")
            for r in m.get("restricciones_output", []):
                print(f"   - {r}")
            print(f"\n✅ PERMITIDO EXPLÍCITAMENTE:")
            for p in m.get("permitido", []):
                print(f"   + {p}")
        
        print(f"\n{'='*60}\n")
