"""
PEXELS ENGINE v2.2 — Dark Factory Sistema Pinpinela
Motor de búsqueda inteligente de clips por canal, prompt y ADN visual.
Escalable para múltiples canales. (FIX: AMPUTACIÓN DE PEXELS PARA LA VIUDA)
"""

import os
import json
import random
import requests
import subprocess

HISTORIAL_PATH  = r"C:\NODO_PINPINELA\historial_clips.json"
PEXELS_API_URL  = "https://api.pexels.com/videos/search"
MAX_HISTORIAL   = 600
BLOQUEO_ULTIMOS = 200

ADN_CANALES = {
    "La Viuda": {
        "ratio_pexels": 0,  # ⚠️ CIRUGÍA ESTRICTA: Reducido a 0. Fuerza 100% Stable Diffusion.
        "orientacion_default": "portrait",
        "estilo_visual": "dark, moody, atmospheric, psychological horror, night",
        "keywords_base": [
            "dark empty room night",
            "dark hallway shadow",
            "foggy forest night",
            "old house night",
            "dark staircase",
            "empty street night fog",
            "dark window night",
            "creepy basement dark",
            "dark attic",
            "abandoned building night",
            "dark door shadow",
            "night forest fog",
        ],
        "keywords_prohibidas": [
            "people", "crowd", "sunny", "happy", "colorful", "beach",
            "hospital", "medical", "forensic", "crime", "police", "camera",
            "equipment", "device", "photography", "makeup", "smile", "laughing",
            "fruit", "food", "golf", "sports", "daylight", "bright"
        ],
        "filtro_duracion_min": 5,
        "filtro_duracion_max": 30,
        "filtro_sin_personas": True,
    },
    "Monkygraff": {
        "ratio_pexels": 50,
        "orientacion_default": "landscape",
        "estilo_visual": "tactical, geopolitical, industrial, military, infrastructure",
        "min_resultados": 15,
        "keywords_base": [
            "military base aerial",
            "industrial infrastructure",
            "cargo ship ocean",
            "control room empty",
            "radar station",
            "satellite dish",
            "oil refinery",
            "power plant",
            "pipeline industrial",
            "military vehicle",
            "port container ship",
            "aerial city night",
            "data center",
            "submarine base",
        ],
        "keywords_prohibidas": [
            "people", "crowd", "children", "party", "nature", "animals",
            "makeup", "beauty", "food", "fashion", "dance", "music",
            "art", "painting", "studio", "model", "woman", "man"
        ],
        "filtro_duracion_min": 25,
        "filtro_duracion_max": 60,
        "filtro_sin_personas": True,
    },
    "FiltradoMX": {
        "ratio_pexels": 40,
        "orientacion_default": "portrait",
        "estilo_visual": "intimate drama, warm candlelight, everyday objects, emotional atmosphere",
        "min_resultados": 15,
        "keywords_base": [
            "phone notification night",
            "coffee table intimate",
            "empty bedroom night lamp",
            "wedding ring table",
            "suitcase door",
            "candlelight shadow room",
            "wine glass table night",
            "door closing dramatic",
            "kitchen night lamp",
            "hallway warm light",
            "living room night intimate",
            "window rain night warm",
        ],
        "keywords_prohibidas": [
            "children", "child", "kids", "kid", "baby", "babies", "toddler",
            "niño", "niña", "infant", "minor", "teen", "teenager", "school",
            "playground", "toy", "toys", "cartoon", "animated",
            "people", "crowd", "group", "party", "outdoor", "sports",
            "office", "corporate", "business", "medical", "hospital"
        ],
        "filtro_duracion_min": 10,
        "filtro_duracion_max": 45,
        "filtro_sin_personas": True,
    },
    "LaesquinaRandom": {
        "ratio_pexels": 50,
        "orientacion_default": "portrait",
        "estilo_visual": "funny mexican street, colorful market, urban comedy",
        "keywords_base": [
            "mexican street market",
            "colorful urban mexico",
            "funny street scene",
            "mexican food market",
            "urban comedy street",
            "colorful building mexico",
        ],
        "keywords_prohibidas": [
            "children", "child", "kids", "baby", "minor", "teen", "school",
            "people", "crowd", "violence", "dark", "horror", "medical"
        ],
        "filtro_duracion_min": 10,
        "filtro_duracion_max": 45,
        "filtro_sin_personas": True,
    },
}

