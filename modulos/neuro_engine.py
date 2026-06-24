"""
NEURO ENGINE v1.0 — Dark Factory Sistema Pinpinela
Motor de Neuromarketing Automático por Canal.
Se inyecta en el pipeline ANTES de que Gemini genere cualquier contenido.
No sugiere — aplica directamente sin preguntar.
"""

import os
import json
import logging
import time
from datetime import datetime, timezone

# ── BANCO DE ESTRUCTURAS DE APERTURA POR CANAL ────────────────────────────────
# NO son frases fijas (esas se repetirían). Son ESTRUCTURAS/moldes que la IA
# rellena fresco con el tema real de cada video → variedad infinita. Una semilla
# por video fuerza a rotar entre ellas para que no se repita la misma apertura.
# Cada canal tiene varias estructuras distintas; se prohíbe repetir la del video
# anterior (rotación determinista por fecha/hora del video).
APERTURAS_POR_CANAL = {
    "La Viuda": [
        "AFIRMACIÓN DIRECTA EN SEGUNDA PERSONA: declara una experiencia perturbadora como un hecho ya ocurrido, sin preguntar. Ej. de molde (NO copiar literal): 'Esa noche supiste que no estabas solo'.",
        "ESCENA CONCRETA CON HORA: pinta un instante específico (lugar + hora exacta) y rómpelo con algo anómalo. Ej. de molde: 'Las 3:33. El pasillo vacío. Hasta que dejó de estarlo'.",
        "DETALLE SENSORIAL: empieza por un sentido (olor, sonido, temperatura) que anuncia lo inexplicable. Ej. de molde: 'Primero fue el olor. Después, los pasos donde no debía haber nadie'.",
        "OBJETO FUERA DE LUGAR: un objeto cotidiano que cambió solo y no tiene explicación. Ej. de molde: 'Cierras con llave cada noche. ¿Por qué amaneció abierta?'.",
        "TESTIMONIO ANCLADO: presenta a alguien real (nombre + lugar) al borde de algo que no puede explicar.",
        "CONTRADICCIÓN DE LA REALIDAD: dos hechos que no pueden ser ciertos a la vez, ambos lo son.",
        "PREGUNTA INQUIETANTE (úsala con moderación, no siempre): una sola pregunta que planta el miedo sin responderla.",
        "SILENCIO ROTO: describe una calma normal y el momento exacto en que algo la quiebra.",
    ],
    "Monkygraff": [
        "CIFRA IMPACTANTE: abre con un número concreto que reordena el poder. Ej. de molde: 'Tres países concentran el 70% de un recurso que mueve la economía mundial'.",
        "CONTRADICCIÓN OFICIAL: lo que dicen los mapas/medios vs lo que muestran los hechos. Ej. de molde: 'Los comunicados dicen una cosa. El movimiento real, otra'.",
        "PREGUNTA TÁCTICA: una pregunta estratégica que obliga a seguir. Ej. de molde: '¿Por qué tres potencias enviaron flotas al mismo punto?'.",
        "AFIRMACIÓN DE PODER: quién controla qué y por qué importa. Ej. de molde: 'Quien controle este corredor controla el comercio de medio continente'.",
        "CONEXIÓN OCULTA: dos hechos que nadie unió y juntos revelan el tablero. Ej. de molde: 'Dos noticias que parecían sin relación revelan la verdadera jugada'.",
        "GEOGRAFÍA DECISIVA: un punto en el mapa (estrecho, frontera, puerto) del que depende todo.",
        "ACTOR INESPERADO: un país o grupo que nadie miraba y que acaba de cambiar el equilibrio.",
        "RECURSO ESTRATÉGICO: un material/energía/ruta por el que se está jugando una guerra silenciosa.",
    ],
    "FiltradoMX": [
        "CONFESIÓN DIRECTA: abre como quien revela algo que prometió callar. Ej. de molde: 'Nunca conté lo que pasó esa noche. Hasta hoy'.",
        "DETALLE INCRIMINATORIO: un dato pequeño que lo cambia todo en la historia.",
        "PREGUNTA AL ESPECTADOR: una pregunta que lo pone en el lugar del protagonista.",
        "GIRO ANTICIPADO: adelanta que habrá una traición/revelación sin decir cuál.",
        "ESCENA ÍNTIMA: un momento cotidiano que esconde algo turbio debajo.",
        "ADVERTENCIA: avisa que lo que viene es incómodo de escuchar.",
        "CITA TEXTUAL: arranca con algo que alguien dijo y no debió decir.",
    ],
    "LaesquinaRandom": [
        "ABSURDO INMEDIATO: abre con una situación ridícula presentada como normal.",
        "PREGUNTA TONTA-GENIAL: una pregunta absurda que da curiosidad. Ej. de molde: '¿Por qué nadie ha pensado en esto?'.",
        "DATO RIDÍCULO: un 'hecho' exagerado y cómico que engancha.",
        "EXAGERACIÓN: lleva algo cotidiano al extremo más absurdo.",
        "GIRO CÓMICO: empieza serio y rómpelo con humor en la segunda frase.",
        "LISTA IMPOSIBLE: anuncia un conteo de cosas absurdas que vienen.",
    ],
    "TuIALista": [
        "DATO TÉCNICO IMPACTANTE: una capacidad o cifra de IA que sorprende. Ej. de molde: 'Esta herramienta hace en segundos lo que antes tomaba semanas'.",
        "ANTES Y DESPUÉS: contrasta cómo se hacía algo vs cómo se hace ahora con IA.",
        "PREGUNTA ÚTIL: una pregunta práctica que el espectador se ha hecho. Ej. de molde: '¿Y si pudieras automatizar esto sin saber programar?'.",
        "PROMESA CONCRETA: lo que el espectador va a poder hacer al terminar el video.",
        "REVELACIÓN DE HERRAMIENTA: presenta algo que pocos conocen aún.",
        "ERROR COMÚN: el fallo que casi todos cometen y cómo evitarlo.",
    ],
    "Umbral Alterno": [
        "PREMISA HIPOTÉTICA: abre con el '¿qué pasaría si...?' del escenario, atemporal.",
        "PUNTO DE DIVERGENCIA: el instante exacto en que la historia/realidad se bifurca.",
        "CONSECUENCIA IMPACTANTE: adelanta el resultado extremo del escenario.",
        "COMPARACIÓN DE MUNDOS: contrasta el mundo real con el alterno.",
        "PREGUNTA EXISTENCIAL: una pregunta grande sobre el destino o las decisiones.",
        "ESCENARIO EN MARCHA: describe el mundo alterno como si ya existiera.",
    ],
}

