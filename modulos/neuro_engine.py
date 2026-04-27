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
            "Ejemplo: 'Alguna vez te has despertado a las 3 de la mañana sintiendo que alguien te observa. "
            "Y no había nadie. O eso creías.'"
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
            "Abre con un dato concreto e impactante ocurrido en las últimas 72 horas que contradice la narrativa oficial. "
            "Usa números específicos, nombres de países y fechas reales. "
            "Ejemplo: 'En las últimas 48 horas, tres movimientos que los medios no conectaron acaban de redefinir el mapa de poder global. "
            "Y ninguno de ellos apareció en los titulares.'"
        ),
        "ritmo_cortes": {"short": 3, "largo": 12},
        "palabras_gatillo": [
            "nadie lo reportó", "en las últimas horas", "esto cambia todo",
            "el mapa real", "lo que no te dicen", "movimiento táctico",
            "fuentes verificadas", "antes de que lo borren", "señal clara",
            "datos clasificados", "acaba de ocurrir", "conexión que nadie hizo"
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
            "0-2min: Dato impactante ocurrido HOY + promesa de análisis exclusivo que nadie más hará",
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
                "Monkygraff": ["geopolitica 2025", "conflicto internacional", "analisis tactico"]
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
                {"titulo": "El movimiento que cambió el mapa en 48 horas", "canal": "Geopolitica Táctica", "termino": "conflicto internacional"},
                {"titulo": "Lo que los medios no conectaron esta semana", "canal": "Análisis Global", "termino": "geopolitica 2025"},
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
        "urgencia_informativa": "Todo sucede AHORA. Usa tiempos presentes y marcadores temporales recientes.",
        "efecto_revelacion": "Presenta información como si fuera exclusiva y temporalmente disponible.",
        "prueba_social_inversa": "Los que saben ya lo saben. ¿Tú eres de los que saben?",
    }
    return descripciones.get(gatillo, "Aplica con naturalidad según el contexto.")