ADN_DEFAULT = {
    "ratio_pexels": 40,
    "orientacion_default": "landscape",
    "estilo_visual": "cinematic, atmospheric",
    "keywords_base": ["cinematic landscape", "atmospheric nature", "urban cityscape"],
    "keywords_prohibidas": ["people", "crowd"],
    "filtro_duracion_min": 25,
    "filtro_duracion_max": 60,
    "filtro_sin_personas": False,
}

STOPWORDS = {
    "no","and","or","the","a","an","with","without","very","photography","style",
    "realistic","cinematic","footage","camera","quality","low","high","heavily",
    "grainy","people","persons","human","man","woman","detailed","lighting",
    "environment","photorealistic","hyperrealistic","dramatic","atmosphere","sharp",
    "focus","film","grain","uhd","macro","reuters","harsh","industrial","desaturated",
    "colors","highly","cctv","security","vhs","glitch","amateur","dashcam","disposable",
    "flash","underexposed","dirty","lens","found","based","8k","ultra","photojournalism",
    "from","into","this","that","they","them","their","there","where","when","what",
    "which","have","been","will","would","could","should","about","over","under",
    "after","before","during"
}


def _cargar_historial():
    if os.path.exists(HISTORIAL_PATH):
        try:
            with open(HISTORIAL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"clips_usados": []}
    return {"clips_usados": []}


def _guardar_historial(historial):
    os.makedirs(os.path.dirname(HISTORIAL_PATH), exist_ok=True)
    historial["clips_usados"] = historial["clips_usados"][-MAX_HISTORIAL:]
    with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)


def _clip_usado_recientemente(clip_id, historial):
    recientes = historial.get("clips_usados", [])[-BLOQUEO_ULTIMOS:]
    return str(clip_id) in [str(c) for c in recientes]


def _registrar_clip(clip_id, historial):
    historial.setdefault("clips_usados", [])
    historial["clips_usados"].append(str(clip_id))
    _guardar_historial(historial)


def _extraer_keywords_prompt(prompt_visual, adn, max_keywords=3):
    texto = prompt_visual.lower().replace(",", " ").replace(".", " ")

    ambientes_terror = [
        "forest", "woods", "basement", "attic", "staircase", "hallway",
        "bedroom", "kitchen", "bathroom", "window", "door", "street",
        "alley", "road", "house", "building", "room", "corridor",
        "cemetery", "church", "bridge", "tunnel", "warehouse", "garage",
        "lake", "river", "field", "path", "wall", "fence"
    ]
    ambientes_tactico = [
        "military", "industrial", "factory", "port", "harbor", "ship",
        "aircraft", "tank", "radar", "satellite", "refinery", "pipeline",
        "bridge", "highway", "city", "aerial", "drone", "facility",
        "base", "station", "power", "data", "control", "tower"
    ]

    palabras = texto.split()

    ambientes_ref = ambientes_terror if "dark" in texto or "night" in texto or "shadow" in texto else ambientes_tactico
    encontrados = [p for p in palabras if p in ambientes_ref]

    if encontrados:
        modificadores = [p for p in palabras if p in ["dark", "night", "foggy", "empty", "abandoned", "old", "aerial", "industrial"] and p not in STOPWORDS]
        query_partes = encontrados[:2] + modificadores[:2]
        if len(query_partes) >= 2:
            return " ".join(query_partes[:max_keywords])

    keywords = [
        p for p in palabras
        if len(p) > 4 and p not in STOPWORDS and p not in adn["keywords_prohibidas"]
    ]
    keywords.sort(key=len, reverse=True)
    if len(keywords) >= 2:
        return " ".join(keywords[:max_keywords])

    return random.choice(adn["keywords_base"])


