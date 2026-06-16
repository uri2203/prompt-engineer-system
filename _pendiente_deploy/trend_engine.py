import os
import json
import logging
from datetime import datetime, timezone

class TrendEngine:
    """
    Módulo de Inteligencia Competitiva (Trend Engine)
    Silo Hermético encargado del Espionaje Algorítmico y cálculo de Velocidad de Visualización (VPH).
    """
    def __init__(self):
        # Aislamiento por Silos Herméticos
        self.nicho_marcas = {
            "La Viuda": [
                "historias de terror reales",
                "relatos de miedo narrados",
                "experiencias paranormales",
                "casos de terror psicologico"
            ],
            "Monkygraff": [
                "geopolitica mundial analisis",
                "guerra comercial China Estados Unidos",
                "conflictos geopoliticos actuales",
                "tension militar mundial"
            ],
            "FiltradoMX": [
                "historias de infidelidad reales",
                "casos de traicion familiar",
                "dramas de la vida real",
                "confesiones reales impactantes"
            ],
            "LaesquinaRandom": [
                "datos curiosos increibles",
                "curiosidades que no sabias",
                "hechos sorprendentes",
                "cosas raras del mundo"
            ],
            "TuIALista": [
                "inteligencia artificial noticias",
                "herramientas IA nuevas",
                "avances inteligencia artificial",
                "IA tecnologia futuro"
            ],
            "Umbral Alterno": [
                "que pasaria si escenario",
                "simulacion del futuro",
                "historia alternativa que hubiera pasado",
                "como seria el mundo si"
            ],
        }

    def _calcular_vph(self, vistas, fecha_publicacion):
        """
        Calcula la Velocidad de Visualización (Views Per Hour).
        Métrica crítica para determinar si una tendencia está viva o muerta.
        """
        try:
            ahora = datetime.now(timezone.utc)
            # Asegurar formato compatible con ISO 8601 de APIs estándar
            fecha_pub = datetime.fromisoformat(fecha_publicacion.replace('Z', '+00:00'))
            horas_transcurridas = (ahora - fecha_pub).total_seconds() / 3600

            # Piso mínimo de 1 hora: un video publicado hace minutos no debe
            # dar un VPH astronómico (evita dividir entre casi cero).
            if horas_transcurridas < 1:
                horas_transcurridas = 1

            return round(vistas / horas_transcurridas, 1)
        except Exception as e:
            logging.error(f"[TREND ENGINE] Error matemático al calcular VPH: {e}")
            return 0

    def _conectar_extraccion_nube(self, api_key, query):
        """
        Puerta de enlace para la API de YouTube Data v3.
        Extrae la data cruda de los competidores.
        PREPARADO: en cuanto se agregue la API key en la Bóveda, funciona en vivo.
        Sin key (o si falla la cuota), cae a simulación para no romper la fábrica.
        """
        if not api_key:
            logging.warning(f"[TREND ENGINE] Llave de API no detectada en la Bóveda. Simulación activada para: {query}")
            return self._simular_respuesta_api(query)

        # ── ESCANEO EN VIVO (YouTube Data v3) ──
        try:
            import requests as _rq
            from datetime import datetime, timedelta, timezone as _tz
            # Videos publicados en los últimos 30 días (ventana amplia = más resultados)
            hace_mes = (datetime.now(_tz.utc) - timedelta(days=30)).isoformat()
            # 1. Buscar videos recientes del término
            r = _rq.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "key": api_key, "q": query, "part": "snippet",
                    "type": "video", "order": "viewCount",
                    "publishedAfter": hace_mes, "maxResults": 10,
                    "regionCode": "MX",
                },
                timeout=15
            )
            if r.status_code != 200:
                logging.warning(f"[TREND ENGINE] YouTube API HTTP {r.status_code} — fallback a simulación.")
                return self._simular_respuesta_api(query)

            items = r.json().get("items", [])
            if not items:
                return self._simular_respuesta_api(query)

            # 2. Obtener estadísticas (vistas) de esos videos
            video_ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
            rs = _rq.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"key": api_key, "id": ",".join(video_ids), "part": "statistics,snippet"},
                timeout=15
            )
            if rs.status_code != 200:
                return self._simular_respuesta_api(query)

            resultados = []
            for v in rs.json().get("items", []):
                stats = v.get("statistics", {})
                snip = v.get("snippet", {})
                resultados.append({
                    "titulo": snip.get("title", query),
                    "vistas": int(stats.get("viewCount", 0)),
                    "fecha_publicacion": snip.get("publishedAt", datetime.now(_tz.utc).isoformat()),
                    "canal": snip.get("channelTitle", "Competidor"),
                })
            logging.info(f"[TREND ENGINE] Escaneo EN VIVO ok: {len(resultados)} videos para '{query}'.")
            return resultados if resultados else self._simular_respuesta_api(query)

        except Exception as e:
            logging.warning(f"[TREND ENGINE] Error en escaneo en vivo ({e}) — fallback a simulación.")
            return self._simular_respuesta_api(query)

    def _simular_respuesta_api(self, query):
        """
        Estructura de respaldo. Mantiene la fábrica operativa y prevé bloqueos de Render
        en caso de que la cuota de la API se agote. Variado para no repetir siempre.
        """
        import random as _r
        fecha_reciente = datetime.now(timezone.utc).isoformat()
        plantillas = [
            "El secreto oculto de {q}",
            "La verdad clasificada sobre {q}",
            "Lo que nadie te contó de {q}",
            "El caso de {q} que cambió todo",
            "Por qué {q} es más grave de lo que crees",
            "La historia real detrás de {q}",
        ]
        elegidas = _r.sample(plantillas, 2)
        return [
            {"titulo": elegidas[0].format(q=query), "vistas": _r.randint(80000, 250000), "fecha_publicacion": fecha_reciente, "canal": "Competidor Alpha"},
            {"titulo": elegidas[1].format(q=query), "vistas": _r.randint(40000, 120000), "fecha_publicacion": fecha_reciente, "canal": "Competidor Beta"},
        ]

    def escanear_traccion_competitiva(self, marca, api_key=None, temas_usados=None):
        """
        Punto de entrada principal del silo.
        Ejecuta el ciclo de combate y retorna la tendencia con mayor tracción algorítmica.
        'temas_usados' = lista de títulos ya generados antes, para NO repetir.
        """
        logging.info(f"[TREND ENGINE] Iniciando radar de tracción para: {marca}")
        temas_usados = [str(t).lower().strip() for t in (temas_usados or [])]

        if marca not in self.nicho_marcas:
            logging.error(f"[TREND ENGINE] Falla de aislamiento: Marca '{marca}' no reconocida.")
            return None

        tendencias_detectadas = []

        for termino in self.nicho_marcas[marca]:
            resultados_crudos = self._conectar_extraccion_nube(api_key, termino)

            for video in resultados_crudos:
                vph = self._calcular_vph(video["vistas"], video["fecha_publicacion"])
                tendencias_detectadas.append({
                    "tema_base": termino,
                    "titulo_competidor": video["titulo"],
                    "vph": vph,
                    "vistas_totales": video["vistas"]
                })

        # Ordenar por VPH (mayor tracción primero)
        tendencias_detectadas.sort(key=lambda x: x["vph"], reverse=True)

        # Excluir las que ya se usaron (anti-repetición): si el título real del
        # competidor ya inspiró un tema antes, lo saltamos.
        def _ya_usado(t):
            titulo = t["titulo_competidor"].lower().strip()
            return any(u and (u in titulo or titulo in u) for u in temas_usados)

        frescas = [t for t in tendencias_detectadas if not _ya_usado(t)]
        candidatas = frescas if frescas else tendencias_detectadas  # si todas usadas, no bloquear

        if candidatas:
            # Elegir aleatoriamente entre el TOP 5 (no siempre el #1) para variar.
            import random as _random
            top = candidatas[:5]
            tendencia_ganadora = _random.choice(top)
            logging.info(f"[TREND ENGINE] Tema elegido: '{tendencia_ganadora['titulo_competidor'][:50]}' ({tendencia_ganadora['vph']:.2f} VPH) de top {len(top)}.")
            return tendencia_ganadora
        else:
            return None

    def inyectar_contexto_viral(self, marca, api_key=None, temas_usados=None):
        """
        Genera la 'Directriz de Tracción' final.
        Este es el texto que se le inyectará al ai_engine antes de generar el guion.
        Ahora ancla el guion al TÍTULO REAL del video que está explotando (no al
        término genérico), para que cada video sea sobre un tema ESPECÍFICO y distinto.
        """
        tendencia = self.escanear_traccion_competitiva(marca, api_key, temas_usados)
        if tendencia:
            titulo_real = tendencia['titulo_competidor']
            contexto_viral = (
                f"[DIRECTRIZ DE TRACCIÓN ALGORÍTMICA]: En tu nicho, este video está dominando el tráfico AHORA: "
                f"'{titulo_real}' ({int(tendencia.get('vistas_totales', 0)):,} vistas, {tendencia['vph']:.0f} vistas/hora). "
                f"Crea un guion sobre ESTE tema específico, NO sobre un concepto genérico. "
                f"Tu objetivo: un ángulo SUPERIOR y DISTINTO al de ese video, con un gancho más agresivo en los primeros 3 segundos, "
                f"para robar su audiencia. El tema debe ser concreto y específico como el del competidor, no vago."
            )
            return contexto_viral
        else:
            return "[DIRECTRIZ DE RETENCIÓN ESTÁNDAR]: Aplica un gancho de curiosidad extrema en el primer segundo y mantén un ritmo acelerado sin usar relleno."
