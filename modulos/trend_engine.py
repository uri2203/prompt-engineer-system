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
                "terror psicologico narrado",
                "historias de miedo extremo",
                "paranoia perturbadora",
                "experiencias paranormales reales"
            ],
            "Monkygraff": [
                "guerra Ucrania Rusia 2026",
                "guerra comercial China Trump aranceles",
                "minerales criticos litio cobalto geopolitica",
                "inteligencia artificial geopolitica poder"
            ]
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
            # Solo videos publicados en los últimos 7 días (tendencia fresca)
            hace_semana = (datetime.now(_tz.utc) - timedelta(days=7)).isoformat()
            # 1. Buscar videos recientes del término
            r = _rq.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "key": api_key, "q": query, "part": "snippet",
                    "type": "video", "order": "viewCount",
                    "publishedAfter": hace_semana, "maxResults": 10,
                    "relevanceLanguage": "es", "regionCode": "MX",
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
        en caso de que la cuota de la API se agote.
        """
        fecha_reciente = datetime.now(timezone.utc).isoformat()
        return [
            {"titulo": f"El secreto oculto de {query}", "vistas": 150000, "fecha_publicacion": fecha_reciente, "canal": "Competidor Alpha"},
            {"titulo": f"La verdad clasificada sobre {query}", "vistas": 85000, "fecha_publicacion": fecha_reciente, "canal": "Competidor Beta"}
        ]

    def escanear_traccion_competitiva(self, marca, api_key=None):
        """
        Punto de entrada principal del silo.
        Ejecuta el ciclo de combate y retorna la tendencia con mayor tracción algorítmica.
        """
        logging.info(f"[TREND ENGINE] Iniciando radar de tracción para: {marca}")
        
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

        # Ordenar el arreglo colocando el VPH más alto en la posición [0]
        tendencias_detectadas.sort(key=lambda x: x["vph"], reverse=True)
        
        if tendencias_detectadas:
            tendencia_ganadora = tendencias_detectadas[0]
            logging.info(f"[TREND ENGINE] Blanco fijado: '{tendencia_ganadora['tema_base']}' corriendo a {tendencia_ganadora['vph']:.2f} VPH.")
            return tendencia_ganadora
        else:
            return None

    def inyectar_contexto_viral(self, marca, api_key=None):
        """
        Genera la 'Directriz de Tracción' final. 
        Este es el texto que se le inyectará al ai_engine antes de generar el guion.
        """
        tendencia = self.escanear_traccion_competitiva(marca, api_key)
        if tendencia:
            contexto_viral = (
                f"[DIRECTRIZ DE TRACCIÓN ALGORÍTMICA]: Un competidor está dominando el tráfico actual con el título '{tendencia['titulo_competidor']}'. "
                f"El tema de alta retención es '{tendencia['tema_base']}'. "
                f"Tu objetivo estricto es crear un guion superior, con un gancho más agresivo en los primeros 3 segundos sobre este mismo tema para robar su audiencia."
            )
            return contexto_viral
        else:
            return "[DIRECTRIZ DE RETENCIÓN ESTÁNDAR]: Aplica un gancho de curiosidad extrema en el primer segundo y mantén un ritmo acelerado sin usar relleno."