def _tiene_personas(video):
    tags = [t.get("name", "").lower() for t in video.get("tags", [])]
    desc = video.get("url", "").lower()
    palabras_persona = [
        "person", "people", "woman", "man", "girl", "boy", "human", "face",
        "model", "portrait", "makeup", "smile", "happy", "couple", "friends",
        "group", "crowd", "kids", "children", "baby", "lifestyle"
    ]
    # Palabras de niños — bloqueo absoluto para todos los canales
    palabras_ninos = [
        "child", "children", "kid", "kids", "baby", "babies", "toddler",
        "infant", "minor", "teen", "teenager", "school", "playground", "toy"
    ]
    tiene_persona = any(p in tags or p in desc for p in palabras_persona)
    tiene_nino    = any(p in tags or p in desc for p in palabras_ninos)
    return tiene_persona or tiene_nino


def _buscar_en_pexels(query, orientacion, adn, api_key, historial, pagina=1, exigir_relevancia=True):
    headers = {"Authorization": api_key}
    params  = {
        "query": query, "orientation": orientacion,
        "size": "medium", "per_page": 80, "page": pagina, "locale": "en-US"
    }
    try:
        res = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=30)
        if res.status_code != 200:
            return None
        videos = res.json().get("videos", [])
        total_resultados = res.json().get("total_results", 0)
        if not videos:
            return None

        # RELEVANCIA: si Pexels tiene muy pocos resultados para esta query,
        # significa que no tiene nada bueno → no descargar basura, mandar a SD
        min_req = adn.get("min_resultados", 8)
        if exigir_relevancia and total_resultados < min_req:
            print(f"   [PEXELS] Solo {total_resultados} resultados para '{query}' (min {min_req}) — poco relevante, descarto.")
            return None

        dur_min = adn.get("filtro_duracion_min", 25)
        dur_max = adn.get("filtro_duracion_max", 60)
        filtrar_personas = adn.get("filtro_sin_personas", False)

        if filtrar_personas:
            videos = [v for v in videos if not _tiene_personas(v)]

        no_usados = [v for v in videos if not _clip_usado_recientemente(v["id"], historial)]
        todos     = videos

        disponibles = [v for v in no_usados if dur_min <= v.get("duration", 0) <= dur_max]
        if not disponibles:
            # Intentar página 2 y 3 antes de reusar clips ya vistos
            if pagina < 3:
                print(f"   [PEXELS] Página {pagina} agotada — buscando página {pagina + 1}...")
                return _buscar_en_pexels(query, orientacion, adn, api_key, historial, pagina + 1, exigir_relevancia)
            # Último recurso: reusar clips (se repite lo menos posible)
            disponibles = [v for v in todos if dur_min <= v.get("duration", 0) <= dur_max]
        if not disponibles:
            return None
        # Pexels ordena por relevancia; tomar de los primeros (más relacionados)
        return random.choice(disponibles[:4])
    except Exception as e:
        print(f"   [PEXELS] Error busqueda '{query}' pág {pagina}: {e}")
        return None