def _indice_rotacion(n_opciones, desfase=0):
    """Índice de rotación que recorre TODO el banco aunque los videos se generen
    a intervalos regulares. Avanza de forma fina (cada 30s) para no quedar atrapado
    en pocas opciones por la periodicidad de los intervalos entre videos."""
    try:
        ahora = datetime.now()
        contador = int(ahora.timestamp() // 30)  # avanza cada 30 segundos
        return (contador + desfase) % max(1, n_opciones)
    except Exception:
        return desfase % max(1, n_opciones)

def _seleccionar_aperturas(marca, n=3):
    """Devuelve estructuras de apertura ROTADAS para este video (variedad).
    La rotación recorre todo el banco; la IA rellena el molde con el tema real."""
    bank = None
    for k, v in APERTURAS_POR_CANAL.items():
        if k.lower().strip() == (marca or "").lower().strip():
            bank = v; break
    if not bank:
        return []
    inicio = _indice_rotacion(len(bank), desfase=0)
    seleccion = [bank[(inicio + i) % len(bank)] for i in range(min(n, len(bank)))]
    return seleccion


# ── BANCO DE ESTRUCTURAS DE CIERRE POR CANAL ──────────────────────────────────
# Igual que las aperturas: moldes que la IA rellena con el contenido real del
# video → cierres siempre distintos. Rotación por tiempo para no repetir. El
# cierre busca retención (suscripción / siguiente video / comentarios) sin sonar
# siempre igual y sin frases de fecha que envejezcan.
CIERRES_POR_CANAL = {
    "La Viuda": [
        "PREGUNTA QUE PERSIGUE: cierra con una pregunta inquietante que el espectador se llevará a la cama. NO la respondas.",
        "HILO SUELTO: deja un detalle sin explicar que invita a comentar teorías.",
        "VUELTA AL INICIO: conecta el final con la imagen del hook, dándole un giro perturbador.",
        "ADVERTENCIA FINAL: cierra avisando que esto podría pasarle a quien escucha.",
        "DATO QUE ESCALA: revela un último dato que hace todo más inquietante.",
        "INVITACIÓN A LA OSCURIDAD: pide al espectador que comparta su propia experiencia similar en comentarios.",
    ],
    "Monkygraff": [
        "PRÓXIMO MOVIMIENTO: cierra señalando qué hecho concreto vigilar a futuro (atemporal).",
        "PREGUNTA ESTRATÉGICA: deja una pregunta geopolítica abierta para los comentarios.",
        "IMPLICACIÓN PERSONAL: conecta el tema con cómo afecta al espectador o a su región.",
        "ESCENARIO ABIERTO: plantea dos desenlaces posibles y pregunta cuál creen que ocurrirá.",
        "CONEXIÓN PENDIENTE: insinúa otra pieza del tablero que se analizará en otro video.",
        "LLAMADO A SEGUIR: invita a suscribirse para no perder el siguiente análisis del tablero.",
    ],
    "FiltradoMX": [
        "GIRO FINAL: cierra con una última revelación que reconfigura todo lo contado.",
        "PREGUNTA AL ESPECTADOR: pídele que juzgue o tome partido en comentarios.",
        "HILO PARA OTRO CASO: insinúa que hay más historias como esta por contar.",
        "MORALEJA INCÓMODA: cierra con una reflexión que deja pensando.",
        "PREGUNTA ABIERTA: '¿Qué habrías hecho tú?' adaptada al caso.",
        "INVITACIÓN A COMPARTIR: pide que cuenten si vivieron algo parecido.",
    ],
    "LaesquinaRandom": [
        "REMATE CÓMICO: cierra con el chiste o giro absurdo más fuerte.",
        "PREGUNTA RIDÍCULA: lanza una pregunta tonta-genial para comentarios.",
        "LLAMADO JUGUETÓN: pide suscripción de forma cómica, no seria.",
        "EXAGERACIÓN FINAL: cierra llevando la premisa al absurdo total.",
        "RETO AL ESPECTADOR: propón algo absurdo para que comenten.",
        "CLIFFHANGER TONTO: deja una mini intriga cómica para el próximo video.",
    ],
    "TuIALista": [
        "RESUMEN ACCIONABLE: cierra con el paso concreto que el espectador debe dar ya.",
        "PRÓXIMA HERRAMIENTA: insinúa otra herramienta/truco que verás en otro video.",
        "PREGUNTA PRÁCTICA: pregunta qué les gustaría automatizar, para comentarios.",
        "PROMESA CUMPLIDA: recuerda lo que aprendieron e invita a aplicarlo.",
        "LLAMADO A SUSCRIBIRSE: por más tutoriales/herramientas de IA.",
        "RETO PRÁCTICO: propón que prueben lo enseñado y comenten el resultado.",
    ],
    "Umbral Alterno": [
        "PREGUNTA EXISTENCIAL: cierra con una gran pregunta sobre el destino o las decisiones.",
        "ESCENARIO ABIERTO: deja el mundo alterno sin resolver, invitando a imaginar.",
        "VUELTA A LA REALIDAD: contrasta el final con nuestro mundo y deja pensando.",
        "PRÓXIMO UMBRAL: insinúa otro escenario hipotético para un futuro video.",
        "DECISIÓN AL ESPECTADOR: pregunta qué habrían elegido ellos.",
        "REFLEXIÓN FINAL: cierra con una idea que resuena más allá del video.",
    ],
}

def _seleccionar_cierres(marca, n=2):
    """Devuelve estructuras de CIERRE rotadas para este video (variedad).
    La IA rellena el molde con el contenido real del video."""
    bank = None
    for k, v in CIERRES_POR_CANAL.items():
        if k.lower().strip() == (marca or "").lower().strip():
            bank = v; break
    if not bank:
        return []
    # desfase distinto al de aperturas para que apertura y cierre no roten igual
    inicio = _indice_rotacion(len(bank), desfase=3)
    seleccion = [bank[(inicio + i) % len(bank)] for i in range(min(n, len(bank)))]
    return seleccion

# ── ADN DE NEUROMARKETING POR CANAL ───────────────────────────────────────────
# Cada canal tiene gatillos psicológicos específicos basados en su nicho.
# Escalable: agregar nuevos canales sin tocar el resto del código.
ADN_NEURO = {
    "La Viuda": {
        "gatillos_primarios": [
            "miedo_a_lo_desconocido",
            "disonancia_cognitiva",
            "loop_tension_alivio",
            "efecto_testigo",
        ],
        "estructura_narrativa": "tension_progresiva",
        "formula_hook": (
            "Abre con una experiencia personal perturbadora en segunda persona. "
            "Nunca expliques en el hook — planta la semilla del miedo inexplicable. "
            "VARÍA la apertura en cada video, NO empieces siempre con '¿Alguna vez...?'. "
            "Alterna entre: (a) una afirmación directa ('Esa noche supiste que no estabas solo en casa'), "
            "(b) una escena concreta ('Las 3:33 de la madrugada. El pasillo estaba vacío. Hasta que dejó de estarlo'), "
            "(c) un detalle sensorial ('Primero fue el olor. Después, el sonido de pasos donde no debía haber nadie'), "
            "(d) una segunda persona inquietante ('Cierras la puerta con llave todas las noches. Entonces, ¿por qué amaneció abierta?'), "
            "(e) ocasionalmente una pregunta, pero no siempre. "
            "Nunca repitas la misma estructura de apertura que un video anterior."
        ),
        "ritmo_cortes": {"short": 4, "largo": 10},
        "palabras_gatillo": [
            "no estabas solo", "algo no está bien", "lo sentiste antes",
            "no puedes ignorarlo", "nadie lo vio", "silencio absoluto",
            "tú lo sabes", "no fue tu imaginación", "esa sensación",
            "lo que no se ve", "en la oscuridad", "esa noche"
        ],
        "estetica_miniatura": (
            "Paleta: negro profundo, azul oscuro, verde tenue. "
            "Sin personas. Objetos cotidianos en contextos perturbadores: "
            "silla vacía iluminada, puerta entreabierta con luz tenue, ventana oscura. "
            "Alto contraste. Elemento de misterio visible pero sin explicación."
        ),
        "arco_retencion_largo": [
            "0-2min: Hook perturbador + promesa de algo inexplicable",
            "2-8min: Contexto que construye atmósfera de tensión psicológica",
            "8-15min: Primer giro — algo no cuadra con la realidad",
            "15-22min: Escalada de paranoia y tensión psicológica máxima",
            "22-28min: Revelación perturbadora — más preguntas que respuestas",
            "28-30min: Cierre abierto que persigue al espectador"
        ],
    },

    "Monkygraff": {
        "gatillos_primarios": [
            "autoridad_tactica",
            "urgencia_informativa",
            "efecto_revelacion",
            "prueba_social_inversa",
        ],
        "estructura_narrativa": "revelacion_progresiva",
        "formula_hook": (
            "Abre con un dato concreto, un número específico o una conexión que contradice la narrativa oficial. "
            "Usa cifras, nombres de países y hechos verificables. "
            "PROHIBIDO ABSOLUTAMENTE abrir con marcos de tiempo relativos que envejecen el video: NO uses "
            "'en las últimas 72 horas', 'en las últimas 48 horas', 'en las últimas horas', 'esta semana', "
            "'recientemente', 'acaba de ocurrir', 'hace unos días' ni nada que ate el video a una fecha cercana "
            "(el video se ve durante meses y esas frases lo hacen parecer viejo). "
            "En su lugar, abre con el HECHO o la TENSIÓN en sí, atemporal. "
            "VARÍA la apertura en cada video — alterna entre estas estructuras: "
            "(a) una cifra impactante ('Tres países acaban de mover el 40% de las reservas mundiales de litio'), "
            "(b) una contradicción ('Los mapas oficiales muestran una cosa. El movimiento de tropas muestra otra'), "
            "(c) una pregunta táctica ('¿Por qué tres potencias enviaron flotas al mismo punto del Pacífico?'), "
            "(d) una afirmación de poder ('Quien controle este corredor de 80 km controla el comercio de medio continente'), "
            "(e) una conexión oculta ('Dos noticias que nadie unió revelan el verdadero tablero'). "
            "Nunca repitas la misma estructura de apertura que un video anterior."
        ),
        "ritmo_cortes": {"short": 3, "largo": 12},
        "palabras_gatillo": [
            "nadie lo conectó", "esto cambia el tablero",
            "el mapa real", "lo que no te dicen", "movimiento táctico",
            "fuentes verificadas", "el dato que importa", "señal clara",
            "la jugada de fondo", "la conexión que nadie hizo", "el verdadero objetivo"
        ],
        "temas_prioritarios_2026": [
            "Guerra Rusia-Ucrania y minerales estratégicos",
            "Guerra comercial Trump vs China aranceles",
            "China vs Taiwán — escenarios de invasión",
            "BRICS y desdolarización",
            "Minerales críticos: litio, cobalto, tierras raras",
            "IA como arma geopolítica",
            "Venezuela y operaciones encubiertas de EE.UU.",
            "Rearmamiento europeo post-OTAN",
            "Narcoestados y carteles como actores geopolíticos",
            "Mar Rojo y rutas comerciales globales"
        ],
        "estetica_miniatura": (
            "Paleta: gris acero, azul oscuro, rojo alerta, verde militar. "
            "Sin personas. Infraestructura, mapas, instalaciones militares vacías, vehículos sin conductor, puertos, refinerías. "
            "Estilo fotoperiodismo Reuters. Sensación de urgencia táctica. "
            "Como si fuera información clasificada que acaba de filtrarse."
        ),
        "arco_retencion_largo": [
            "0-2min: Dato impactante y específico + promesa de análisis exclusivo que nadie más hará (SIN fechas relativas que envejezcan)",
            "2-8min: Contexto geopolítico — por qué este momento es diferente a todo lo anterior",
            "8-15min: Análisis táctico profundo — conexiones no obvias entre eventos aparentemente separados",
            "15-22min: El dinero detrás de la guerra — quién financia, quién gana, quién pierde",
            "22-28min: Implicaciones para América Latina — cómo esto te afecta directamente",
            "28-30min: El próximo movimiento a vigilar + llamado a acción"
        ],
    },

    # ── PLANTILLA PARA NUEVO CANAL ──────────────────────────────────────────
    # "NuevoCanal": {
    #     "gatillos_primarios": [],
    #     "estructura_narrativa": "",
    #     "formula_hook": "",
    #     "ritmo_cortes": {"short": 4, "largo": 10},
    #     "palabras_gatillo": [],
    #     "estetica_miniatura": "",
    #     "arco_retencion_largo": [],
    # },
}

# ── ESTRATEGIAS DE RETENCIÓN UNIVERSAL ────────────────────────────────────────
# Aplican a todos los canales independientemente del nicho
ESTRATEGIAS_UNIVERSALES = {
    "open_loop": (
        "Nunca cierres una pregunta antes de abrir otra. "
        "El espectador debe sentir que si para el video pierde información crítica."
    ),
    "pattern_interrupt": (
        "Cada 30-45 segundos introduce un cambio de ritmo, tono o información "
        "inesperada que resetea la atención del cerebro."
    ),
    "segunda_persona": (
        "Habla directamente al espectador en segunda persona. "
        "'Tú', 'tu', 'te' — el cerebro no puede ignorar cuando se dirigen a él directamente."
    ),
    "especificidad": (
        "Datos específicos generan más credibilidad y retención que generalizaciones. "
        "'3 de cada 4 casos' es más poderoso que 'la mayoría de los casos'."
    ),
    "cierre_abierto": (
        "Nunca cierres completamente la historia. Deja un hilo suelto que "
        "invite al siguiente video o a los comentarios."
    ),
}


class NeuroEngine:
    """
    Motor de Neuromarketing Automático.
    Analiza tendencias, selecciona estrategias y las inyecta en todo el pipeline.
    """

    def __init__(self):
        self.adn = ADN_NEURO
        self.universales = ESTRATEGIAS_UNIVERSALES

    def _obtener_adn_canal(self, marca):
        """Retorna el ADN de neuromarketing del canal o el default."""
        for key in self.adn:
            if key.lower() in marca.lower() or marca.lower() in key.lower():
                return self.adn[key], key
        # Default: usar La Viuda como base
        return self.adn.get("La Viuda", {}), marca

    def _buscar_tendencias_youtube(self, marca, api_key):
        """
        Busca tendencias reales en YouTube para el nicho del canal.
        Si no hay API key, usa datos estructurados de respaldo.
        """
        adn, _ = self._obtener_adn_canal(marca)

        if not api_key:
            logging.warning("[NEURO ENGINE] Sin YouTube API key — usando base de conocimiento interna.")
            return self._tendencias_respaldo(marca)

        try:
            from googleapiclient.discovery import build

            youtube = build('youtube', 'v3', developerKey=api_key)

            # Términos de búsqueda basados en el nicho
            terminos = {
                "La Viuda": ["terror psicologico", "misterio sin resolver", "caso real perturbador"],
                "Monkygraff": ["geopolitica actual", "conflicto internacional", "analisis tactico"]
            }
            busquedas = terminos.get(marca, ["videos virales"])

            resultados_totales = []
            for termino in busquedas[:2]:  # Máximo 2 búsquedas para no gastar cuota
                try:
                    res = youtube.search().list(
                        q=termino,
                        part='snippet',
                        type='video',
                        order='viewCount',
                        relevanceLanguage='es',
                        publishedAfter=(
                            datetime.now(timezone.utc)
                            .replace(hour=0, minute=0, second=0)
                            .__class__.fromtimestamp(
                                datetime.now(timezone.utc).timestamp() - 72*3600,
                                tz=timezone.utc
                            ).strftime('%Y-%m-%dT%H:%M:%SZ')
                        ),
                        maxResults=5
                    ).execute()

                    for item in res.get('items', []):
                        resultados_totales.append({
                            "titulo": item['snippet']['title'],
                            "canal": item['snippet']['channelTitle'],
                            "termino": termino
                        })
                except Exception as e:
                    logging.warning(f"[NEURO ENGINE] Error en búsqueda '{termino}': {e}")
                    continue

            if resultados_totales:
                return resultados_totales
            return self._tendencias_respaldo(marca)

        except ImportError:
            logging.warning("[NEURO ENGINE] googleapiclient no instalado — usando respaldo.")
            return self._tendencias_respaldo(marca)
        except Exception as e:
            logging.error(f"[NEURO ENGINE] Error YouTube API: {e}")
            return self._tendencias_respaldo(marca)

    def _tendencias_respaldo(self, marca):
        """Tendencias estructuradas de respaldo cuando no hay API."""
        respaldo = {
            "La Viuda": [
                {"titulo": "El caso que la policía nunca resolvió", "canal": "Terror Real", "termino": "misterio sin resolver"},
                {"titulo": "Lo que encontraron en el edificio abandonado", "canal": "Misterios MX", "termino": "casos reales"},
                {"titulo": "La historia que nadie quiere escuchar", "canal": "Paranoia TV", "termino": "terror psicologico"},
            ],
            "Monkygraff": [
                {"titulo": "El movimiento que está redibujando el mapa de poder", "canal": "Geopolitica Táctica", "termino": "conflicto internacional"},
                {"titulo": "La conexión que los medios no quieren que veas", "canal": "Análisis Global", "termino": "geopolitica actual"},
                {"titulo": "La base que nadie debía encontrar", "canal": "Intel Táctica", "termino": "tecnología militar"},
            ]
        }
        return respaldo.get(marca, respaldo["La Viuda"])

    def generar_directriz_neuro(self, marca, formato, api_key=None):
        """
        Genera la directriz completa de neuromarketing para inyectar en Gemini.
        Analiza tendencias, selecciona estrategias y las estructura en un prompt.
        """
        adn, nombre_canal = self._obtener_adn_canal(marca)
        es_largo = "16:9" in formato or formato.upper() == "LARGO"

        # Obtener tendencias actuales
        tendencias = self._buscar_tendencias_youtube(marca, api_key)
        titulos_competencia = [t["titulo"] for t in tendencias[:3]]

        # Seleccionar gatillos primarios (primeros 2 más efectivos)
        gatillos = adn.get("gatillos_primarios", [])[:2]
        palabras = adn.get("palabras_gatillo", [])[:6]
        formula_hook = adn.get("formula_hook", "")
        estetica = adn.get("estetica_miniatura", "")
        arco = adn.get("arco_retencion_largo", [])

        # ROTACIÓN DE APERTURAS: estructuras distintas en cada video (variedad infinita).
        # La IA rellena el molde con el tema real; la rotación evita repetir aperturas.
        _aperturas = _seleccionar_aperturas(nombre_canal, n=3)
        if _aperturas:
            _bloque_aperturas = (
                "\n\n━━━ APERTURA OBLIGATORIA (VARIEDAD) ━━━\n"
                "Para ESTE video, abre el guión usando UNA de estas estructuras (elige la que mejor "
                "encaje con el tema, pero NO uses siempre la misma en videos distintos). Rellénala con "
                "el tema real y específico de hoy. Genera una apertura NUEVA, no copies los ejemplos:\n"
                + "\n".join(f"  {i+1}. {a}" for i, a in enumerate(_aperturas))
                + "\nNUNCA abras con frases de tiempo relativo que envejecen el video "
                  "('en las últimas 72 horas', 'esta semana', 'recientemente', 'acaba de ocurrir', "
                  "'hace unos días'). El video se ve durante meses: la apertura debe ser ATEMPORAL."
            )
            formula_hook = formula_hook + _bloque_aperturas

        # ROTACIÓN DE CIERRES: estructuras de cierre distintas en cada video.
        _cierres = _seleccionar_cierres(nombre_canal, n=2)
        _bloque_cierres = ""
        if _cierres:
            _bloque_cierres = (
                "\n\n━━━ CIERRE OBLIGATORIO (VARIEDAD) ━━━\n"
                "Cierra el guión usando UNA de estas estructuras (la que mejor cierre ESTE tema). "
                "Rellénala con el contenido real del video. Genera un cierre NUEVO, no copies literal, "
                "y NO uses siempre el mismo tipo de cierre en videos distintos:\n"
                + "\n".join(f"  {i+1}. {c}" for i, c in enumerate(_cierres))
                + "\nEl cierre debe ser ATEMPORAL (sin fechas relativas) y dejar al espectador con ganas "
                  "de suscribirse, comentar o ver otro video."
            )

        # Construir directriz completa
        directriz = f"""
[DIRECTRIZ DE NEUROMARKETING — SISTEMA PINPINELA]

CANAL: {nombre_canal}
FORMATO: {"VIDEO LARGO" if es_largo else "SHORT"}

━━━ 1. TENDENCIAS EN COMPETENCIA (últimas 72h) ━━━
Los siguientes títulos están generando alta tracción en tu nicho ahora mismo.
NO copies — supéralos en gancho, retención y profundidad:
{chr(10).join(f'• {t}' for t in titulos_competencia)}

━━━ 2. GATILLOS PSICOLÓGICOS ACTIVOS ━━━
Aplica estos gatillos de forma natural en el guión:
{chr(10).join(f'• {g.replace("_", " ").upper()}: {_describir_gatillo(g)}' for g in gatillos)}

━━━ 3. FÓRMULA DEL HOOK ━━━
{formula_hook}
{_bloque_cierres}

━━━ 4. PALABRAS DE ALTO IMPACTO NEUROLÓGICO ━━━
Integra estas palabras de forma natural, no forzada:
{', '.join(palabras)}

━━━ 5. ESTRATEGIAS UNIVERSALES DE RETENCIÓN ━━━
• OPEN LOOP: {ESTRATEGIAS_UNIVERSALES['open_loop']}
• SEGUNDA PERSONA: {ESTRATEGIAS_UNIVERSALES['segunda_persona']}
• ESPECIFICIDAD: {ESTRATEGIAS_UNIVERSALES['especificidad']}

{f'━━━ 6. ARCO DE RETENCIÓN PARA VIDEO LARGO ━━━{chr(10)}{chr(10).join(arco)}' if es_largo else '━━━ 6. RITMO SHORT ━━━{chr(10)}Corte de imagen cada {adn.get("ritmo_cortes", {}).get("short", 4)} segundos. Cada frase debe poder leerse en ese tiempo.'}

━━━ 7. ESTÉTICA PARA MINIATURA (solo si aplica) ━━━
{estetica}

INSTRUCCIÓN FINAL: Todo lo anterior debe estar IMPLÍCITO en el guión y los prompts.
No menciones estas estrategias explícitamente. Simplemente aplícalas.
El resultado debe sentirse natural, no manipulador.
"""
        return directriz.strip()

    def enriquecer_contexto(self, contexto_original, marca, formato, api_key=None):
        """
        Punto de entrada principal.
        Toma el contexto original y le inyecta la capa de neuromarketing.
        Retorna el contexto enriquecido listo para Gemini.
        """
        print(f"[NEURO ENGINE] Activando matriz de neuromarketing para {marca}...")
        directriz = self.generar_directriz_neuro(marca, formato, api_key)
        contexto_enriquecido = f"{contexto_original}\n\n{directriz}"
        print(f"[NEURO ENGINE] Directriz inyectada. Pipeline optimizado para retención máxima.")
        return contexto_enriquecido


def _describir_gatillo(gatillo):
    """Descripción ejecutable de cada gatillo psicológico."""
    descripciones = {
        "miedo_a_lo_desconocido": "El cerebro llena los vacíos con terror. Deja preguntas sin respuesta inmediata.",
        "disonancia_cognitiva": "Presenta información que contradice lo que el espectador creía saber.",
        "loop_tension_alivio": "Crea tensión sostenida con micro-alivios cada 30-45 segundos que enganchan.",
        "efecto_testigo": "Ancla la historia a personas reales con nombres y fechas específicas.",
        "autoridad_tactica": "El narrador demuestra saber más. Usa datos precisos y jerga especializada.",
        "urgencia_informativa": "Transmite que esto importa AHORA por su relevancia, sin frases de fecha relativa ('últimas horas', 'esta semana') que envejecen el video. La urgencia viene del peso del hecho, no de la fecha.",
        "efecto_revelacion": "Presenta la información como exclusiva y valiosa, algo que pocos conectaron, sin sugerir que 'desaparecerá' o que es de una fecha concreta.",
        "prueba_social_inversa": "Los que saben ya lo saben. ¿Tú eres de los que saben?",
    }
    return descripciones.get(gatillo, "Aplica con naturalidad según el contexto.")