def _descargar_clip(video, orientacion, carpeta_destino, nombre_archivo, w, h):
    archivos = video.get("video_files", [])
    if orientacion == "portrait":
        filtrados = [a for a in archivos if a.get("width", 1) < a.get("height", 0)]
    else:
        filtrados = [a for a in archivos if a.get("width", 0) >= a.get("height", 1)]
    if not filtrados:
        filtrados = archivos
    filtrados.sort(key=lambda a: a.get("width", 0) * a.get("height", 0), reverse=True)
    url_clip = filtrados[0].get("link", "") if filtrados else ""
    if not url_clip:
        return False

    clip_id  = video["id"]
    ruta_raw = os.path.join(carpeta_destino, f"_pex_raw_{clip_id}.mp4")
    ruta_out = os.path.join(carpeta_destino, nombre_archivo)
    try:
        with requests.get(url_clip, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(ruta_raw, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        cmd = [
            "ffmpeg", "-y", "-i", ruta_raw,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-an", "-pix_fmt", "yuv420p", ruta_out
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(ruta_raw):
            os.remove(ruta_raw)
        return os.path.exists(ruta_out)
    except Exception as e:
        print(f"   [PEXELS] Error descarga: {e}")
        if os.path.exists(ruta_raw):
            os.remove(ruta_raw)
        return False


def buscar_clip_pexels(prompt_visual, marca, formato, api_key, carpeta_destino, nombre_archivo, pexels_query=None):
    if not api_key:
        print("   [PEXELS] Sin API key — SD fallback.")
        return False

    adn         = ADN_CANALES.get(marca, ADN_DEFAULT)
    orientacion = "landscape" if "16:9" in formato else "portrait"
    w, h        = (1024, 576) if orientacion == "landscape" else (576, 1024)
    historial   = _cargar_historial()

    intentos_crudos = []
    if pexels_query and len(pexels_query.strip()) > 3:
        print(f"   [PEXELS] Query de Gemini: '{pexels_query.strip()}'")
        # Intentos RELEVANTES (específicos de la escena) — exigen relevancia
        intentos_crudos = [
            (pexels_query.strip(), True),
            (_extraer_keywords_prompt(prompt_visual, adn), True),
        ]
    else:
        intentos_crudos = [
            (_extraer_keywords_prompt(prompt_visual, adn), True),
        ]

    # Intento genérico de keywords_base SIN exigir relevancia (último recurso)
    intentos_crudos.append((random.choice(adn["keywords_base"]), False))

    # Deduplicar conservando el flag de relevancia
    vistos = set()
    intentos_base = []
    for q, rel in intentos_crudos:
        if q and q not in vistos:
            vistos.add(q)
            intentos_base.append((q, rel))

    intentos = []
    if marca.lower() in ["la viuda", "laviuda"]:
        for q, rel in intentos_base:
            q_lower = q.lower()
            if not any(word in q_lower for word in ["dark", "creepy", "scary", "horror", "night", "shadow"]):
                intentos.append((f"{q} dark", rel))
                intentos.append((f"{q} creepy", rel))
            else:
                intentos.append((q, rel))
        # Deduplicar
        vistos2 = set()
        dedup = []
        for q, rel in intentos:
            if q not in vistos2:
                vistos2.add(q)
                dedup.append((q, rel))
        intentos = dedup
    else:
        intentos = intentos_base

    for query, exigir_rel in intentos:
        print(f"   [PEXELS] Buscando: '{query}' ({orientacion}) [relevancia={'sí' if exigir_rel else 'no'}]...")
        video = _buscar_en_pexels(query, orientacion, adn, api_key, historial, exigir_relevancia=exigir_rel)
        if video:
            clip_id = video["id"]
            print(f"   [PEXELS] Clip ID {clip_id} encontrado — descargando...")
            ok = _descargar_clip(video, orientacion, carpeta_destino, nombre_archivo, w, h)
            if ok:
                _registrar_clip(clip_id, historial)
                print(f"   [PEXELS] Clip listo.")
                return True
            print(f"   [PEXELS] Fallo descarga — siguiente intento...")

    print("   [PEXELS] Sin resultados relevantes — SD fallback.")
    return False


def usar_pexels(marca):
    adn   = ADN_CANALES.get(marca, ADN_DEFAULT)
    ratio = adn.get("ratio_pexels", 40)
    return random.randint(1, 100) <= ratio