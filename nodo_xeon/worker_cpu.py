import sys
# FIX UTF-8: evita que los emojis (⚡🚀🎬) rompan el worker al escribir a archivo/log
# en Windows (cp1252). Reconfigura la salida a UTF-8 con reemplazo seguro.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import requests
import time
import os
import json
import base64
import subprocess
import random
import uuid
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False
    print("⚠️ Pillow no instalado — ejecuta: pip install Pillow")

# 🚀 CONFIGURACIÓN CORPORATE TECH V8.4.8 - MOTOR HÍBRIDO (FIX: BLOQUEO ANTI-BUCLE)
PEXELS_API_KEY_LOCAL = "jkdA4ukl8lt61jzm39P5D6tmNzYDHtQMlk8kwEe7mUhPB4jbWtw552an"

IP_GRAFICA_1 = "192.168.0.215"
IP_GRAFICA_2 = "192.168.0.215"
IP_GRAFICA   = IP_GRAFICA_1
RENDER_URL   = "https://prompt-engineer-system-l2r6.onrender.com"
CARPETA_LOCAL  = "C:\\DarkFactory_Renders"
CARPETA_ASSETS = "C:\\DarkFactory_ASSETS"

VOLUMEN_MUSICA = "0.15"

# ══════════════════════════════════════════════════════════════
# DEPTHFLOW — Parallax 2.5D (corre en el PC GPU, puerto 8500)
# ══════════════════════════════════════════════════════════════
DEPTHFLOW_URL = f"http://{IP_GRAFICA}:8500"
# Porcentaje de escenas que reciben parallax real (el resto usa zoompan).
# Variado para todos los canales. Se mezclan los dos para dinamismo + velocidad.
DEPTHFLOW_RATIO = 45  # 45% de las escenas con parallax, 55% zoompan

# ── Nodos críticos para el pre-flight check ──────────────────────────────────
IP_VOZ_LOCAL = "192.168.0.251"   # motor_voz.py / XTTS
URL_NODO_SD   = f"http://{IP_GRAFICA}:7861"      # Stable Diffusion
URL_NODO_VOZ  = f"http://{IP_VOZ_LOCAL}:8000"    # Motor de voz

# ── DIAGNÓSTICO: el worker sube un reporte por video a la rama diagnostico ────
# Así se puede revisar de forma remota qué pasó con cada video (hooks, subtítulos,
# paquete, errores) sin tener que copiar el log de la terminal.
_GH_REPO = "uri2203/prompt-engineer-system"
_GH_TOKEN_PATH = r"C:\NODO_PINPINELA\token_github.txt"

def _leer_token_github():
    try:
        with open(_GH_TOKEN_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

def subir_diagnostico_video(diag):
    """Sube un JSON de diagnóstico de UN video a _diagnostico/videos/ en la rama
    diagnostico. No interrumpe la producción si falla (best-effort)."""
    try:
        token = _leer_token_github()
        if not token:
            return False
        vid_id = str(diag.get("id", "sin_id"))[:20].replace("/", "_")
        ts = time.strftime("%Y%m%d_%H%M%S")
        ruta = f"_diagnostico/videos/{ts}_{diag.get('marca','?')}_{vid_id}.json"
        contenido = base64.b64encode(json.dumps(diag, ensure_ascii=False, indent=2).encode()).decode()
        H = {"Authorization": f"token {token}"}
        # No hace falta SHA: cada archivo es nuevo (timestamp único)
        r = requests.put(
            f"https://api.github.com/repos/{_GH_REPO}/contents/{ruta}",
            headers=H,
            json={"message": f"diag video {diag.get('marca','?')} {vid_id}",
                  "content": contenido, "branch": "diagnostico"},
            timeout=30,
        )
        if r.status_code in (200, 201):
            print(f"   [DIAG] Reporte del video subido a diagnostico/videos/")
            return True
        return False
    except Exception as e:
        print(f"   [DIAG] No se pudo subir el diagnóstico (no crítico): {e}")
        return False

def _ping_nodo(url, nombre, timeout=8):
    """Verifica si un nodo HTTP responde. Devuelve True/False."""
    try:
        r = requests.get(url, timeout=timeout)
        # Cualquier respuesta HTTP (incluso 404) significa que el servicio está vivo
        return True
    except Exception:
        return False

def verificar_nodos_criticos(necesita_sd=True, necesita_voz=True):
    """Pre-flight check: verifica que los nodos críticos estén vivos ANTES de
    empezar a generar. Si falta uno crítico, devuelve (False, mensaje) para abortar
    y NO desperdiciar horas de trabajo. DepthFlow NO es crítico (cae a zoompan)."""
    print("🔎 [PRE-FLIGHT] Verificando nodos antes de empezar...")
    problemas = []

    if necesita_sd:
        # SD responde en /sdapi/v1/sd-models o en la raíz
        sd_ok = _ping_nodo(f"{URL_NODO_SD}/sdapi/v1/options", "SD") or _ping_nodo(URL_NODO_SD, "SD")
        print(f"   {'🟢' if sd_ok else '🔴'} Nodo IMÁGENES (SD {URL_NODO_SD})")
        if not sd_ok:
            problemas.append(f"Nodo de IMÁGENES (SD) no responde en {URL_NODO_SD}")

    if necesita_voz:
        voz_ok = _ping_nodo(URL_NODO_VOZ, "VOZ")
        print(f"   {'🟢' if voz_ok else '🔴'} Nodo VOZ ({URL_NODO_VOZ})")
        if not voz_ok:
            problemas.append(f"Nodo de VOZ no responde en {URL_NODO_VOZ}")

    # DepthFlow: informativo, no crítico
    df_ok = _ping_nodo(f"{DEPTHFLOW_URL}/health", "DepthFlow")
    print(f"   {'🟢' if df_ok else '🟡'} Nodo PARALLAX (DepthFlow {DEPTHFLOW_URL}) {'' if df_ok else '— usará zoompan'}")

    if problemas:
        print("❌ [PRE-FLIGHT] ABORTADO — nodos críticos caídos:")
        for p in problemas:
            print(f"      • {p}")
        print("   No se generará nada para no desperdiciar tiempo. Activa los nodos y reintenta.")
        return False, " | ".join(problemas)

    print("✅ [PRE-FLIGHT] Todos los nodos críticos activos. Procediendo.")
    return True, "ok"

_depthflow_vivo = None  # cache del estado del servidor (None=sin verificar)

def _liberar_vram_sd():
    """NEUTRALIZADA: descargar el modelo de SD de la VRAM movía el modelo (varios GB)
    entre VRAM y RAM del sistema, saturando la RAM (subía a 20 GB) y colgando el equipo.
    Ahora el modelo se queda SIEMPRE cargado y quieto. SD estable, RAM ~1 GB."""
    return False

def _recargar_sd():
    """NEUTRALIZADA: ya no se descarga el modelo, así que no hay que recargarlo."""
    return True

def _asegurar_sd_cargado():
    """Solo verifica que SD responda (ping ligero). NO toca el modelo ni la VRAM."""
    try:
        requests.get(f"{URL_NODO_SD}/sdapi/v1/options", timeout=15)
    except Exception:
        pass
    return True

def _depthflow_disponible():
    """Verifica una sola vez si el servidor DepthFlow del PC GPU está vivo."""
    global _depthflow_vivo
    if _depthflow_vivo is not None:
        return _depthflow_vivo
    try:
        r = requests.get(f"{DEPTHFLOW_URL}/health", timeout=5)
        _depthflow_vivo = (r.status_code == 200 and r.json().get("depthflow", False))
    except Exception:
        _depthflow_vivo = False
    print(f"   [DEPTHFLOW] Servidor {'DISPONIBLE' if _depthflow_vivo else 'no disponible (usando zoompan)'}")
    return _depthflow_vivo

def _pedir_parallax(path_img, path_salida, marca, escena_idx, duracion, fps, w, h):
    """Manda una imagen al servidor DepthFlow y guarda el clip parallax resultante.
    Devuelve True si tuvo éxito, False si hay que caer a zoompan."""
    try:
        with open(path_img, "rb") as f:
            archivos = {"imagen": f}
            datos = {
                "marca": marca, "escena_idx": str(escena_idx),
                "duracion": str(duracion), "fps": str(fps),
                "width": str(w), "height": str(h),
            }
            r = requests.post(f"{DEPTHFLOW_URL}/parallax",
                              files=archivos, data=datos, timeout=600)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(path_salida, "wb") as fo:
                fo.write(r.content)
            preset = r.headers.get("X-Preset", "?")
            print(f"   [DEPTHFLOW] escena {escena_idx} → parallax '{preset}' OK")
            return True
        print(f"   [DEPTHFLOW] escena {escena_idx} falló ({r.status_code}) — zoompan fallback")
        return False
    except Exception as e:
        print(f"   [DEPTHFLOW] escena {escena_idx} error: {str(e)[:80]} — zoompan fallback")
        return False


# ══════════════════════════════════════════════════════════════
# QUEMADOR DE TÍTULO EN MINIATURAS — CTR EXTREMO V1.0
# ══════════════════════════════════════════════════════════════
ADN_TEXTO_MINIATURAS = {
    "la viuda":   {"fuente_size": 95, "color_texto": (255,255,255), "color_sombra": (180,0,0),   "color_barra": (0,0,0,210),    "sombra_offset": 5, "mayusculas": True, "linea_acento": (180,0,0)},
    "monkygraff": {"fuente_size": 90, "color_texto": (255,255,255), "color_sombra": (220,100,0), "color_barra": (0,10,30,220),  "sombra_offset": 4, "mayusculas": True, "linea_acento": (220,100,0)},
    "default":    {"fuente_size": 88, "color_texto": (255,255,255), "color_sombra": (0,0,0),     "color_barra": (0,0,0,200),    "sombra_offset": 4, "mayusculas": True, "linea_acento": (255,200,0)},
}
FUENTES_WINDOWS = ["C:\\Windows\\Fonts\\impact.ttf","C:\\Windows\\Fonts\\ariblk.ttf","C:\\Windows\\Fonts\\arialbd.ttf","C:\\Windows\\Fonts\\verdanab.ttf"]

def _quemar_titulo_miniatura(ruta_imagen, titulo, marca):
    if not PIL_DISPONIBLE or not titulo or not os.path.exists(ruta_imagen):
        return
    try:
        marca_key = "default"
        for key in ADN_TEXTO_MINIATURAS:
            if key in marca.lower(): marca_key = key; break
        adn = ADN_TEXTO_MINIATURAS[marca_key]
        img = Image.open(ruta_imagen).convert("RGBA")
        w, h = img.size
        stopwords = {"DE","DEL","LA","EL","LOS","LAS","UN","UNA","Y","O","EN","A","CON","POR","QUE","SE","SU","AL"}
        palabras = titulo.upper().split() if adn["mayusculas"] else titulo.split()
        palabras_clave = [p for p in palabras if p not in stopwords][:7]
        texto_display = " ".join(palabras_clave)
        words = texto_display.split()
        lineas = [" ".join(words[:len(words)//2]), " ".join(words[len(words)//2:])] if len(words) > 4 else [texto_display]
        font = None
        for ruta_fuente in FUENTES_WINDOWS:
            if os.path.exists(ruta_fuente):
                try: font = ImageFont.truetype(ruta_fuente, adn["fuente_size"]); break
                except: continue
        if not font: font = ImageFont.load_default()
        alto_linea = adn["fuente_size"] + 14
        alto_bloque = alto_linea * len(lineas) + 40
        y_barra = h - alto_bloque - 30
        overlay = Image.new("RGBA", img.size, (0,0,0,0))
        ImageDraw.Draw(overlay).rectangle([(0, y_barra-10),(w, y_barra+alto_bloque+10)], fill=adn["color_barra"])
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, y_barra-10),(w, y_barra-4)], fill=adn["linea_acento"])
        for idx, linea in enumerate(lineas):
            bbox = draw.textbbox((0,0), linea, font=font)
            x = (w - (bbox[2]-bbox[0])) // 2
            y = y_barra + 12 + idx * alto_linea
            off = adn["sombra_offset"]
            for dx,dy in [(off,off),(-off,off),(0,off*2)]:
                draw.text((x+dx, y+dy), linea, font=font, fill=adn["color_sombra"])
            draw.text((x, y), linea, font=font, fill=adn["color_texto"])
        img.convert("RGB").save(ruta_imagen, "PNG", quality=98)
        print(f"   [MINIATURA CTR] Título quemado: '{texto_display}'")
    except Exception as e:
        print(f"   [MINIATURA CTR] Error: {e}")


# ══════════════════════════════════════════════════════════════
# SISTEMA DE MÚSICA DINÁMICA — ALTERNANCIA + TENSIÓN V1.0
# ══════════════════════════════════════════════════════════════
HISTORIAL_MUSICA_PATH = "C:\\NODO_PINPINELA\\historial_musica.json"

def _cargar_historial_musica():
    if os.path.exists(HISTORIAL_MUSICA_PATH):
        try:
            with open(HISTORIAL_MUSICA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def _guardar_historial_musica(historial):
    with open(HISTORIAL_MUSICA_PATH, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)

def _elegir_musica_fondo(carpeta_marca, marca):
    pistas = [f"musica_fondo{i}.mp3" for i in range(1, 5)]
    disponibles = [p for p in pistas if os.path.exists(os.path.join(carpeta_marca, p))]
    if not disponibles:
        return None
    historial = _cargar_historial_musica()
    ultima = historial.get(marca, {}).get("ultimo_fondo", "")
    candidatas = [p for p in disponibles if p != ultima]
    if not candidatas:
        candidatas = disponibles
    elegida = random.choice(candidatas)
    historial.setdefault(marca, {})["ultimo_fondo"] = elegida
    _guardar_historial_musica(historial)
    print(f"   [MUSICA] Fondo: {elegida} (anterior: {ultima or 'ninguno'})")
    return os.path.join(carpeta_marca, elegida)

def _elegir_musica_tension(carpeta_marca, marca):
    pistas = [f"musica_tension{i}.mp3" for i in range(1, 3)]
    disponibles = [p for p in pistas if os.path.exists(os.path.join(carpeta_marca, p))]
    if not disponibles:
        return None
    historial = _cargar_historial_musica()
    ultima = historial.get(marca, {}).get("ultima_tension", "")
    candidatas = [p for p in disponibles if p != ultima]
    if not candidatas:
        candidatas = disponibles
    elegida = random.choice(candidatas)
    historial.setdefault(marca, {})["ultima_tension"] = elegida
    _guardar_historial_musica(historial)
    print(f"   [MUSICA] Tension: {elegida}")
    return os.path.join(carpeta_marca, elegida)

def _mezclar_musica_dinamica(ruta_video, carpeta_marca, marca, duracion_total):
    ruta_fondo   = _elegir_musica_fondo(carpeta_marca, marca)
    ruta_tension = _elegir_musica_tension(carpeta_marca, marca)
    if not ruta_fondo:
        print(f"   [MUSICA] Sin pistas para {marca}.")
        return ruta_video
    # Verificar si el video de entrada tiene pista de audio (la narración).
    # Si NO la tiene (bug previo), el amix con [0:a] fallaría y quedaría mudo.
    _video_tiene_audio = False
    try:
        _chk = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a',
             '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', ruta_video],
            capture_output=True, text=True)
        _video_tiene_audio = 'audio' in _chk.stdout
    except Exception:
        pass
    if not _video_tiene_audio:
        print(f"   [⚠️ MUSICA] El video NO tiene narración — el problema es anterior. Omito mezcla para no romper.")
        return ruta_video
    carpeta_temp  = os.path.dirname(ruta_video)
    ruta_salida   = os.path.join(carpeta_temp, "paso2_musica.mp4")
    # Shorts (<= 90s): tensión al 40% — activa atención en escalada
    # Largos (> 90s):  tensión al 60% — punto de giro natural
    es_short = duracion_total <= 90
    punto_tension = duracion_total * (0.40 if es_short else 0.60)
    crossfade_dur = 1.5 if es_short else 3.0
    print(f"   [MUSICA] {'SHORT' if es_short else 'LARGO'} — tension al {int(punto_tension)}s de {int(duracion_total)}s")
    if ruta_tension and os.path.exists(ruta_tension):
        print(f"   [MUSICA] Fondo hasta {punto_tension:.1f}s -> tension con crossfade {crossfade_dur}s")
        filter_complex = (
            f"[1:a]volume={VOLUMEN_MUSICA},aloop=loop=-1:size=2e+09[bg];"
            f"[2:a]volume={VOLUMEN_MUSICA},aloop=loop=-1:size=2e+09[ten];"
            f"[bg]atrim=0:{punto_tension + crossfade_dur},asetpts=PTS-STARTPTS[bg_trim];"
            f"[ten]atrim=0:{duracion_total - punto_tension + crossfade_dur},asetpts=PTS-STARTPTS[ten_trim];"
            f"[bg_trim][ten_trim]acrossfade=d={crossfade_dur}:c1=exp:c2=exp[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd = [
            'ffmpeg', '-y',
            '-i', ruta_video.replace("\\", "/"),
            '-stream_loop', '-1', '-i', ruta_fondo.replace("\\", "/"),
            '-stream_loop', '-1', '-i', ruta_tension.replace("\\", "/"),
            '-filter_complex', filter_complex,
            '-map', '0:v', '-map', '[aout]',
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', ruta_salida
        ]
    else:
        cmd = [
            'ffmpeg', '-y',
            '-i', ruta_video.replace("\\", "/"),
            '-stream_loop', '-1', '-i', ruta_fondo.replace("\\", "/"),
            '-filter_complex', f"[1:a]volume={VOLUMEN_MUSICA}[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
            '-map', '0:v', '-map', '[aout]',
            '-c:v', 'copy', '-c:a', 'aac', ruta_salida
        ]
    resultado = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if resultado.returncode == 0 and os.path.exists(ruta_salida):
        try: os.remove(ruta_video)
        except: pass
        return ruta_salida
    print("   [MUSICA] Error mezclando — video sin musica de fondo")
    return ruta_video

# ── ALTERNANCIA INTELIGENTE PEXELS/SD ────────────────────────
PALABRAS_FISICAS    = {"military","industrial","port","harbor","ship","factory","pipeline","city","aerial","drone","facility","base","station","tower","bridge","highway","infrastructure","satellite","refinery","mine","tunnel","warehouse","building","road","forest","ocean","field","mountain","dark","room","hallway","door","window","street","alley","house","basement","staircase","corridor","cemetery","church","fog","night"}
PALABRAS_ABSTRACTAS = {"control","power","domination","strategy","concept","symbol","idea","system","network","digital","virtual","data","map","global","world","shadow","silhouette","force","energy","influence","geopolitical","monopoly","secret","hidden","classified","operation","plan","fear"}


os.environ['no_proxy'] = f'{IP_GRAFICA_1},{IP_GRAFICA_2},localhost,127.0.0.1,render.com'

for _carpeta in [CARPETA_LOCAL, CARPETA_ASSETS]:
    if not os.path.exists(_carpeta):
        os.makedirs(_carpeta)

# ══════════════════════════════════════════════════════════════
# VELOCIDAD DE LOCUCIÓN POR CANAL (palabras por minuto reales)
# ══════════════════════════════════════════════════════════════
VELOCIDAD_PPM = {
    "la viuda":         85,
    "monkygraff":       140,
    "filtradmx":        130,
    "filtrado mx":      130,
    "laesquinarandom":  155,
    "laesquina random": 155,
    "tuialista":        140,
    "umbral alterno":   115,
    "umbralalterno":    115,
    "default":          120,
}

PAUSA_PUNTUACION = {
    ".":  0.55,   
    "…":  0.70,   
    "...": 0.70,  
    ",":  0.20,   
    ";":  0.30,   
    "!":  0.40,   
    "?":  0.40,   
    ":":  0.25,   
}

# ── CIRCUIT BREAKER & MEMORIA ANTI-BUCLE ────────────────────
_errores_render     = 0
_MAX_ERRORES_RENDER = 5
_PAUSA_EMERGENCIA   = 300
_ultimo_error_429   = 0

_tareas_completadas = set()  # <-- FIX: Memoria para no repetir tareas
_worker_tomo_tarea = [False]  # control para reportar libre/ocupado (lista = mutable global)

def _registrar_error_render():
    global _errores_render
    _errores_render += 1
    if _errores_render >= _MAX_ERRORES_RENDER:
        print(f"[CIRCUIT BREAKER] {_errores_render} errores consecutivos. Pausando {_PAUSA_EMERGENCIA}s...")
        time.sleep(_PAUSA_EMERGENCIA)
        _errores_render = 0

def _resetear_errores_render():
    global _errores_render
    _errores_render = 0

# ══════════════════════════════════════════════════════════════
# MOTORES MATEMÁTICOS Y LECTURA DE TIEMPO
# ══════════════════════════════════════════════════════════════

def _obtener_velocidad_canal(marca):
    marca_lower = marca.lower().replace(" ", "")
    for canal, ppm in VELOCIDAD_PPM.items():
        if canal.replace(" ", "") in marca_lower or marca_lower in canal.replace(" ", ""):
            return ppm
    return VELOCIDAD_PPM["default"]

def _obtener_duracion_audio(ruta_audio, texto_locucion, marca_audio):
    try:
        ruta_safe = ruta_audio.replace("\\", "/")
        cmd_dur = [
            'ffprobe', '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            ruta_safe
        ]
        dur_str = subprocess.check_output(cmd_dur, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        duracion_real = float(dur_str)
        if duracion_real < 5.0:
            raise ValueError("Duración leída demasiado corta (posible corrupción).")
        print(f"   [SYNC] FFprobe leyó duración exacta: {duracion_real:.2f}s")
        return duracion_real
    except Exception as e:
        num_palabras = len(texto_locucion.split())
        ppm = _obtener_velocidad_canal(marca_audio)
        dur_estimada = (num_palabras / ppm) * 60.0
        print(f"   [⚠️ ALERTA CRÍTICA] FFprobe falló. Usando Motor Matemático: {dur_estimada:.2f}s")
        return dur_estimada

def _generar_srt_calibrado(texto_completo, dur_total_audio, marca, ruta_srt):
    """
    Distribución lineal pura por palabra — sin pausas teóricas, sin drift.
    Cada palabra recibe exactamente dur_total_audio / total_palabras segundos.
    El audio RVC no respeta pausas teóricas, entonces no las calculamos.
    """
    import re

    # Chunks según velocidad del canal
    ppm = _obtener_velocidad_canal(marca)
    palabras_por_chunk = 4 if ppm <= 90 else (5 if ppm <= 130 else 6)

    # Dividir en oraciones → chunks de N palabras
    frases_raw = re.split(r'(?<=[.!?…])\s+', texto_completo.strip())
    frases_raw = [f.strip() for f in frases_raw if f.strip()]

    chunks = []
    for frase in frases_raw:
        palabras = frase.split()
        if len(palabras) <= palabras_por_chunk:
            chunks.append(frase)
        else:
            for j in range(0, len(palabras), palabras_por_chunk):
                parte = " ".join(palabras[j:j+palabras_por_chunk])
                if parte.strip():
                    chunks.append(parte)
    if not chunks:
        return

    # DISTRIBUCIÓN LINEAL PURA: tiempo proporcional a palabras, sin correcciones
    # Esto elimina el drift acumulado porque no hay factores que se desvíen
    total_palabras = sum(len(c.split()) for c in chunks)
    if total_palabras == 0:
        return

    seg_por_palabra = dur_total_audio / total_palabras

    tiempo = 0.0
    total  = len(chunks)
    with open(ruta_srt, "w", encoding="utf-8") as srt:
        for idx, chunk in enumerate(chunks):
            n_palabras = len(chunk.split())
            dur        = n_palabras * seg_por_palabra
            ini        = tiempo
            fin_t      = dur_total_audio if idx == total - 1 else tiempo + dur

            if ini >= fin_t:
                continue

            h_i,m_i = int(ini//3600),int((ini%3600)//60)
            s_i,ms_i = int(ini%60),int((ini%1)*1000)
            h_f,m_f = int(fin_t//3600),int((fin_t%3600)//60)
            s_f,ms_f = int(fin_t%60),int((fin_t%1)*1000)
            srt.write(
                f"{idx+1}\n"
                f"{h_i:02d}:{m_i:02d}:{s_i:02d},{ms_i:03d} --> "
                f"{h_f:02d}:{m_f:02d}:{s_f:02d},{ms_f:03d}\n"
                f"{chunk.upper()}\n\n"
            )
            tiempo += dur

def _detectar_silencios(ruta_audio, umbral_db=-30, dur_min_silencio=0.35):
    """Detecta los silencios reales del audio (pausas del locutor) con ffmpeg.
    Devuelve lista de tiempos (segundos) donde TERMINA cada silencio = inicio de habla."""
    try:
        r = subprocess.run(
            ['ffmpeg', '-i', ruta_audio, '-af',
             f'silencedetect=noise={umbral_db}dB:d={dur_min_silencio}',
             '-f', 'null', '-'],
            capture_output=True, text=True
        )
        import re
        # silencedetect imprime "silence_end: X" en stderr
        fines = re.findall(r'silence_end:\s*([\d.]+)', r.stderr)
        return [float(f) for f in fines]
    except Exception as e:
        print(f"   [SUBS] No se pudieron detectar silencios: {e}")
        return []


# ── CONFIGURACIÓN DE SUBTÍTULOS POR CANAL ────────────────────────────────────
# Cada canal tiene distinto ritmo de voz. Para AJUSTAR un canal, cambia SUS números:
#
#   dur_min_silencio = cuánto debe durar una pausa para contar como frontera entre
#                      bloques. Voz RÁPIDA necesita pausas más largas para no
#                      fragmentar; voz LENTA usa pausas cortas (detección fina).
#   fusionar_bloques_min = si un bloque dura menos que esto, se fusiona con el
#                      siguiente (evita micro-bloques que desincronizan).
#   max_palabras     = palabras máximas por línea de subtítulo (ritmo de lectura).
#   offset_seg       = DESFASE en segundos. Es el ajuste fino de sincronía:
#                      • Si los subtítulos van ATRASADOS (el texto llega tarde) →
#                        usa un valor NEGATIVO (ej. -0.3) para ADELANTARLOS.
#                      • Si van ADELANTADOS (el texto aparece antes que la voz) →
#                        usa un valor POSITIVO (ej. 0.3) para ATRASARLOS.
#                      • Si están bien → déjalo en 0.0.
#                      Ajusta de a poco: 0.2-0.3s suele bastar. 1.0s es mucho.
SUBS_POR_CANAL = {
    "la viuda":          {"dur_min_silencio": 0.28, "fusionar_bloques_min": 0.8, "max_palabras": 4, "offset_seg": 0.0},
    "laviuda":           {"dur_min_silencio": 0.28, "fusionar_bloques_min": 0.8, "max_palabras": 4, "offset_seg": 0.0},
    "monkygraff":        {"dur_min_silencio": 0.38, "fusionar_bloques_min": 1.2, "max_palabras": 5, "offset_seg": 0.0},
    # FiltradoMX: subtítulos iban ATRASADOS → offset negativo para adelantarlos
    "filtradomx":        {"dur_min_silencio": 0.40, "fusionar_bloques_min": 1.3, "max_palabras": 5, "offset_seg": -0.35},
    "filtrado mx":       {"dur_min_silencio": 0.40, "fusionar_bloques_min": 1.3, "max_palabras": 5, "offset_seg": -0.35},
    # LaesquinaRandom: subtítulos iban ATRASADOS → offset negativo para adelantarlos
    "laesquinarandom":   {"dur_min_silencio": 0.50, "fusionar_bloques_min": 1.8, "max_palabras": 6, "offset_seg": -0.35},
    "laesquina random":  {"dur_min_silencio": 0.50, "fusionar_bloques_min": 1.8, "max_palabras": 6, "offset_seg": -0.35},
    "tuialista":         {"dur_min_silencio": 0.40, "fusionar_bloques_min": 1.3, "max_palabras": 5, "offset_seg": 0.0},
    "umbral alterno":    {"dur_min_silencio": 0.34, "fusionar_bloques_min": 1.0, "max_palabras": 5, "offset_seg": 0.0},
    "umbralalterno":     {"dur_min_silencio": 0.34, "fusionar_bloques_min": 1.0, "max_palabras": 5, "offset_seg": 0.0},
}
SUBS_DEFAULT = {"dur_min_silencio": 0.36, "fusionar_bloques_min": 1.1, "max_palabras": 5, "offset_seg": 0.0}

def _config_subs(marca):
    """Devuelve la config de subtítulos del canal (o el default)."""
    return SUBS_POR_CANAL.get((marca or "").lower().strip(), SUBS_DEFAULT)


def _fusionar_microbloques(bloques, min_dur):
    """Fusiona bloques demasiado cortos (micro-pausas de respiración) con el
    siguiente, para que los bloques coincidan con frases reales y no con jadeos.
    Crucial en voces rápidas que generan muchos micro-bloques."""
    if not bloques:
        return bloques
    fusionados = []
    ini_actual, fin_actual = bloques[0]
    for i in range(1, len(bloques)):
        b_ini, b_fin = bloques[i]
        # Si el bloque actual es muy corto O el hueco al siguiente es mínimo, fusionar
        if (fin_actual - ini_actual) < min_dur:
            fin_actual = b_fin  # extender el bloque actual hasta el siguiente
        else:
            fusionados.append((ini_actual, fin_actual))
            ini_actual, fin_actual = b_ini, b_fin
    fusionados.append((ini_actual, fin_actual))
    return fusionados


def _detectar_bloques_habla(ruta_audio, umbral_db=-30, dur_min_silencio=0.30):
    """SINCRONÍA FUERTE: detecta los BLOQUES DE HABLA reales (inicio, fin) del audio,
    usando los silencios como fronteras (VAD por energía). Devuelve [(ini, fin), ...].
    Esto permite anclar los subtítulos al ritmo REAL de la voz (no a una estimación).

    ADAPTATIVO: si con el umbral normal no detecta bloques (típico en voces SUSURRANTES
    y bajas como La Viuda), reintenta con umbrales más sensibles (-38, -45 dB) antes de
    rendirse. Así los subtítulos se anclan al ritmo real incluso con voz muy suave."""
    import re
    dur_total = _obtener_duracion_audio_simple(ruta_audio)
    # Umbrales de menos a más sensibles. Una voz susurrante necesita umbral más bajo
    # (capta sonidos más suaves como habla, no como silencio).
    umbrales = [umbral_db, -38, -45]
    for u in umbrales:
        try:
            r = subprocess.run(
                ['ffmpeg', '-i', ruta_audio, '-af',
                 f'silencedetect=noise={u}dB:d={dur_min_silencio}',
                 '-f', 'null', '-'],
                capture_output=True, text=True
            )
            starts = [float(x) for x in re.findall(r'silence_start:\s*([\d.]+)', r.stderr)]  # fin de habla
            ends = [float(x) for x in re.findall(r'silence_end:\s*([\d.]+)', r.stderr)]      # inicio de habla
            bloques = []
            inicio_habla = 0.0
            si = 0
            for ss in starts:
                if ss > inicio_habla + 0.05:
                    bloques.append((inicio_habla, ss))
                if si < len(ends):
                    inicio_habla = ends[si]; si += 1
                else:
                    inicio_habla = ss
            if dur_total > 0 and inicio_habla < dur_total - 0.05:
                bloques.append((inicio_habla, dur_total))
            # Si detectó al menos 2 bloques, es buena señal: usar estos.
            # Con 0-1 bloques, reintentar con umbral más sensible.
            if len(bloques) >= 2:
                if u != umbral_db:
                    print(f"   [SUBS] Voz suave detectada — umbral ajustado a {u}dB ({len(bloques)} bloques)")
                return bloques, dur_total
            ultimo_resultado = (bloques, dur_total)
        except Exception as e:
            print(f"   [SUBS] Error detectando bloques con umbral {u}dB: {e}")
            ultimo_resultado = ([], 0.0)
    # Ningún umbral dio 2+ bloques: el audio es habla CONTINUA sin pausas largas
    # (típico en shorts rápidos). En vez de rendirse, subdividir el habla real en
    # segmentos regulares dentro de la duración detectada. Mucho mejor que el reparto
    # lineal ciego, porque se ancla a la duración REAL del audio.
    if dur_total <= 0:
        dur_total = _obtener_duracion_audio_simple(ruta_audio)
    if dur_total > 2:
        # Detectar inicio y fin reales del habla (recortar silencios de borde)
        ini_real, fin_real = _detectar_borde_habla(ruta_audio, dur_total)
        dur_habla = max(1.0, fin_real - ini_real)
        # Segmentos de ~3s (ritmo natural de lectura de subtítulos)
        n_seg = max(2, int(round(dur_habla / 3.0)))
        paso = dur_habla / n_seg
        bloques_sint = [(ini_real + i*paso, ini_real + (i+1)*paso) for i in range(n_seg)]
        print(f"   [SUBS] Habla continua sin pausas — {n_seg} segmentos sobre habla real ({ini_real:.1f}s-{fin_real:.1f}s)")
        return bloques_sint, dur_total
    return ultimo_resultado


def _corregir_pronunciacion(texto):
    """Corrige palabras que el XTTS español pronuncia mal, reescribiéndolas
    fonéticamente SOLO para la voz (el texto original se conserva para subtítulos).
    XTTS en español tropieza con anglicismos, nombres propios extranjeros y ciertas
    combinaciones de letras. Este diccionario se amplía con lo que el usuario detecte.
    El reemplazo respeta mayúsculas/minúsculas y solo afecta palabras completas."""
    import re
    # clave = palabra original (en minúscula) ; valor = escritura que XTTS pronuncia bien
    REEMPLAZOS = {
        # ── Reportadas por el usuario (La Viuda) ──
        "explica": "eks plica", "explican": "eks plican", "explicar": "eks plicar",
        "explicó": "eks plicó", "explico": "eks plico", "explicación": "eks plicación",
        "explicaciones": "eks plicaciones", "explícame": "eks plícame", "explicando": "eks plicando",
        "iceberg": "áisberg", "icebergs": "áisbergs",
        "washington": "guáshington",
        "amiga": "amíga", "amigas": "amígas", "amigo": "amígo", "amigos": "amígos",
        "illinois": "ilinóis",
        "quince": "kínse",
        "bloodgood": "blad gud",
        # ── Reportadas por el usuario (Monkygraff) ──
        "enterprise": "énterprayz",
        "nearshoring": "níar shórin",
        "timing": "táimin",
        "offshoring": "ófshórin", "reshoring": "ríshórin",
        # ── Anglicismos / tecnología frecuentes (todos los canales, sobre todo TuIALista) ──
        "software": "sóftgüer", "hardware": "járdgüer", "smartphone": "smártfon",
        "internet": "ínternet", "online": "onláin", "offline": "ofláin",
        "streaming": "estrímin", "streamer": "estrímer",
        "podcast": "pódcast", "hashtag": "jáshtag", "influencer": "ínfluenser",
        "chatgpt": "chat g p t", "deepfake": "dípfeik", "deepfakes": "dípfeiks",
        "blockchain": "blókchein", "marketing": "márketin", "branding": "brándin",
        "bitcoin": "bítcoin", "startup": "estártap", "startups": "estártaps",
        "google": "gúgol", "youtube": "yutúb", "whatsapp": "guátsap",
        "iphone": "áifon", "android": "ándroid", "wifi": "guifi",
        "gigabyte": "gígabait", "byte": "bait", "bytes": "baits",
        "ranking": "ránkin", "rankings": "ránkins",
        "trading": "tréidin", "trader": "tréider", "traders": "tréiders",
        "holding": "jóldin", "holdings": "jóldins", "dumping": "dámpin",
        "boom": "bum", "default": "difólt", "lobby": "lóbi",
        # ── Nombres propios / geográficos extranjeros ──
        "hollywood": "jóligud",
        "trump": "tramp", "biden": "báiden", "putin": "pútin",
        "beijing": "beishín", "shanghai": "shanghái", "taiwan": "taiguán",
        "microsoft": "máicrosoft", "tesla": "tésla", "amazon": "ámazon",
        # ── Combinaciones que el modelo suele romper ──
        "algoritmo": "algorítmo", "algoritmos": "algorítmos",
    }
    # frases de varias palabras (se reemplazan primero)
    REEMPLAZOS_FRASE = {
        "new york": "niu york", "los angeles": "los ángeles",
        "machine learning": "mashín lérnin", "deep learning": "díp lérnin",
        "enterprise bank": "énterprayz bánk",
        "wall street": "guól strít", "silicon valley": "sílicon váli",
    }
    # ── Siglas: deletrear en español o expandir ──
    # Se reemplazan como frase para controlar exactamente cómo se leen.
    SIGLAS = {
        "EE.UU.": "Estados Unidos", "EEUU": "Estados Unidos", "EE. UU.": "Estados Unidos",
        "EE.UU": "Estados Unidos", "E.E.U.U.": "Estados Unidos",
        "UE": "Unión Europea", "U.E.": "Unión Europea",
        "OMC": "o eme ce", "O.M.C.": "o eme ce",
        "S&P 500": "ese and pi quinientos", "S&P500": "ese and pi quinientos",
        "S&P": "ese and pi",
        "ONU": "o ene u", "OTAN": "otán", "FMI": "efe eme i", "BCE": "be ce e",
        "PIB": "pib", "IA": "i a", "EU": "Unión Europea",
        "OPEP": "opép", "BRICS": "brics", "G7": "ge siete", "G20": "ge veinte",
    }
    def _reemplazar(match):
        palabra = match.group(0)
        clave = palabra.lower()
        if clave in REEMPLAZOS:
            nuevo = REEMPLAZOS[clave]
            if palabra[0].isupper():
                nuevo = nuevo[0].upper() + nuevo[1:]
            return nuevo
        return palabra
    resultado = texto
    # 1. Siglas primero (incluyen puntos y símbolos, antes de tocar nada)
    #    Se ordenan de más larga a más corta para no romper las compuestas (S&P 500 antes que S&P).
    for sigla in sorted(SIGLAS, key=len, reverse=True):
        resultado = resultado.replace(sigla, " " + SIGLAS[sigla] + " ")
    # 1b. Símbolos comunes a palabras (antes de procesar números)
    resultado = re.sub(r'(\d)\s*%', r'\1 por ciento', resultado)
    resultado = resultado.replace("%", " por ciento ")
    resultado = re.sub(r'(\d)\s*°', r'\1 grados', resultado)
    resultado = resultado.replace("$", " ").replace("€", " euros ").replace("&", " y ")
    # 2. Números → palabras. Usa num2words (robusto: años, decimales, millones) si está
    #    instalado; si no, cae a una regla casera para decimales. Así el worker nunca falla.
    try:
        from num2words import num2words as _n2w
        def _num_a_palabras(m):
            try:
                txt = m.group(0).replace(",", "")  # quitar separador de miles
                if "." in txt:
                    return _n2w(float(txt), lang="es")
                return _n2w(int(txt), lang="es")
            except Exception:
                return m.group(0)
        # Números con posibles separadores de miles y decimales
        resultado = re.sub(r'\d[\d.,]*\d|\d', _num_a_palabras, resultado)
    except Exception:
        # Respaldo si num2words no está instalado: al menos arreglar decimales
        resultado = re.sub(r'(\d+)\.(\d+)', r'\1 punto \2', resultado)
    # 3. Frases de varias palabras
    for frase, rep in REEMPLAZOS_FRASE.items():
        resultado = re.sub(r'\b' + re.escape(frase) + r'\b', rep, resultado, flags=re.IGNORECASE)
    # 4. Palabras sueltas
    resultado = re.sub(r'\b\w+\b', _reemplazar, resultado, flags=re.UNICODE)
    # 5. Espacio antes de coma/punto: workaround del bug de XTTS español que debilita
    #    o corta la última sílaba antes de la puntuación (tu "quince→quice").
    resultado = re.sub(r'\s*([,.;:!?…])', r' \1', resultado)
    # Limpiar espacios dobles que pudieron quedar
    resultado = re.sub(r'\s{2,}', ' ', resultado).strip()
    return resultado


def _detectar_borde_habla(ruta_audio, dur_total):
    """Detecta dónde empieza y termina realmente el habla (recorta silencio inicial/final).
    Usa silencedetect muy sensible solo para los bordes."""
    import re
    try:
        r = subprocess.run(
            ['ffmpeg', '-i', ruta_audio, '-af', 'silencedetect=noise=-45dB:d=0.5',
             '-f', 'null', '-'], capture_output=True, text=True
        )
        starts = [float(x) for x in re.findall(r'silence_start:\s*([\d.]+)', r.stderr)]
        ends = [float(x) for x in re.findall(r'silence_end:\s*([\d.]+)', r.stderr)]
        # inicio del habla: si hay un silencio que empieza en ~0, el habla empieza en su end
        ini = 0.0
        if ends and starts and starts[0] < 0.5:
            ini = ends[0]
        # fin del habla: si hay un silencio final, el habla termina en su start
        fin = dur_total
        if starts and starts[-1] > dur_total - 2.0 and (not ends or ends[-1] < starts[-1]):
            fin = starts[-1]
        if fin <= ini:
            ini, fin = 0.0, dur_total
        return ini, fin
    except Exception:
        return 0.0, dur_total


def _obtener_duracion_audio_simple(ruta_audio):
    try:
        r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0', ruta_audio],
                          capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def _imagen_es_negra(ruta_png, umbral_pblack=92):
    """Detecta si una imagen es (casi) completamente negra usando el filtro
    blackframe de FFmpeg. Devuelve el % de píxeles negros; si supera el umbral,
    la imagen se considera negra/vacía. SD a veces devuelve negro (censura NSFW,
    fallo del modelo) con HTTP 200, lo que corta la retención del video."""
    try:
        if not os.path.exists(ruta_png) or os.path.getsize(ruta_png) < 1000:
            return True  # archivo vacío o minúsculo = inválido
        # blackframe: umbral de luma 32 (oscuro). pblack = % de píxeles bajo ese umbral.
        cmd = ['ffmpeg', '-i', ruta_png, '-vf', 'blackframe=99:32', '-f', 'null', '-']
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        m = re.search(r'pblack:(\d+)', r.stderr)
        if m:
            return int(m.group(1)) >= umbral_pblack
        return False  # blackframe no reportó nada = la imagen tiene contenido
    except Exception:
        return False  # ante la duda, no descartar (evita falsos positivos)


def _generar_subtitulos_shorts(ruta_audio, texto_locucion, escenas_texto, marca, carpeta_reciente, dur_total):
    """Subtítulos anclados a los BLOQUES DE HABLA reales del audio (sincronía fuerte)."""
    ruta_srt = os.path.join(carpeta_reciente, "subtitulos.srt").replace("\\", "/")

    print(f"📝 Generando subtítulos — Canal: {marca} | Duración: {dur_total:.1f}s")

    texto_completo = " ".join(escenas_texto) if escenas_texto else texto_locucion
    if not texto_completo.strip():
        print("   [ERROR] Texto vacío.")
        return None

    # SINCRONÍA FUERTE POR CANAL: cada canal tiene distinto ritmo de voz, así que la
    # detección y el reparto se ajustan a su config (La Viuda lenta = fina; LaesquinaRandom
    # rápida = pausas más largas + fusión de micro-bloques para no fragmentar).
    cfg = _config_subs(marca)
    bloques, dur_detectada = _detectar_bloques_habla(
        ruta_audio, dur_min_silencio=cfg["dur_min_silencio"]
    ) if ruta_audio and os.path.exists(ruta_audio) else ([], 0.0)
    # Fusionar micro-bloques (respiraciones) según el canal, para que los bloques
    # coincidan con frases reales y los subtítulos no se desincronicen.
    if bloques:
        antes = len(bloques)
        bloques = _fusionar_microbloques(bloques, cfg["fusionar_bloques_min"])
        if len(bloques) != antes:
            print(f"   [SUBS] {antes} bloques → {len(bloques)} tras fusionar micro-pausas (canal {marca})")
    _num_bloques = len(bloques)
    # Aplicar el OFFSET de sincronía del canal: desplaza todos los bloques en el tiempo.
    # Negativo = adelanta los subtítulos (si iban atrasados); positivo = los atrasa.
    _offset = cfg.get("offset_seg", 0.0)
    if _offset and bloques:
        bloques = [(max(0.0, ini + _offset), max(0.05, fin + _offset)) for (ini, fin) in bloques]
        print(f"   [SUBS] Offset de {_offset:+.2f}s aplicado (sincronía fina canal {marca})")
    if bloques and len(bloques) >= 1:
        print(f"   [SUBS] {len(bloques)} bloques de habla — sincronía por canal ({marca})")
        _generar_srt_por_bloques(texto_completo, bloques, dur_total or dur_detectada, marca, ruta_srt, cfg["max_palabras"])
    else:
        print(f"   [SUBS] Sin bloques detectados — distribución lineal de respaldo")
        _generar_srt_calibrado(texto_completo, dur_total, marca, ruta_srt)
    print(f"   [OK] SRT generado.")
    return ruta_srt, _num_bloques


def _generar_srt_por_bloques(texto_completo, bloques, dur_total, marca, ruta_srt, max_pal=None):
    """SINCRONÍA FUERTE: reparte el texto en los bloques de habla reales, proporcional
    a la duración de cada bloque, y distribuye las palabras dentro del tiempo real de
    cada bloque. Así los subtítulos siguen el ritmo REAL de la voz (rápido/lento/pausas)."""
    import re
    if max_pal is None:
        ppm = _obtener_velocidad_canal(marca)
        max_pal = 4 if ppm <= 90 else (5 if ppm <= 130 else 6)

    palabras = texto_completo.split()
    total_pal = len(palabras)
    if total_pal == 0 or not bloques:
        return
    dur_habla = sum(f - i for i, f in bloques) or dur_total

    # Intentar alinear FRASES con bloques: si el texto tiene tantas frases como
    # bloques (±1), cada bloque toma una frase entera (corte semántico limpio).
    frases = [f.strip() for f in re.split(r'(?<=[.!?…])\s+', texto_completo.strip()) if f.strip()]
    usar_frases = frases and abs(len(frases) - len(bloques)) <= max(1, len(bloques)//3)

    chunks = []  # (texto, ini, fin)
    if usar_frases and len(frases) >= len(bloques):
        # Asignar frases a bloques: repartir las frases entre los bloques en orden
        fr_por_bloque = _repartir(len(frases), len(bloques))
        fr_idx = 0
        for bi, (b_ini, b_fin) in enumerate(bloques):
            n_fr = fr_por_bloque[bi]
            texto_bloque = " ".join(frases[fr_idx:fr_idx + n_fr])
            fr_idx += n_fr
            chunks += _trocear_en_tiempo(texto_bloque, b_ini, b_fin, max_pal)
    else:
        # Reparto proporcional por palabras según duración del bloque
        pal_idx = 0
        for bi, (b_ini, b_fin) in enumerate(bloques):
            if bi == len(bloques) - 1:
                n_pal = total_pal - pal_idx
            else:
                frac = (b_fin - b_ini) / dur_habla
                n_pal = max(1, round(total_pal * frac))
            n_pal = min(n_pal, total_pal - pal_idx)
            if n_pal <= 0:
                continue
            texto_bloque = " ".join(palabras[pal_idx:pal_idx + n_pal])
            pal_idx += n_pal
            chunks += _trocear_en_tiempo(texto_bloque, b_ini, b_fin, max_pal)
        if pal_idx < total_pal and chunks:
            txt, ini, fin = chunks[-1]
            chunks[-1] = (txt + " " + " ".join(palabras[pal_idx:]), ini, fin)

    def fmt(t):
        h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    with open(ruta_srt, "w", encoding="utf-8") as srt:
        for idx, (txt, ini, fin) in enumerate(chunks):
            if fin <= ini:
                fin = ini + 0.4
            srt.write(f"{idx+1}\n{fmt(ini)} --> {fmt(fin)}\n{txt.upper()}\n\n")


def _repartir(n_items, n_grupos):
    """Reparte n_items entre n_grupos lo más parejo posible. Devuelve lista de tamaños."""
    base = n_items // n_grupos
    extra = n_items % n_grupos
    return [base + (1 if k < extra else 0) for k in range(n_grupos)]


def _trocear_en_tiempo(texto, t_ini, t_fin, max_pal):
    """Divide 'texto' en chunks de max_pal palabras, repartiendo [t_ini, t_fin].
    Tope: ningún chunk dura más de 3s (legibilidad); si la voz deja tiempo de sobra,
    el chunk se muestra su tiempo natural y el resto queda como pausa visual."""
    pal = texto.split()
    if not pal:
        return []
    seg_pal = (t_fin - t_ini) / len(pal)
    out = []
    j = 0
    while j < len(pal):
        grupo = pal[j:j + max_pal]
        ini = t_ini + j * seg_pal
        fin = t_ini + min(len(pal), j + max_pal) * seg_pal
        # Tope de 3.0s por chunk para que el subtítulo no se quede pegado demasiado
        if fin - ini > 3.0:
            fin = ini + 3.0
        out.append((" ".join(grupo), ini, fin))
        j += max_pal
    return out


def _generar_srt_anclado(texto_completo, dur_total, marca, ruta_srt, silencios):
    """[LEGADO] Distribuye chunks anclándolos a las pausas reales del audio.
    Mantenido por compatibilidad; el flujo nuevo usa _generar_srt_por_bloques."""
    import re
    ppm = _obtener_velocidad_canal(marca)
    palabras_por_chunk = 4 if ppm <= 90 else (5 if ppm <= 130 else 6)

    frases_raw = re.split(r'(?<=[.!?…])\s+', texto_completo.strip())
    frases_raw = [f.strip() for f in frases_raw if f.strip()]
    chunks = []
    for frase in frases_raw:
        palabras = frase.split()
        if len(palabras) <= palabras_por_chunk:
            chunks.append(frase)
        else:
            for j in range(0, len(palabras), palabras_por_chunk):
                parte = " ".join(palabras[j:j+palabras_por_chunk])
                if parte.strip():
                    chunks.append(parte)
    if not chunks:
        return

    total_palabras = sum(len(c.split()) for c in chunks)
    seg_por_palabra = dur_total / total_palabras

    inicios_est = []
    t = 0.0
    for c in chunks:
        inicios_est.append(t)
        t += len(c.split()) * seg_por_palabra

    silencios_sorted = sorted(silencios)
    inicios_finales = []
    for ini_est in inicios_est:
        candidatos = [s for s in silencios_sorted if abs(s - ini_est) <= 1.5]
        if candidatos:
            mejor = min(candidatos, key=lambda s: abs(s - ini_est))
            inicios_finales.append(mejor)
        else:
            inicios_finales.append(ini_est)

    for i in range(1, len(inicios_finales)):
        if inicios_finales[i] <= inicios_finales[i-1]:
            inicios_finales[i] = inicios_finales[i-1] + 0.3

    with open(ruta_srt, "w", encoding="utf-8") as srt:
        for idx, chunk in enumerate(chunks):
            ini = inicios_finales[idx]
            fin_t = dur_total if idx == len(chunks)-1 else inicios_finales[idx+1]
            if ini >= fin_t:
                fin_t = ini + 0.5
            h_i,m_i = int(ini//3600),int((ini%3600)//60)
            s_i,ms_i = int(ini%60),int((ini%1)*1000)
            h_f,m_f = int(fin_t//3600),int((fin_t%3600)//60)
            s_f,ms_f = int(fin_t%60),int((fin_t%1)*1000)
            srt.write(
                f"{idx+1}\n"
                f"{h_i:02d}:{m_i:02d}:{s_i:02d},{ms_i:03d} --> "
                f"{h_f:02d}:{m_f:02d}:{s_f:02d},{ms_f:03d}\n"
                f"{chunk.upper()}\n\n"
            )


# ══════════════════════════════════════════════════════════════
# GENERADORES DE DOCUMENTOS WORD
# ══════════════════════════════════════════════════════════════

def _generar_word_paquete(paquete, marca, formato, carpeta):
    import tempfile, subprocess as sp
    es_largo   = "16:9" in formato
    carpeta_js = carpeta.replace("\\", "/")
    ruta_out   = f"{carpeta_js}/paquete_publicacion.docx"

    tmp_json = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8')
    json.dump(paquete, tmp_json, ensure_ascii=False)
    tmp_json.close()
    ruta_json  = tmp_json.name.replace("\\", "/")
    fmt_label  = "Largo 16:9" if es_largo else "Short 9:16"
    es_largo_js = "true" if es_largo else "false"

    js = f"""
const {{ Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, ShadingType }} = require('docx');
const fs = require('fs');
const p = JSON.parse(fs.readFileSync('{ruta_json}', 'utf8'));
const CR="C0392B",CN="1A1A1A",CG="F5F5F5",CA="2980B9";
function sec(t){{ return new Paragraph({{ children:[new TextRun({{text:t,bold:true,color:"FFFFFF",size:26,font:"Arial"}})], shading:{{fill:CR,type:ShadingType.CLEAR}}, spacing:{{before:300,after:100}}, indent:{{left:200,right:200}} }}); }}
function blq(t,it=false,c=CN){{ return new Paragraph({{ children:[new TextRun({{text:t||"",size:22,font:"Arial",italics:it,color:c}})], shading:{{fill:CG,type:ShadingType.CLEAR}}, spacing:{{before:80,after:160}}, indent:{{left:200,right:200}} }}); }}
function sep(){{ return new Paragraph({{ border:{{bottom:{{style:BorderStyle.SINGLE,size:2,color:"DDDDDD"}}}}, spacing:{{before:160,after:160}} }}); }}
const ch=[
  new Paragraph({{children:[new TextRun({{text:"PAQUETE DE PUBLICACION",bold:true,size:40,font:"Arial",color:CR}})],alignment:AlignmentType.CENTER,spacing:{{before:0,after:60}}}}),
  new Paragraph({{children:[new TextRun({{text:"Canal: {marca}  |  Formato: {fmt_label}",size:20,font:"Arial",color:"777777"}})],alignment:AlignmentType.CENTER,spacing:{{before:0,after:40}}}}),
  new Paragraph({{border:{{bottom:{{style:BorderStyle.SINGLE,size:6,color:CR}}}},spacing:{{before:0,after:300}}}}),
  sec("TITULO SEO OPTIMIZADO"),
  new Paragraph({{children:[new TextRun({{text:p.titulo_final||"",bold:true,size:26,font:"Arial",color:CN}})],shading:{{fill:CG,type:ShadingType.CLEAR}},spacing:{{before:100,after:200}},indent:{{left:200,right:200}}}}),
  sep(),
  sec("DESCRIPCION COMPLETA"),
  ...(p.descripcion||"").split("\\n\\n").filter(x=>x.trim()).map(x=>new Paragraph({{children:[new TextRun({{text:x.trim(),size:22,font:"Arial",color:CN}})],shading:{{fill:CG,type:ShadingType.CLEAR}},spacing:{{before:80,after:80}},indent:{{left:200,right:200}}}})),
  sep(),sec("HASHTAGS"),blq(p.hashtags||"",false,CA),
  sep(),sec("KEYWORDS"),blq(p.keywords||""),
  sep(),sec("PRIMER COMENTARIO FIJO"),blq(p.primer_comentario||"",true),
  sep(),sec("PROMPT HOOK"),blq(p.prompt_hook||"",true,"555555"),
];
if({es_largo_js} && p.prompt_miniatura_A){{
  ch.push(sep(),sec("MINIATURA A"),blq(p.prompt_miniatura_A||"",true,"555555"),
          sec("MINIATURA B"),blq(p.prompt_miniatura_B||"",true,"555555"),
          sec("MINIATURA C"),blq(p.prompt_miniatura_C||"",true,"555555"));
}}
ch.push(new Paragraph({{border:{{top:{{style:BorderStyle.SINGLE,size:6,color:CR}}}},spacing:{{before:300,after:100}}}}));
ch.push(new Paragraph({{children:[new TextRun({{text:"Generado por Dark Factory — Sistema Pinpinela",size:18,font:"Arial",color:"AAAAAA",italics:true}})],alignment:AlignmentType.CENTER}}));
const doc=new Document({{styles:{{default:{{document:{{run:{{font:"Arial",size:22}}}}}}}},sections:[{{properties:{{page:{{size:{{width:12240,height:15840}},margin:{{top:1440,right:1440,bottom:1440,left:1440}}}}}},children:ch}}]}});
Packer.toBuffer(doc).then(buf=>{{fs.writeFileSync('{ruta_out}',buf);console.log('OK');}}).catch(e=>{{console.error(e);process.exit(1);}});
"""
    tmp_js = tempfile.NamedTemporaryFile(suffix='.js', delete=False, mode='w', encoding='utf-8')
    tmp_js.write(js)
    tmp_js.close()
    result = sp.run(['node', tmp_js.name], capture_output=True, text=True)
    os.unlink(tmp_js.name)
    os.unlink(tmp_json.name)
    if result.returncode != 0:
        raise Exception(result.stderr)

def _generar_word_guion(texto_locucion, marca, formato, tarea, carpeta):
    import tempfile, subprocess as sp
    es_largo   = "16:9" in formato
    carpeta_js = carpeta.replace("\\", "/")
    ruta_out   = f"{carpeta_js}/guion_completo.docx"
    fmt_label  = "Largo 16:9" if es_largo else "Short 9:16"

    guion_data = {
        "titulo":   tarea.get("titulo_sugerido", "Guion sin titulo"),
        "marca":    marca,
        "formato":  fmt_label,
        "escenas":  tarea.get("escenas", []),
        "locucion": texto_locucion
    }
    tmp_json = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8')
    json.dump(guion_data, tmp_json, ensure_ascii=False)
    tmp_json.close()
    ruta_json = tmp_json.name.replace("\\", "/")

    js = f"""
const {{ Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, ShadingType }} = require('docx');
const fs = require('fs');
const d = JSON.parse(fs.readFileSync('{ruta_json}', 'utf8'));
const CR="C0392B",CN="1A1A1A",CG="F5F5F5";
function sep(){{ return new Paragraph({{border:{{bottom:{{style:BorderStyle.SINGLE,size:1,color:"EEEEEE"}}}},spacing:{{before:60,after:60}}}}); }}
const ch=[
  new Paragraph({{children:[new TextRun({{text:"GUION COMPLETO",bold:true,size:40,font:"Arial",color:CR}})],alignment:AlignmentType.CENTER,spacing:{{before:0,after:60}}}}),
  new Paragraph({{children:[new TextRun({{text:"Canal: "+d.marca+"  |  Formato: "+d.formato,size:20,font:"Arial",color:"777777"}})],alignment:AlignmentType.CENTER,spacing:{{before:0,after:40}}}}),
  new Paragraph({{children:[new TextRun({{text:d.titulo,bold:true,size:28,font:"Arial",color:CN}})],alignment:AlignmentType.CENTER,shading:{{fill:CG,type:ShadingType.CLEAR}},spacing:{{before:100,after:60}},indent:{{left:200,right:200}}}}),
  new Paragraph({{border:{{bottom:{{style:BorderStyle.SINGLE,size:6,color:CR}}}},spacing:{{before:0,after:300}}}}),
];
if(d.escenas && d.escenas.length>0){{
  d.escenas.forEach(e=>{{
    ch.push(new Paragraph({{children:[new TextRun({{text:"ESCENA "+e.id_escena,bold:true,size:22,font:"Arial",color:CR}})],spacing:{{before:200,after:40}},indent:{{left:200}}}}));
    ch.push(new Paragraph({{children:[new TextRun({{text:"LOCUCION:",bold:true,size:20,font:"Arial",color:CN}})],spacing:{{before:40,after:20}},indent:{{left:200}}}}));
    ch.push(new Paragraph({{children:[new TextRun({{text:e.texto_locucion||"",size:20,font:"Arial",color:CN}})],shading:{{fill:CG,type:ShadingType.CLEAR}},spacing:{{before:20,after:40}},indent:{{left:200,right:200}}}}));
    ch.push(new Paragraph({{children:[new TextRun({{text:"PROMPT VISUAL:",bold:true,size:18,font:"Arial",color:"555555"}})],spacing:{{before:20,after:20}},indent:{{left:200}}}}));
    ch.push(new Paragraph({{children:[new TextRun({{text:e.prompt_visual||"",size:18,font:"Arial",color:"777777",italics:true}})],spacing:{{before:0,after:60}},indent:{{left:200,right:200}}}}));
    ch.push(sep());
  }});
}} else {{
  d.locucion.split("\\n").filter(p=>p.trim()).forEach(p=>{{
    ch.push(new Paragraph({{children:[new TextRun({{text:p.trim(),size:22,font:"Arial",color:CN}})],spacing:{{before:80,after:80}},indent:{{left:200,right:200}}}}));
  }});
}}
ch.push(new Paragraph({{children:[new TextRun({{text:"Generado por Dark Factory — Sistema Pinpinela",size:18,font:"Arial",color:"AAAAAA",italics:true}})],alignment:AlignmentType.CENTER,spacing:{{before:300}}}}));
const doc=new Document({{styles:{{default:{{document:{{run:{{font:"Arial",size:22}}}}}}}},sections:[{{properties:{{page:{{size:{{width:12240,height:15840}},margin:{{top:1440,right:1440,bottom:1440,left:1440}}}}}},children:ch}}]}});
Packer.toBuffer(doc).then(buf=>{{fs.writeFileSync('{ruta_out}',buf);console.log('OK');}}).catch(e=>{{console.error(e);process.exit(1);}});
"""
    tmp_js = tempfile.NamedTemporaryFile(suffix='.js', delete=False, mode='w', encoding='utf-8')
    tmp_js.write(js)
    tmp_js.close()
    result = sp.run(['node', tmp_js.name], capture_output=True, text=True)
    os.unlink(tmp_js.name)
    os.unlink(tmp_json.name)
    if result.returncode != 0:
        raise Exception(result.stderr)


# ══════════════════════════════════════════════════════════════
# BUCLE PRINCIPAL DE PROCESAMIENTO
# ══════════════════════════════════════════════════════════════

def _clip_es_valido(ruta, dur_esperada=None):
    """Verifica que un clip de video sea legible y tenga duración válida."""
    if not os.path.exists(ruta) or os.path.getsize(ruta) < 1024:
        return False
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', ruta],
            capture_output=True, text=True
        )
        dur = float(r.stdout.strip())
        if dur <= 0.1:
            return False
        # Si esperamos cierta duración, tolerar 30% de diferencia
        if dur_esperada and dur < dur_esperada * 0.5:
            return False
        return True
    except Exception:
        return False


def _generar_clip_simple(path_origen, path_clip, dur, w, h, fps):
    """Genera un clip simple a prueba de balas (zoom lento) cuando el complejo falla."""
    try:
        es_imagen = path_origen.lower().endswith(('.png', '.jpg', '.jpeg'))
        total_frames = int(round(dur * fps))
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
              f"zoompan=z='min(1.0+0.0008*on,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":d={total_frames}:fps={fps}:s={w}x{h},setpts=PTS-STARTPTS")
        if es_imagen:
            cmd = ['ffmpeg', '-y', '-i', path_origen, '-vf', vf, '-t', str(dur),
                   '-c:v', 'libx264', '-preset', 'ultrafast', '-threads', '0',
                   '-pix_fmt', 'yuv420p', '-r', str(fps), path_clip]
        else:
            cmd = ['ffmpeg', '-y', '-stream_loop', '-1', '-i', path_origen,
                   '-vf', f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setpts=PTS-STARTPTS",
                   '-t', str(dur), '-c:v', 'libx264', '-preset', 'ultrafast',
                   '-threads', '0', '-pix_fmt', 'yuv420p', '-r', str(fps), path_clip]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return _clip_es_valido(path_clip)
    except Exception:
        return False




# ═══════════ MÓDULO DE HOOKS V2 (integrado al pipeline) ═══════════
def _dur(ruta):
    try:
        r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                            '-of','csv=p=0', ruta], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0

def _clip_valido(ruta, min_dur=0.2):
    return os.path.exists(ruta) and os.path.getsize(ruta) > 1000 and _dur(ruta) >= min_dur


# ── CONFIGURACIÓN DE RE-HOOKS POR CANAL ──────────────────────────────────────
# Cada canal tiene su ritmo. Aquí se define, por canal:
#   dur_hook        = cuántos segundos dura cada re-hook en pantalla (tiempo de lectura)
#   dur_inicial     = duración del hook inicial (el primer gancho del video)
#   seg_por_rehook  = cada cuántos segundos de video aparece un re-hook (densidad)
#   max_rehooks     = tope de re-hooks por video
#   intensidad_texto= "fuerte" (texto grande/contrastado) o "suave"
# Para AJUSTAR un canal: cambia sus números aquí. No afecta a los demás.
HOOKS_POR_CANAL = {
    # La Viuda (terror): hooks pausados, lectura lenta, pocos (no romper la tensión)
    "la viuda":          {"dur_hook": 2.8, "dur_inicial": 3.0, "seg_por_rehook": 90, "max_rehooks": 6, "intensidad_texto": "suave"},
    "laviuda":           {"dur_hook": 2.8, "dur_inicial": 3.0, "seg_por_rehook": 90, "max_rehooks": 6, "intensidad_texto": "suave"},
    # Monkygraff (geopolítica, denso): hooks más largos para leer, ritmo medio
    "monkygraff":        {"dur_hook": 2.8, "dur_inicial": 3.0, "seg_por_rehook": 80, "max_rehooks": 8, "intensidad_texto": "fuerte"},
    # FiltradoMX (drama): hooks ágiles, más frecuentes (mantener el morbo)
    "filtradomx":        {"dur_hook": 2.4, "dur_inicial": 2.6, "seg_por_rehook": 60, "max_rehooks": 10, "intensidad_texto": "fuerte"},
    # LaesquinaRandom (curiosidades, ágil): hooks rápidos y frecuentes
    "laesquinarandom":   {"dur_hook": 2.2, "dur_inicial": 2.4, "seg_por_rehook": 55, "max_rehooks": 10, "intensidad_texto": "fuerte"},
    "la esquina random": {"dur_hook": 2.2, "dur_inicial": 2.4, "seg_por_rehook": 55, "max_rehooks": 10, "intensidad_texto": "fuerte"},
    # TuIALista (tech): hooks medios, informativos
    "tuialista":         {"dur_hook": 2.6, "dur_inicial": 2.8, "seg_por_rehook": 70, "max_rehooks": 9, "intensidad_texto": "fuerte"},
    # Umbral Alterno (documental): hooks pausados para leer, ritmo medio-serio
    "umbral alterno":    {"dur_hook": 2.8, "dur_inicial": 3.0, "seg_por_rehook": 85, "max_rehooks": 8, "intensidad_texto": "suave"},
    "umbralalterno":     {"dur_hook": 2.8, "dur_inicial": 3.0, "seg_por_rehook": 85, "max_rehooks": 8, "intensidad_texto": "suave"},
}
HOOKS_DEFAULT = {"dur_hook": 2.6, "dur_inicial": 2.8, "seg_por_rehook": 75, "max_rehooks": 8, "intensidad_texto": "fuerte"}

def _config_hooks(marca):
    """Devuelve la config de re-hooks del canal (o el default)."""
    return HOOKS_POR_CANAL.get((marca or "").lower().strip(), HOOKS_DEFAULT)


def planificar_hooks(num_escenas, duraciones_escenas, hooks_frases, es_short, dur_hook=2.6, marca=""):
    """
    Decide DÓNDE caen los re-hooks (en qué límites de escena) y con qué frase/formato.
    Devuelve:
      - hook_inicial: frase del hook inicial (o None)
      - inserciones: lista de dicts {despues_de_escena, frase, formato, dur}
        'despues_de_escena' = índice de escena tras la cual se inserta el re-hook
    NO toca archivos; solo planifica. Determinista por semilla (reproducible).
    dur_hook subido a 2.6s (antes 1.8s): 1.8s era muy corto para leer la frase del
    hook, se sentía atropellado. 2.6s da tiempo a leerla sin frenar el ritmo.
    """
    # Filtrar frases vacías/None; la primera válida es el hook inicial
    _frases_limpias = [str(f).strip() for f in (hooks_frases or []) if f and str(f).strip()]
    frase_inicial = _frases_limpias[0] if _frases_limpias else None
    frases_inter = _frases_limpias[1:] if len(_frases_limpias) > 1 else []

    dur_total = sum(duraciones_escenas) if duraciones_escenas else 0
    if dur_total < 5 or num_escenas < 2:
        return frase_inicial, []  # solo hook inicial, sin re-hooks

    # Config del canal (densidad y duración del re-hook)
    cfg = _config_hooks(marca)
    dur_hook_canal = cfg["dur_hook"]
    seg_por_rehook = cfg["seg_por_rehook"]
    max_rehooks = cfg["max_rehooks"]

    # Cuántos re-hooks: según la densidad del canal (cada 'seg_por_rehook' segundos)
    if es_short:
        n = min(1, len(frases_inter))
    else:
        n = min(len(frases_inter), max_rehooks, max(1, int(dur_total // seg_por_rehook)))
    if n <= 0:
        return frase_inicial, []

    # Tiempos objetivo (repartidos), evitando el inicio (primeras escenas) y el final
    inicio_t = max(8.0, duraciones_escenas[0])
    fin_t = dur_total - 8.0
    if fin_t <= inicio_t:
        return frase_inicial, []
    paso = (fin_t - inicio_t) / (n + 1)
    tiempos_objetivo = [inicio_t + paso * k for k in range(1, n + 1)]

    # Para cada tiempo objetivo, encontrar el LÍMITE DE ESCENA más cercano
    # (acumulado de duraciones). Así el hook cae entre escenas, no a media frase.
    acum = []
    s = 0.0
    for d in duraciones_escenas:
        s += d
        acum.append(s)  # acum[i] = tiempo donde TERMINA la escena i

    inserciones = []
    escenas_usadas = set()
    rnd = random.Random("hooksplan")
    for idx, t_obj in enumerate(tiempos_objetivo):
        # buscar la escena cuyo final esté más cerca del tiempo objetivo
        mejor_i, mejor_dist = None, 1e9
        for i, t_fin in enumerate(acum[:-1]):  # no tras la última escena
            if i in escenas_usadas:
                continue
            dist = abs(t_fin - t_obj)
            if dist < mejor_dist:
                mejor_dist, mejor_i = dist, i
        if mejor_i is None:
            continue
        escenas_usadas.add(mejor_i)
        frase = frases_inter[idx] if idx < len(frases_inter) else frases_inter[-1]
        # Alternar formato A (pattern interrupt) y B (flash-forward)
        formato = "A" if rnd.random() < 0.5 else "B"
        inserciones.append({
            "despues_de_escena": mejor_i,
            "frase": frase,
            "formato": formato,
            "dur": dur_hook_canal,
        })

    # Ordenar por escena
    inserciones.sort(key=lambda x: x["despues_de_escena"])
    return frase_inicial, inserciones


def recalcular_srt(ruta_srt_in, ruta_srt_out, inserciones, duraciones_escenas, dur_hook_inicial):
    """
    Desplaza los tiempos del SRT para compensar los hooks insertados.
    - El hook inicial desplaza TODO el SRT hacia adelante (dur_hook_inicial).
    - Cada re-hook tras la escena i desplaza los subtítulos posteriores a ese punto.
    """
    if not os.path.exists(ruta_srt_in):
        return False
    try:
        # Calcular tiempo de fin de cada escena (para saber a partir de qué segundo desplazar)
        acum = []
        s = 0.0
        for d in duraciones_escenas:
            s += d
            acum.append(s)

        # Lista de (tiempo_original, desplazamiento_a_aplicar_desde_ahi)
        desfases = []
        for ins in inserciones:
            i = ins["despues_de_escena"]
            if i < len(acum):
                desfases.append((acum[i], ins["dur"]))
        desfases.sort()

        def nuevo_t(t):
            # Desplazamiento del hook inicial + los re-hooks anteriores a t
            extra = dur_hook_inicial
            for t_ins, d in desfases:
                if t > t_ins:
                    extra += d
            return t + extra

        def parse_t(s):
            h, m, resto = s.split(":")
            seg, ms = resto.split(",")
            return int(h)*3600 + int(m)*60 + int(seg) + int(ms)/1000.0

        def fmt_t(t):
            h = int(t // 3600); t -= h*3600
            m = int(t // 60); t -= m*60
            seg = int(t); ms = int(round((t - seg)*1000))
            if ms >= 1000: seg += 1; ms = 0
            return f"{h:02d}:{m:02d}:{seg:02d},{ms:03d}"

        with open(ruta_srt_in, encoding="utf-8") as f:
            lineas = f.read().split("\n")
        out = []
        for ln in lineas:
            if "-->" in ln:
                a, b = ln.split("-->")
                ta = nuevo_t(parse_t(a.strip()))
                tb = nuevo_t(parse_t(b.strip()))
                out.append(f"{fmt_t(ta)} --> {fmt_t(tb)}")
            else:
                out.append(ln)
        with open(ruta_srt_out, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        return True
    except Exception as e:
        print(f"   [HOOKS] Error recalculando SRT: {e}")
        return False


# ═══════════ GENERACIÓN DE CLIPS DE HOOK ═══════════
def _obtener_stinger_canal(carpeta_marca, tipo, dur_sil, ruta_salida):
    """Usa los stingers REALES del canal (stinger1.mp3 = whoosh, stinger2.mp3 = impact)
    si existen en la carpeta de assets. Si no, genera uno sintético como respaldo.
    Devuelve True si dejó un audio válido en ruta_salida."""
    import random as _rnd
    # Mapeo: formato A (whoosh) → stinger1; formato B (impact) → stinger2
    nombre = "stinger1.mp3" if tipo == "whoosh" else "stinger2.mp3"
    ruta_real = os.path.join(carpeta_marca, nombre) if carpeta_marca else None
    # Si no existe el específico, intentar el otro stinger disponible
    if ruta_real and not os.path.exists(ruta_real):
        alt = os.path.join(carpeta_marca, "stinger2.mp3" if tipo == "whoosh" else "stinger1.mp3")
        ruta_real = alt if os.path.exists(alt) else None
    if ruta_real and os.path.exists(ruta_real):
        try:
            # Recortar/ajustar el stinger real a la duración del hueco del hook
            subprocess.run(['ffmpeg','-y','-i', ruta_real, '-t', str(dur_sil),
                            '-af', f'afade=t=out:st={max(0.1,dur_sil*0.6):.2f}:d={max(0.2,dur_sil*0.4):.2f}',
                            '-c:a','pcm_s16le','-ar','44100','-ac','2', ruta_salida],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if _clip_valido(ruta_salida, 0.05):
                return True
        except Exception:
            pass
    # Respaldo: stinger sintético (el de siempre)
    try:
        if tipo == "whoosh":
            _filt = (f"anoisesrc=d={dur_sil}:c=pink:a=0.25,"
                     f"afade=t=in:d=0.3,afade=t=out:st={dur_sil*0.5:.2f}:d={dur_sil*0.5:.2f},"
                     f"highpass=f=200,lowpass=f=3000")
        else:
            _filt = f"sine=frequency=80:duration={dur_sil},afade=t=out:st=0.1:d={dur_sil-0.1:.2f}"
        subprocess.run(['ffmpeg','-y','-f','lavfi','-i', _filt,
                        '-c:a','pcm_s16le','-ar','44100','-ac','2', ruta_salida],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return _clip_valido(ruta_salida, 0.05)
    except Exception:
        return False


def _generar_stinger(ruta_salida, dur=1.2, tipo="whoosh"):
    try:
        if tipo == "whoosh":
            filtro = (f"anoisesrc=d={dur}:c=pink:a=0.3,"
                      f"afade=t=in:d=0.3,afade=t=out:st={dur*0.5:.2f}:d={dur*0.5:.2f},"
                      f"highpass=f=200,lowpass=f=3000")
        else:
            filtro = f"sine=frequency=80:duration={dur},afade=t=out:st=0.1:d={dur-0.1:.2f}"
        cmd = ['ffmpeg','-y','-f','lavfi','-i', filtro, '-ar','44100','-ac','2','-q:a','5', ruta_salida]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(ruta_salida)
    except Exception:
        return False

def _texto_en_frame(ruta_img, frase, ruta_salida, w, h, pil, fuentes):
    if not pil or not frase:
        return False
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.open(ruta_img).convert('RGBA').resize((w, h))
        img = Image.alpha_composite(img, Image.new('RGBA', img.size, (0,0,0,120)))
        draw = ImageDraw.Draw(img)
        fsize = int(h * 0.072)
        font = None
        for rf in fuentes:
            if os.path.exists(rf):
                try: font = ImageFont.truetype(rf, fsize); break
                except: continue
        if not font: font = ImageFont.load_default()
        palabras = frase.upper().split()
        lineas, actual = [], ""
        for p in palabras:
            prueba = (actual + " " + p).strip()
            bb = draw.textbbox((0,0), prueba, font=font)
            if bb[2]-bb[0] > w*0.85 and actual:
                lineas.append(actual); actual = p
            else:
                actual = prueba
        if actual: lineas.append(actual)
        alto_l = int(fsize*1.25)
        y0 = (h - alto_l*len(lineas))//2
        for idx, l in enumerate(lineas):
            bb = draw.textbbox((0,0), l, font=font); tw = bb[2]-bb[0]
            x = (w-tw)//2; y = y0 + idx*alto_l
            for dx in range(-3,4):
                for dy in range(-3,4):
                    draw.text((x+dx,y+dy), l, font=font, fill=(0,0,0,255))
            draw.text((x,y), l, font=font, fill=(255,220,40,255))
        img.convert('RGB').save(ruta_salida)
        return os.path.exists(ruta_salida)
    except Exception as e:
        print(f"   [HOOK] texto: {e}")
        return False

def generar_clip_hook(frase, img, ruta_salida, w, h, fps, carpeta, pil, fuentes, formato="A", dur=1.8):
    """Genera UN clip de hook SOLO VIDEO (el concat es mudo; el stinger va en el audio).
    Formato A: zoom punch + flash blanco. Formato B: zoom out + fades (teaser)."""
    try:
        frame = os.path.join(carpeta, f"_hkf_{random.randint(1000,99999)}.png")
        if not _texto_en_frame(img, frase, frame, w, h, pil, fuentes):
            frame = img
        tf = int(dur*fps)
        # ZOOM CENTRADO: anclar el zoompan al centro (x/y centrados respecto al zoom)
        # para que el texto CREZCA HACIA EL CENTRO y no se desplace a un costado.
        _cx = "x='iw/2-(iw/zoom/2)'"
        _cy = "y='ih/2-(ih/zoom/2)'"
        if formato == "A":  # pattern interrupt: zoom punch CENTRADO + flash blanco
            vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                  f"zoompan=z='1.0+0.4*on/{tf}':{_cx}:{_cy}:d={tf}:s={w}x{h}:fps={fps},"
                  f"fade=t=in:st=0:d=0.08:color=white")
        else:  # flash-forward: zoom out CENTRADO + fades (teaser)
            vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                  f"zoompan=z='1.15-0.1*on/{tf}':{_cx}:{_cy}:d={tf}:s={w}x{h}:fps={fps},"
                  f"fade=t=in:st=0:d=0.15,fade=t=out:st={dur-0.2:.2f}:d=0.2")
        subprocess.run(['ffmpeg','-y','-loop','1','-i', frame,'-vf', vf,'-t', str(dur),
                        '-r', str(fps),'-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p',
                        '-an', ruta_salida],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if frame != img:
            try: os.remove(frame)
            except: pass
        return ruta_salida if _clip_valido(ruta_salida) else None
    except Exception as e:
        print(f"   [HOOK] clip {formato}: {e}")
        return None


def _detectar_silencios(ruta_audio, umbral_db=-32, dur_min=0.28):
    """Devuelve una lista de tiempos (segundos) donde hay silencios reales en el
    audio (centro de cada pausa). Sirve para cortar en pausas naturales de la
    narración, no a media palabra."""
    try:
        cmd = ['ffmpeg','-i', ruta_audio,'-af',
               f'silencedetect=noise={umbral_db}dB:d={dur_min}','-f','null','-']
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        salida = r.stderr
        inicios, finales = [], []
        for linea in salida.splitlines():
            if 'silence_start' in linea:
                try: inicios.append(float(linea.split('silence_start:')[1].strip()))
                except: pass
            elif 'silence_end' in linea:
                try:
                    parte = linea.split('silence_end:')[1].strip()
                    finales.append(float(parte.split('|')[0].strip()))
                except: pass
        # Centro de cada pausa = punto ideal de corte (en mitad del silencio)
        centros = []
        for i in range(min(len(inicios), len(finales))):
            centros.append((inicios[i] + finales[i]) / 2.0)
        return sorted(centros)
    except Exception:
        return []


def _ajustar_corte_a_silencio(t_objetivo, silencios, ventana=4.0):
    """Mueve un punto de corte al silencio real más cercano dentro de una ventana.
    Si no hay silencio cerca, devuelve el tiempo objetivo original (mejor no forzar)."""
    if not silencios:
        return t_objetivo
    candidatos = [s for s in silencios if abs(s - t_objetivo) <= ventana]
    if not candidatos:
        return t_objetivo
    return min(candidatos, key=lambda s: abs(s - t_objetivo))


def construir_audio_con_hooks(ruta_audio_in, ruta_audio_out, inserciones, duraciones_escenas,
                               dur_hook_inicial, carpeta, hook_inicial_presente, carpeta_marca=None):
    """
    Reconstruye el audio de narración insertando, en cada punto de hook, un tramo
    de silencio de duración = dur del hook (para que el audio NO pise el hook visual,
    y narración + video queden sincronizados).
    El hook visual trae su propio stinger en SU pista, así que aquí solo insertamos
    silencio en la narración (el stinger del clip suena durante ese silencio).

    IMPORTANTE: los puntos de corte se AJUSTAN al silencio real más cercano de la
    narración, para que el re-hook entre en una pausa natural (entre frases) y NO
    corte una palabra a la mitad.
    """
    try:
        # Guarda: si el audio de entrada no existe o es inválido, no se puede reconstruir
        if not os.path.exists(ruta_audio_in) or _dur(ruta_audio_in) < 0.5:
            return False
        # Puntos (en segundos del audio original) donde cortar e insertar silencio
        acum = []
        s = 0.0
        for d in duraciones_escenas:
            s += d
            acum.append(s)
        # Detectar los silencios REALES del audio para cortar en pausas naturales
        silencios = _detectar_silencios(ruta_audio_in)
        if silencios:
            print(f"   [HOOKS] {len(silencios)} pausas naturales detectadas para alinear re-hooks.")
        _acum_map = {i: acum[i] for i in range(len(acum))}  # escena -> tiempo de fin
        cortes = []  # (tiempo_corte, duracion_silencio)
        if hook_inicial_presente:
            cortes.append((0.0, dur_hook_inicial))  # silencio al inicio
        for ins in inserciones:
            i = ins["despues_de_escena"]
            if i < len(acum):
                t_objetivo = acum[i]
                # Ajustar el corte al silencio real más cercano (pausa entre frases)
                t_ajustado = _ajustar_corte_a_silencio(t_objetivo, silencios, ventana=4.0)
                cortes.append((t_ajustado, ins["dur"]))
        cortes.sort()
        if not cortes:
            import shutil; shutil.copy(ruta_audio_in, ruta_audio_out); return True

        dur_audio = _dur(ruta_audio_in)
        # Construir segmentos de narración entre cortes + silencios
        partes = []
        t_prev = 0.0
        idx = 0
        for (t_corte, dur_sil) in cortes:
            # Segmento de narración de t_prev a t_corte
            if t_corte > t_prev + 0.05:
                seg = os.path.join(carpeta, f"_au_seg_{idx}.wav")
                subprocess.run(['ffmpeg','-y','-i', ruta_audio_in,'-ss', str(t_prev),'-to', str(t_corte),
                                '-c:a','pcm_s16le','-ar','44100','-ac','2', seg],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if _clip_valido(seg, 0.05): partes.append(seg)
                idx += 1
            # Silencio del hook CON STINGER (el concat de video es mudo, así que
            # el sonido del hook debe ir aquí, en la pista de narración)
            sil = os.path.join(carpeta, f"_au_sil_{idx}.wav")
            # Generar stinger del tipo correspondiente y usarlo como "relleno" del hueco
            tipo_st = "whoosh"
            for _ins in inserciones:
                if abs((_acum_map.get(_ins["despues_de_escena"], -99)) - t_corte) < 0.01:
                    tipo_st = "whoosh" if _ins.get("formato") == "A" else "impact"
                    break
            _st_tmp = os.path.join(carpeta, f"_st_{idx}.wav")
            # Usa el stinger REAL del canal (stinger1/stinger2.mp3) si existe;
            # si no, genera el sintético como respaldo.
            _ok_st = _obtener_stinger_canal(carpeta_marca, tipo_st, dur_sil, _st_tmp)
            if _ok_st:
                sil = _st_tmp
            else:
                subprocess.run(['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=44100:cl=stereo',
                                '-t', str(dur_sil),'-c:a','pcm_s16le','-ar','44100','-ac','2', sil],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if _clip_valido(sil, 0.05): partes.append(sil)
            idx += 1
            t_prev = t_corte
        # Resto de narración
        if dur_audio > t_prev + 0.05:
            seg = os.path.join(carpeta, f"_au_seg_{idx}.wav")
            subprocess.run(['ffmpeg','-y','-i', ruta_audio_in,'-ss', str(t_prev),
                            '-c:a','pcm_s16le','-ar','44100','-ac','2', seg],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if _clip_valido(seg, 0.05): partes.append(seg)

        if len(partes) < 2:
            import shutil; shutil.copy(ruta_audio_in, ruta_audio_out); return True

        # Concatenar con el filtro concat de audio (más robusto que el demuxer para AAC)
        inputs = []
        for p in partes:
            inputs.extend(['-i', p])
        n = len(partes)
        filtro = "".join(f"[{k}:a]" for k in range(n)) + f"concat=n={n}:v=0:a=1[out]"
        cmd = ['ffmpeg','-y'] + inputs + ['-filter_complex', filtro, '-map','[out]',
               '-c:a','aac','-b:a','192k', ruta_audio_out]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for p in partes:
            try: os.remove(p)
            except: pass
        return _clip_valido(ruta_audio_out, 1.0)
    except Exception as e:
        print(f"   [HOOKS] Error audio: {e}")
        try:
            import shutil; shutil.copy(ruta_audio_in, ruta_audio_out)
        except: pass
        return False

# ═══════════ FIN MÓDULO DE HOOKS V2 ═══════════

def _lote_fue_cancelado():
    """Consulta a Render si el lote fue cancelado. Si es así, el worker debe
    limpiar su cola local en vez de seguir produciendo videos de un lote muerto."""
    try:
        r = requests.get(f"{RENDER_URL}/api/bot/lote_progreso", timeout=15)
        if r.status_code == 200:
            estado = r.json().get("estado_lote", "")
            return estado in ("cancelado", "inactivo")
    except Exception:
        pass
    return False

def _limpiar_cola_local(motivo=""):
    """Borra todos los ensamblajes pendientes de la cola local del worker."""
    import glob as _glob
    cola_local_dir = r"C:\NODO_PINPINELA\cola_local"
    borrados = 0
    try:
        if os.path.isdir(cola_local_dir):
            for archivo in _glob.glob(os.path.join(cola_local_dir, "*.json")):
                try:
                    os.remove(archivo)
                    borrados += 1
                except Exception:
                    pass
        if borrados:
            print(f"🧹 [LIMPIEZA] {borrados} ensamblaje(s) pendiente(s) borrados de la cola local. {motivo}")
    except Exception as e:
        print(f"⚠️ Error limpiando cola local: {e}")
    return borrados

def procesar():
    global _tareas_completadas  # FIX: Llamamos al registro local
    
    try:
        # PRIORIDAD: revisar la cola local (ensamblajes encolados por el propio worker).
        # Esto NO depende de Render ni de su /tmp efímero.
        import glob as _glob
        tarea = None
        cola_local_dir = r"C:\NODO_PINPINELA\cola_local"
        # Antes de tomar trabajo de la cola local: si el lote fue cancelado, NO
        # procesar ensamblajes viejos — limpiarlos para no producir videos de un
        # lote que el operador ya canceló.
        if os.path.isdir(cola_local_dir):
            _hay_pendientes = bool(_glob.glob(os.path.join(cola_local_dir, "*.json")))
            if _hay_pendientes and _lote_fue_cancelado():
                _limpiar_cola_local("Lote cancelado por el operador — no se producen videos viejos.")
        if os.path.isdir(cola_local_dir):
            locales = sorted(_glob.glob(os.path.join(cola_local_dir, "*.json")))
            if locales:
                archivo_local = locales[0]
                try:
                    with open(archivo_local, encoding="utf-8") as f:
                        tarea = json.load(f)
                    os.remove(archivo_local)
                    print(f"\n📦 [COLA LOCAL] Tomando ensamblaje encolado: {tarea.get('id')}")
                except Exception as e:
                    print(f"⚠️ Error leyendo cola local: {e}")
                    tarea = None

        if tarea is not None:
            data = {"hay_trabajo": True, "tarea": tarea}
        else:
            res = requests.post(
                f"{RENDER_URL}/api/nodo/polling",
                json={"nodo_id": "XEON_ASSEMBLER"},
                timeout=400
            )
            if res.status_code == 429:
                print("[CIRCUIT BREAKER] 429 en polling — pausando 60s...")
                time.sleep(60)
                return
            if res.status_code != 200:
                _registrar_error_render()
                return
            _resetear_errores_render()
            data = res.json()

        if data.get("hay_trabajo"):
            tarea    = data["tarea"]
            tarea_id = tarea["id"]
            
            # 🛑 FIX MAESTRO ANTI-BUCLE: 
            # Si el worker ya hizo esta tarea, la ignora y manda matar el proceso en el servidor.
            if tarea_id in _tareas_completadas:
                print(f"🛑 [BLOQUEO] Tarea {tarea_id} ya se completó localmente. Evitando bucle infinito...")
                try:
                    requests.post(f"{RENDER_URL}/api/nodo/tarea_completada", json={"tarea_id": tarea_id, "estado": "finalizado"}, timeout=10)
                except:
                    pass
                return
                
            _tareas_completadas.add(tarea_id)  # Registramos que ya empezamos a trabajarla
            
            tipo_tarea = tarea.get("tipo", "IMAGEN")

            # Avisar a Render que el worker está OCUPADO (evita solapamiento de órdenes)
            _worker_tomo_tarea[0] = True
            try:
                requests.post(f"{RENDER_URL}/api/nodo/worker_estado",
                              json={"ocupado": True, "tarea_actual": f"{tipo_tarea} {tarea_id[:8]}"}, timeout=10)
            except:
                pass

            # ══════════════════════════════════════════════════
            # RUTA 1: ENSAMBLAJE DE ALTA FIDELIDAD
            # ══════════════════════════════════════════════════
            if tipo_tarea == "ENSAMBLAJE":
                print(f"\n🎬 [ENSAMBLAJE V8.4.8] Iniciando Motor Híbrido Multicapa...")

                # Diagnóstico del video (se sube a la rama diagnostico al terminar)
                _diag = {
                    "id": tarea_id,
                    "marca": tarea.get("marca", "?"),
                    "formato": tarea.get("formato", "?"),
                    "tipo": "Largo" if ("16:9" in tarea.get("formato", "")) else "Short",
                    "inicio": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "hooks": {"frases_recibidas": len(tarea.get("hooks", []) or []), "insertados": 0, "activos": False},
                    "subtitulos": {"aplica": False, "bloques_habla": 0, "desplazado_por_hooks": False},
                    "paquete": {"generado": False, "respaldo": False},
                    "errores": [],
                }

                # PRE-FLIGHT: el ensamblaje necesita SD (imágenes) y VOZ. Si falta
                # alguno, abortar AHORA y no perder el trabajo largo.
                nodos_ok, motivo = verificar_nodos_criticos(necesita_sd=True, necesita_voz=True)
                if not nodos_ok:
                    print(f"🛑 [ENSAMBLAJE CANCELADO] {motivo}")
                    _diag["errores"].append(f"Pre-flight abortado: {motivo}")
                    subir_diagnostico_video(_diag)
                    _tareas_completadas.discard(tarea_id)  # permitir reintento cuando se reactiven los nodos
                    return

                texto_locucion = tarea.get("texto_locucion", "")
                marca_audio    = tarea.get("marca", "La Viuda")

                if not texto_locucion:
                    print("⚠️ No hay texto de locución en la tarea.")
                    return

                carpetas = [
                    os.path.join(CARPETA_LOCAL, d)
                    for d in os.listdir(CARPETA_LOCAL)
                    if os.path.isdir(os.path.join(CARPETA_LOCAL, d))
                ]
                if not carpetas:
                    return
                carpeta_reciente = max(carpetas, key=os.path.getmtime)

                ruta_formato = os.path.join(carpeta_reciente, "formato.txt")
                formato_ensamblaje = "9:16"
                if os.path.exists(ruta_formato):
                    with open(ruta_formato, "r") as f:
                        formato_ensamblaje = f.read().strip()

                es_largo_video = "16:9" in formato_ensamblaje
                w, h = (1024, 576) if es_largo_video else (576, 1024)

                _MAPA_CARPETA_ASSETS = {
                    "laesquinarandom": "Laesquina",
                    "filtradomx":      "Filtradomx",
                    "laviuda":         "La Viuda",
                    "monkygraff":      "Monkygraff",
                    "umbralalterno":   "Umbral Alterno",
                    "tuialista":       "TuIAlista",
                }
                _nombre_carpeta = _MAPA_CARPETA_ASSETS.get(marca_audio.lower().replace(" ", ""), marca_audio)
                carpeta_marca_assets = os.path.join(CARPETA_ASSETS, _nombre_carpeta)
                ruta_musica_fondo    = os.path.join(carpeta_marca_assets, "musica_fondo.mp3")
                ruta_intro_dinamico  = os.path.join(carpeta_marca_assets, "intro_169.mp4" if es_largo_video else "intro_916.mp4")
                ruta_outro_dinamico  = os.path.join(carpeta_marca_assets, "outro_169.mp4" if es_largo_video else "outro_916.mp4")
                ruta_audio           = os.path.join(carpeta_reciente, "locucion.mp3")

                print("🎙️ Generando audio con motor de voz local (XTTS)...")
                try:
                    import sys
                    sys.path.insert(0, "C:\\NODO_PINPINELA")
                    from voice_local import generar_audio_local
                    # Corregir pronunciación SOLO para la voz (el texto original se
                    # conserva intacto para los subtítulos). Arregla palabras que XTTS
                    # descompone (explica→espica, Washington→vasinton, amiga→amilla, etc.)
                    texto_para_voz = _corregir_pronunciacion(texto_locucion)
                    resultado = generar_audio_local(texto_para_voz, marca_audio, ruta_audio)
                    if resultado:
                        ruta_audio = resultado
                        print(f"✅ Audio local generado: {ruta_audio}")
                    else:
                        print("⚠️ Error en voz local.")
                        return
                except Exception as e:
                    print(f"⚠️ Error voz local: {e}")
                    return

                archivos_escenas = sorted([
                    f for f in os.listdir(carpeta_reciente)
                    if f.startswith('escena_') and (f.endswith('.png') or f.endswith('.mp4'))
                ])
                num_escenas = len(archivos_escenas)
                if num_escenas == 0:
                    print("⚠️ No hay escenas PNG o MP4 en la carpeta.")
                    return

                duracion_audio = _obtener_duracion_audio(ruta_audio, texto_locucion, marca_audio)
                fps = 30

                def calcular_duraciones(num_imgs, dur_total, target_fps=30):
                    pesos = []
                    for i in range(num_imgs):
                        pos  = i / max(num_imgs - 1, 1)
                        peso = 0.7 + 0.6 * (1 - abs(pos - 0.5) * 2)
                        pesos.append(peso)
                    total_pesos = sum(pesos)

                    total_frames = int(dur_total * target_fps)
                    frames_asignados = 0
                    duraciones_finales = []

                    for i in range(num_imgs):
                        if i == num_imgs - 1:
                            frames_escena = total_frames - frames_asignados
                        else:
                            frames_escena = int(total_frames * (pesos[i] / total_pesos))

                        frames_asignados += frames_escena
                        duraciones_finales.append(frames_escena / target_fps)

                    return duraciones_finales

                def alinear_duraciones_a_silencios(duraciones, ruta_audio, target_fps=30):
                    """Ajusta los límites de cada escena al silencio (pausa) real más
                    cercano del audio, para que cada escena termine donde termina su
                    frase — así los re-hooks entran en pausas naturales, no a media
                    palabra. Si no hay silencios detectables, deja las duraciones tal cual."""
                    silencios = _detectar_silencios(ruta_audio)
                    if not silencios or len(duraciones) < 2:
                        return duraciones
                    # Límites acumulados originales (fin de cada escena)
                    limites = []
                    s = 0.0
                    for d in duraciones:
                        s += d
                        limites.append(s)
                    dur_total = limites[-1]
                    # Ajustar cada límite interno (no el último) al silencio más cercano
                    nuevos_limites = []
                    usados = set()
                    for i, lim in enumerate(limites[:-1]):
                        cand = _ajustar_corte_a_silencio(lim, silencios, ventana=3.5)
                        # Evitar que dos escenas caigan en el mismo silencio o se crucen
                        prev = nuevos_limites[-1] if nuevos_limites else 0.0
                        if cand <= prev + 0.5 or cand in usados:
                            cand = lim  # mantener el original si el ajuste colapsa
                        usados.add(cand)
                        nuevos_limites.append(cand)
                    nuevos_limites.append(dur_total)  # el último siempre = fin del audio
                    # Reconvertir límites a duraciones
                    nuevas_dur = []
                    prev = 0.0
                    for lim in nuevos_limites:
                        nuevas_dur.append(max(0.1, lim - prev))
                        prev = lim
                    return nuevas_dur

                duraciones_escenas = calcular_duraciones(num_escenas, duracion_audio, fps)
                # Alinear a las pausas reales del audio (clave para que los re-hooks
                # entren entre frases y no corten palabras)
                try:
                    duraciones_escenas = alinear_duraciones_a_silencios(
                        duraciones_escenas, ruta_audio, fps)
                    print(f"   [SYNC] Duraciones de escena alineadas a las pausas naturales del audio.")
                except Exception as _e_align:
                    print(f"   [SYNC] No se pudieron alinear (se usan duraciones base): {_e_align}")

                efectos_por_tipo = {
                    # Solo efectos DINÁMICOS/AGRESIVOS — se eliminaron los lentos
                    # (push_in_slow, pan_*_slow, drift_diagonal) que dejaban la imagen
                    # casi congelada y mataban el dinamismo del video.
                    'tension':    ['ken_burns_agresivo', 'punch_in', 'slide_l', 'slide_r', 'zoom_punch', 'snap_zoom', 'shake_zoom', 'whip_pan', 'rush_diagonal'],
                    'impacto':    ['zoom_punch', 'flash_cut', 'snap_zoom', 'punch_in', 'shake_zoom', 'fast_push', 'pulse_punch'],
                    'transicion': ['slide_l', 'slide_r', 'slide_up', 'ken_burns_diagonal', 'zoom_punch', 'snap_zoom', 'whip_pan', 'rush_diagonal', 'fast_push'],
                }

                def detectar_tipo_escena(texto):
                    texto = texto.lower()
                    palabras_impacto = [
                        'entonces', 'de repente', 'pero', 'jamás', 'nunca', 'murió',
                        'desapareció', 'encontraron', 'revelación', 'encontró',
                        'descubrió', 'confesó', 'ataque', 'golpe', 'disparo'
                    ]
                    palabras_tension = [
                        'silencio', 'oscuridad', 'nadie', 'solo', 'espera', 'escucha',
                        'sientes', 'sabes', 'algo', 'sombra', 'frío', 'miedo',
                        'extraño', 'raro', 'oculto', 'susurro'
                    ]
                    score_i = sum(1 for p in palabras_impacto if p in texto)
                    score_t = sum(1 for p in palabras_tension  if p in texto)
                    if score_i > score_t: return 'impacto'
                    if score_t > 0:       return 'tension'
                    return 'transicion'

                ultimo_efecto = [None]

                def elegir_efecto(tipo):
                    opciones = efectos_por_tipo[tipo][:]
                    if ultimo_efecto[0] in opciones and len(opciones) > 1:
                        opciones = [e for e in opciones if e != ultimo_efecto[0]]
                    efecto = random.choice(opciones)
                    ultimo_efecto[0] = efecto
                    return efecto

                def construir_filtro_movimiento(efecto, total_frames, fps, w, h):
                    es_largo = w > h
                    dur_s = total_frames / fps

                    if efecto == 'zoom_punch':
                        # Zoom rápido al 170% en 0.3s — golpe visual de impacto
                        punch_frames = max(1, int(fps * 0.3))
                        return (
                            f"zoompan=z='if(lte(on,{punch_frames}),1.0+0.7*(on/{punch_frames}),1.70)'"
                            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'shake_zoom':
                        # Zoom con SACUDIDA rápida (tipo cámara nerviosa) — muy agresivo
                        dist = 0.06 if es_largo else 0.05
                        return (
                            f"zoompan=z='1.55+0.10*sin(on/12)'"
                            f":x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/7)'"
                            f":y='ih/2-(ih/zoom/2)+(ih*{dist})*cos(on/5)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'fast_push':
                        # Empuje RÁPIDO y constante hacia el centro — energía creciente
                        return (
                            f"zoompan=z='1.10+1.0*(on/{total_frames})'"
                            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'whip_pan':
                        # Barrido lateral RÁPIDO (whip) — recorre la imagen con fuerza
                        dist = 0.28 if es_largo else 0.24
                        return (
                            f"zoompan=z='1.50+0.10*sin(on/40)'"
                            f":x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/35)'"
                            f":y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'pulse_punch':
                        # Latido rápido de zoom (in-out marcado) — ritmo agresivo
                        return (
                            f"zoompan=z='1.45+0.18*sin(on/18)'"
                            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'rush_diagonal':
                        # Recorrido diagonal RÁPIDO con zoom firme — mucho dinamismo
                        dist = 0.24 if es_largo else 0.20
                        return (
                            f"zoompan=z='1.55+0.10*sin(on/45)'"
                            f":x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/38)'"
                            f":y='ih/2-(ih/zoom/2)+(ih*{dist*0.8:.2f})*cos(on/42)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'flash_cut':
                        # Ken Burns agresivo + flash blanco al final (eq brightness, sin geq)
                        t_flash = max(0.05, dur_s - 0.1)
                        return (
                            f"zoompan=z='1.60+0.10*sin(on/70)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                            f",eq=brightness='if(between(t,{t_flash:.3f},{dur_s:.3f}),0.9,0)':eval=frame"
                        )
                    elif efecto == 'ken_burns_agresivo':
                        # Zoom 1.80x con movimiento amplio — muy cinematográfico
                        dist = 0.18 if es_largo else 0.15
                        return (
                            f"zoompan=z='1.80+0.15*sin(on/80)'"
                            f":x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/110)'"
                            f":y='ih/2-(ih/zoom/2)+(ih*{dist*0.6:.2f})*cos(on/130)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'ken_burns_diagonal':
                        # Movimiento diagonal — variedad visual
                        dist = 0.14 if es_largo else 0.12
                        return (
                            f"zoompan=z='1.60+0.08*cos(on/90)'"
                            f":x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/100)'"
                            f":y='ih/2-(ih/zoom/2)+(ih*{dist:.2f})*sin(on/100)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'vignette_pulse':
                        # (Acelerado) Pan más marcado + vignette pulsante de urgencia
                        dist = 0.16 if es_largo else 0.13
                        return (
                            f"zoompan=z='1.55+0.06*sin(on/50)':x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/60)'"
                            f":y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'rgb_glitch':
                        # Zoom firme sin vibración (la separación RGB se aplica aparte como glitch_fx)
                        return (
                            f"zoompan=z='1.40+0.05*(on/{total_frames})':x='iw/2-(iw/zoom/2)'"
                            f":y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'snap_zoom':
                        # Zoom rápido y limpio (sin vibración) — golpe de atención profesional
                        snap_frames = max(1, int(fps * 0.4))
                        return (
                            f"zoompan=z='if(lte(on,{snap_frames}),1.0+0.5*(on/{snap_frames}),1.50)'"
                            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'punch_in':
                        # Acercamiento progresivo constante — tensión creciente, suave
                        return (
                            f"zoompan=z='1.20+0.50*(on/{total_frames})'"
                            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'push_in_slow':
                        # (Acelerado) Empuje firme hacia el centro — más dinámico que antes
                        return (
                            f"zoompan=z='1.15+0.65*(on/{total_frames})'"
                            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'drift_diagonal':
                        # (Acelerado) Deriva diagonal con más recorrido y zoom marcado
                        dist = 0.20 if es_largo else 0.17
                        return (
                            f"zoompan=z='1.45+0.12*sin(on/55)'"
                            f":x='iw/2-(iw/zoom/2)+(iw*{dist})*(on/{total_frames})'"
                            f":y='ih/2-(ih/zoom/2)+(ih*{dist*0.7:.2f})*(on/{total_frames})'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'pan_l_slow':
                        # (Acelerado) Paneo izquierda más rápido y amplio
                        dist = 0.20 if es_largo else 0.17
                        return f"zoompan=z='1.55+0.08*sin(on/60)':x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/65)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'pan_r_slow':
                        # (Acelerado) Paneo derecha más rápido y amplio
                        dist = 0.20 if es_largo else 0.17
                        return f"zoompan=z='1.55+0.08*cos(on/60)':x='iw/2-(iw/zoom/2)+(iw*{dist})*cos(on/65)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'slide_l':
                        dist = 0.16 if es_largo else 0.14
                        return f"zoompan=z=1.55:x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/90)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'slide_r':
                        dist = 0.16 if es_largo else 0.14
                        return f"zoompan=z=1.55:x='iw/2-(iw/zoom/2)+(iw*{dist})*cos(on/90)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'slide_up':
                        dist = 0.16 if es_largo else 0.14
                        return f"zoompan=z=1.55:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+(ih*{dist})*sin(on/100)':d={total_frames}:fps={fps}:s={w}x{h}"
                    else:
                        return f"zoompan=z=1.50:x='iw/2-(iw/zoom/2)+(iw*0.10)*sin(on/100)':y='ih/2-(ih/zoom/2)+(ih*0.10)*cos(on/100)':d={total_frames}:fps={fps}:s={w}x{h}"

                escenas_data   = tarea.get("escenas", [])
                textos_escenas = [e.get("texto_locucion", "") for e in escenas_data] if escenas_data else []
                clips_temp     = []
                
                es_cartoon_fx = (marca_audio.lower() in ["la esquina random", "laesquinarandom"])

                UMBRAL_SUB_EFECTOS = 4.0

                print(f"⚙️ Procesando {num_escenas} matrices visuales con CPU Xeon...")

                # ¿Está vivo el servidor DepthFlow del PC GPU? (verifica una vez)
                usar_parallax_global = _depthflow_disponible()

                # Si vamos a usar parallax, liberar la VRAM de SD primero.
                # Esto resuelve el error 500: DepthFlow necesita la VRAM que SD ocupa.
                if usar_parallax_global:
                    _liberar_vram_sd()

                _rnd_para = random.Random(str(tarea.get("id", "")) + "parallax")

                for i, archivo in enumerate(archivos_escenas):
                    path_origen = os.path.join(carpeta_reciente, archivo).replace("\\", "/")
                    path_clip   = os.path.join(carpeta_reciente, f"clip_{i:02d}.mp4")

                    texto_escena  = textos_escenas[i] if i < len(textos_escenas) else ""
                    tipo   = detectar_tipo_escena(texto_escena)
                    efecto = elegir_efecto(tipo)

                    dur_original = duraciones_escenas[i]
                    dur_exacta   = dur_original

                    if i == num_escenas - 1:
                        dur_exacta += 1.0  

                    total_frames = int(round(dur_exacta * fps)) 

                    # ── DECISIÓN PARALLAX: algunas escenas usan DepthFlow (2.5D real) ──
                    # Se decide por escena, determinista (mismo video = mismo patrón).
                    # Las escenas de "impacto" se quedan con zoompan (llevan glitch rápido).
                    parallax_ok = False
                    if (usar_parallax_global and archivo.endswith('.png')
                            and tipo != 'impacto'
                            and _rnd_para.randint(1, 100) <= DEPTHFLOW_RATIO):
                        parallax_ok = _pedir_parallax(
                            path_origen, path_clip, marca_audio, i,
                            dur_exacta, fps, w, h
                        )
                        if parallax_ok:
                            # Validar el clip parallax recibido; si está corrupto, cae a zoompan
                            if _clip_es_valido(path_clip, dur_exacta):
                                clips_temp.append(path_clip)
                                continue
                            else:
                                print(f"   [DEPTHFLOW] clip {i} inválido — zoompan fallback")
                                parallax_ok = False

                    if es_cartoon_fx:
                        glitch_fx = ""
                    else:
                        if tipo == 'impacto':
                            t_glitch = max(0.1, dur_original - 0.2)
                            t_negate = max(0.15, dur_original - 0.1)
                            glitch_fx = (
                                f",rgbashift=rh=20:bv=20:enable='between(t,{t_glitch:.3f},{dur_exacta:.3f})'"
                                f",negate=enable='between(t,{t_negate:.3f},{dur_exacta:.3f})'"
                            )
                        elif tipo == 'tension':
                            t_glitch  = max(0.1, dur_original - 0.3)
                            glitch_fx = f",rgbashift=rh=8:bv=8:enable='between(t,{t_glitch:.3f},{dur_exacta:.3f})'"
                        else:
                            glitch_fx = ""

                    if archivo.endswith('.png') and dur_exacta > UMBRAL_SUB_EFECTOS:
                        # Cortes cada ~2.2s (más frecuentes = más dinámico), hasta 14 sub-clips
                        num_subs = max(2, min(int(dur_exacta / 2.2), 14))
                        dur_sub = dur_exacta / num_subs

                        efectos_sub = [efecto]
                        for _ in range(num_subs - 1):
                            efectos_sub.append(elegir_efecto(tipo))

                        sub_clips = []
                        escala_previa = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                        for k, efx in enumerate(efectos_sub):
                            sub_path    = os.path.join(carpeta_reciente, f"clip_{i:02d}_s{k}.mp4")
                            sub_frames  = int(round(dur_sub * fps))
                            mf_sub      = construir_filtro_movimiento(efx, sub_frames, fps, w, h)
                            glitch_sub = glitch_fx if k == num_subs - 1 else ""
                            # Fade de entrada rápido en cada corte = transición limpia y marcada
                            fade_in = "fade=t=in:st=0:d=0.12"
                            vf_sub = f"{escala_previa}{mf_sub},{fade_in},noise=alls=4:allf=t+u,vignette=PI/4,setpts=PTS-STARTPTS{glitch_sub}"
                            cmd_sub = [
                                'ffmpeg', '-y', '-i', path_origen,
                                '-vf', vf_sub, '-t', str(dur_sub),
                                '-c:v', 'libx264', '-preset', 'ultrafast',
                                '-threads', '0', '-pix_fmt', 'yuv420p', '-r', str(fps), sub_path
                            ]
                            subprocess.run(cmd_sub, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            sub_clips.append(sub_path)

                        list_sub = os.path.join(carpeta_reciente, f"subs_{i:02d}.txt")
                        with open(list_sub, "w") as flist:
                            for sc in sub_clips:
                                flist.write(f"file '{sc.replace(chr(92), '/')}'\n")
                        cmd_concat_sub = [
                            'ffmpeg', '-y', '-fflags', '+genpts',
                            '-f', 'concat', '-safe', '0', '-i', list_sub,
                            '-c:v', 'libx264', '-preset', 'ultrafast',
                            '-threads', '0', '-pix_fmt', 'yuv420p',
                            '-vsync', 'cfr', '-r', str(fps), path_clip
                        ]
                        subprocess.run(cmd_concat_sub, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        for sc in sub_clips:
                            try: os.remove(sc)
                            except: pass
                        try: os.remove(list_sub)
                        except: pass

                        # Validar el clip; si está corrupto, regenerar simple
                        if not _clip_es_valido(path_clip, dur_exacta):
                            print(f"   [FIX] clip_{i:02d} corrupto — regenerando simple...")
                            _generar_clip_simple(path_origen, path_clip, dur_exacta, w, h, fps)

                        clips_temp.append(path_clip)
                        print(f"   [OK] Escena {i+1} (SD-Dinamica {num_subs}x) — tipo:{tipo} efectos:{','.join(efectos_sub)}")
                        continue

                    if archivo.endswith('.png'):
                        escala_previa = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                        mf = construir_filtro_movimiento(efecto, total_frames, fps, w, h)
                        vf_string = f"{escala_previa}{mf},fade=t=in:st=0:d=0.1,noise=alls=5:allf=t+u,vignette=PI/4,setpts=PTS-STARTPTS{glitch_fx}"
                        cmd_scene = [
                            'ffmpeg', '-y', '-i', path_origen,
                            '-vf', vf_string, '-t', str(dur_exacta),
                            '-c:v', 'libx264', '-preset', 'ultrafast',
                            '-threads', '0', '-pix_fmt', 'yuv420p', '-r', str(fps), path_clip
                        ]
                    else:
                        # Pexels (video): forzar duración EXACTA frame-perfect, igual que
                        # las imágenes SD. Sin esto, recortar un video con -t deja
                        # milisegundos de más/menos que se ACUMULAN escena tras escena
                        # y desfasan los re-hooks de la voz (el bug de Monkygraff/FiltradoMX).
                        # 'trim' corta exacto al segundo pedido, fps fija el ritmo constante,
                        # y tpad rellena si el recorte quedó corto. Solo afecta a Pexels.
                        _frames_exactos = int(round(dur_exacta * fps))
                        vf_string = (
                            f"fade=t=in:st=0:d=0.1,noise=alls=5:allf=t+u,vignette=PI/4,"
                            f"setpts=PTS-STARTPTS,fps={fps},"
                            f"trim=end_frame={_frames_exactos},"
                            f"tpad=stop_mode=clone:stop=-1,trim=end_frame={_frames_exactos},"
                            f"setpts=PTS-STARTPTS{glitch_fx}"
                        )
                        cmd_scene = [
                            'ffmpeg', '-y', '-stream_loop', '-1', '-i', path_origen,
                            '-vf', vf_string, '-frames:v', str(_frames_exactos),
                            '-c:v', 'libx264', '-preset', 'ultrafast',
                            '-threads', '0', '-pix_fmt', 'yuv420p',
                            '-vsync', 'cfr', '-r', str(fps), path_clip
                        ]

                    subprocess.run(cmd_scene, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    # Validar el clip; si está corrupto, regenerar simple
                    if not _clip_es_valido(path_clip, dur_exacta):
                        print(f"   [FIX] clip_{i:02d} corrupto — regenerando simple...")
                        _generar_clip_simple(path_origen, path_clip, dur_exacta, w, h, fps)
                    clips_temp.append(path_clip)
                    print(f"   [OK] Escena {i+1} ({'SD' if archivo.endswith('.png') else 'Pexels'}) — tipo:{tipo} efecto:{efecto}")

                # ══════════ SINCRONÍA REAL ══════════
                # Medir la duración REAL de cada clip ya construido. Los clips de Pexels
                # y los de SD pueden no durar exactamente lo calculado (redondeos de
                # frames, +1s del último, stream_loop). Si los hooks y el audio se
                # cortaran según las duraciones CALCULADAS, el error se acumula y el
                # hook visual se desfasa de la pausa de la voz (el bug de Monkygraff).
                # Usando las duraciones REALES, hook visual y audio quedan sincronizados.
                _dur_reales = []
                for _ic in range(len(clips_temp)):
                    _d = _dur(clips_temp[_ic])
                    _dur_reales.append(_d if _d and _d > 0 else duraciones_escenas[_ic] if _ic < len(duraciones_escenas) else 3.0)
                if _dur_reales and len(_dur_reales) == len(clips_temp):
                    duraciones_escenas = _dur_reales
                    print(f"   [SYNC] Duraciones reales de {len(_dur_reales)} clips medidas (hooks y audio se alinean a ellas).")

                # ══════════ HOOKS DE RETENCIÓN (integrados al pipeline) ══════════
                # Se insertan ENTRE escenas (límites naturales). Reconstruyen audio
                # y recalculan subtítulos para mantener sincronía total.
                _hook_inicial_dur = 0.0
                _hook_inserciones = []
                _hooks_activos = False
                _ruta_audio_original = ruta_audio  # audio SIN hooks (para subtítulos limpios)
                try:
                    _hooks_frases = tarea.get("hooks", []) or []
                    _hooks_frases = [str(x).strip() for x in _hooks_frases if x and str(x).strip()]
                    if _hooks_frases and len(clips_temp) >= 2:
                        _es_short_hk = not es_largo_video
                        _frase_ini, _hook_inserciones = planificar_hooks(
                            len(clips_temp), duraciones_escenas, _hooks_frases,
                            es_short=_es_short_hk, dur_hook=2.6, marca=marca_audio
                        )
                        # Imágenes de escena disponibles (para teasers)
                        _imgs_hk = [
                            os.path.join(carpeta_reciente, f).replace("\\", "/")
                            for f in sorted(os.listdir(carpeta_reciente))
                            if f.startswith("escena_") and f.endswith(".png")
                        ]
                        _img_def = _imgs_hk[0] if _imgs_hk else (
                            os.path.join(carpeta_reciente, archivos_escenas[0]) if archivos_escenas else None)

                        # 1. Hook inicial (clip al frente) — duración según el canal
                        _cfg_hk = _config_hooks(marca_audio)
                        _dur_ini_canal = _cfg_hk["dur_inicial"]
                        nuevos_clips = []
                        if _frase_ini and _img_def and os.path.exists(_img_def):
                            _hk_ini = os.path.join(carpeta_reciente, "_hook_inicial.mp4")
                            _r = generar_clip_hook(_frase_ini, _img_def, _hk_ini, w, h, fps,
                                                   carpeta_reciente, PIL_DISPONIBLE, FUENTES_WINDOWS,
                                                   formato="A", dur=_dur_ini_canal)
                            if _r:
                                nuevos_clips.append(_r)
                                _hook_inicial_dur = _dur_ini_canal

                        # 2. Reconstruir clips_temp intercalando re-hooks tras las escenas indicadas
                        _ins_por_escena = {ins["despues_de_escena"]: ins for ins in _hook_inserciones}
                        _rnd_img = random.Random("hkimg")
                        for _idx_c, _clip in enumerate(clips_temp):
                            nuevos_clips.append(_clip)
                            if _idx_c in _ins_por_escena:
                                _ins = _ins_por_escena[_idx_c]
                                _img_teaser = _rnd_img.choice(_imgs_hk) if _imgs_hk else _img_def
                                if _img_teaser and os.path.exists(_img_teaser):
                                    _hk = os.path.join(carpeta_reciente, f"_rehook_{_idx_c:02d}.mp4")
                                    _r = generar_clip_hook(_ins["frase"], _img_teaser, _hk, w, h, fps,
                                                           carpeta_reciente, PIL_DISPONIBLE, FUENTES_WINDOWS,
                                                           formato=_ins["formato"], dur=_ins["dur"])
                                    if _r:
                                        nuevos_clips.append(_r)

                        if len(nuevos_clips) > len(clips_temp):
                            clips_temp = nuevos_clips
                            _hooks_activos = True
                            # 3. Reconstruir el audio con los silencios de los hooks
                            _audio_hk = os.path.join(carpeta_reciente, "locucion_hooks.m4a")
                            if construir_audio_con_hooks(
                                ruta_audio, _audio_hk, _hook_inserciones, duraciones_escenas,
                                _hook_inicial_dur, carpeta_reciente,
                                hook_inicial_presente=(_hook_inicial_dur > 0),
                                carpeta_marca=carpeta_marca_assets
                            ):
                                ruta_audio = _audio_hk
                                duracion_audio = _dur(_audio_hk)
                            print(f"🪝 HOOKS: 1 inicial + {len(_hook_inserciones)} re-hooks integrados (entre escenas, audio resincronizado)")
                            _diag["hooks"]["insertados"] = len(_hook_inserciones) + (1 if _hook_inicial_dur > 0 else 0)
                            _diag["hooks"]["activos"] = True
                except Exception as _e_hk:
                    print(f"   [HOOKS] Omitidos por error (video intacto): {_e_hk}")
                    _hooks_activos = False
                    _diag["errores"].append(f"Hooks omitidos: {str(_e_hk)[:100]}")

                filtro_sub = ""
                if not es_largo_video:
                    _diag["subtitulos"]["aplica"] = True
                    escenas_texto = tarea.get("escenas_texto", [])
                    # SINCRONÍA CORRECTA: generar el SRT sobre el audio ORIGINAL (solo
                    # locución real, sin los stingers de los hooks que confunden al
                    # detector de bloques de habla). Luego, si hubo hooks, desplazar los
                    # tiempos del SRT para compensar los silencios insertados.
                    _dur_original = _obtener_duracion_audio_simple(_ruta_audio_original)
                    ruta_srt, _num_bloques = _generar_subtitulos_shorts(
                        _ruta_audio_original, texto_locucion, escenas_texto, marca_audio,
                        carpeta_reciente, _dur_original
                    )
                    _diag["subtitulos"]["bloques_habla"] = _num_bloques
                    if ruta_srt and os.path.exists(ruta_srt) and _hooks_activos and (_hook_inserciones or _hook_inicial_dur > 0):
                        _srt_shift = ruta_srt.replace(".srt", "_sync.srt")
                        if recalcular_srt(ruta_srt, _srt_shift, _hook_inserciones,
                                          duraciones_escenas, _hook_inicial_dur):
                            ruta_srt = _srt_shift
                            _diag["subtitulos"]["desplazado_por_hooks"] = True
                            print(f"   [SUBS] Tiempos desplazados para los hooks (sincronía mantenida).")
                    if ruta_srt and os.path.exists(ruta_srt):
                        sub_path = ruta_srt.replace('\\', '/').replace(':', '\\:')
                        filtro_sub = (
                            f"subtitles='{sub_path}':force_style='"
                            f"Alignment=10,FontSize=18,MarginV=0,Bold=1,"
                            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                            f"BackColour=&H80000000,BorderStyle=4,Outline=2,Shadow=1'"
                        )
                else:
                    print("📝 Video largo (16:9) — subtítulos desactivados.")

                print("🔗 FASE 1: Ensamblando cuerpo principal...")

                # VALIDACIÓN FINAL: revisar cada clip y regenerar los corruptos
                # antes de armar la lista de concat (evita que el concat muera)
                _suma_clips = 0.0
                for _ci, _clip in enumerate(clips_temp):
                    _es_hook_clip = ("_hook" in os.path.basename(_clip) or "_rehook" in os.path.basename(_clip))
                    if not _clip_es_valido(_clip):
                        if _es_hook_clip:
                            # Un clip de hook corrupto se descarta (no rompe el video)
                            print(f"   [FIX] clip de hook ilegible — se omite")
                            continue
                        print(f"   [FIX] clip_{_ci:02d} ilegible en validación final — regenerando...")
                        # Mapear el índice real de escena (descontando los hooks previos)
                        _idx_escena = len([c for c in clips_temp[:_ci]
                                           if "_hook" not in os.path.basename(c) and "_rehook" not in os.path.basename(c)])
                        _dur_esp = duraciones_escenas[_idx_escena] if _idx_escena < len(duraciones_escenas) else None
                        _dur_regen = _dur_esp if _dur_esp else 5.0
                        _origen_regen = (os.path.join(carpeta_reciente, archivos_escenas[_idx_escena])
                                         if _idx_escena < len(archivos_escenas) else _clip)
                        _generar_clip_simple(_origen_regen, _clip, _dur_regen, w, h, fps)
                    try:
                        _rr = subprocess.run(
                            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                             '-of', 'csv=p=0', _clip],
                            capture_output=True, text=True
                        )
                        _suma_clips += float(_rr.stdout.strip())
                    except Exception:
                        pass
                print(f"   [DIAG] {len(clips_temp)} clips suman {_suma_clips:.1f}s | audio: {duracion_audio:.1f}s")

                list_file = os.path.join(carpeta_reciente, "concat_list.txt")
                with open(list_file, "w") as f:
                    for clip in clips_temp:
                        safe = clip.replace('\\', '/')
                        f.write(f"file '{safe}'\n")


                ruta_base       = os.path.join(carpeta_reciente, "paso1_base.mp4")
                ruta_con_musica = os.path.join(carpeta_reciente, "paso2_musica.mp4")
                ruta_final      = os.path.join(carpeta_reciente, "00_FINAL_EXTREME_DYNAMICS.mp4")

                filtro_vf_concat = filtro_sub if filtro_sub else "setpts=N/FRAME_RATE/TB"
                ruta_video_mudo = os.path.join(carpeta_reciente, "video_concat_mudo.mp4")

                # PASO 1A: concatenar clips a video mudo regenerando timestamps (+genpts)
                # +igndts e ignore_errors hacen el concat tolerante a clips problemáticos
                cmd_concat = [
                    'ffmpeg', '-y', '-fflags', '+genpts+igndts', '-err_detect', 'ignore_err',
                    '-f', 'concat', '-safe', '0', '-i', list_file,
                    '-vf', filtro_vf_concat,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-threads', '0', '-crf', '22',
                    '-force_key_frames', 'expr:gte(t,n_forced*4)', '-pix_fmt', 'yuv420p',
                    '-an', '-vsync', 'cfr', '-r', str(fps),
                    ruta_video_mudo
                ]
                subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                # DIAGNÓSTICO: duración del video concatenado mudo
                try:
                    _rrm = subprocess.run(
                        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                         '-of', 'csv=p=0', ruta_video_mudo],
                        capture_output=True, text=True
                    )
                    print(f"   [DIAG] video_concat_mudo dura: {float(_rrm.stdout.strip()):.1f}s (esperado ~{_suma_clips:.1f}s)")
                except Exception as _e:
                    print(f"   [DIAG] video_mudo ILEGIBLE: {_e}")

                # PASO 1B: muxear audio sobre el video, extendiendo el video si el
                # audio es más largo (congela último frame) para NO cortar la narración
                _dur_video_mudo = 0.0
                try:
                    _rv = subprocess.run(
                        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                         '-of', 'csv=p=0', ruta_video_mudo],
                        capture_output=True, text=True)
                    _dur_video_mudo = float(_rv.stdout.strip())
                except Exception:
                    pass

                if duracion_audio > _dur_video_mudo + 0.3 and _dur_video_mudo > 0:
                    # El audio es más largo: extender video congelando último frame
                    _falta = duracion_audio - _dur_video_mudo
                    ruta_video_ext = os.path.join(carpeta_reciente, "video_ext.mp4")
                    cmd_pad = [
                        'ffmpeg', '-y', '-i', ruta_video_mudo,
                        '-vf', f"tpad=stop_mode=clone:stop_duration={_falta:.2f}",
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22',
                        '-pix_fmt', 'yuv420p', '-r', str(fps), ruta_video_ext
                    ]
                    subprocess.run(cmd_pad, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if _clip_es_valido(ruta_video_ext):
                        try: os.remove(ruta_video_mudo)
                        except Exception: pass
                        ruta_video_mudo = ruta_video_ext
                        print(f"   [FIX] Video extendido +{_falta:.1f}s para cubrir narración completa")
                elif _dur_video_mudo > duracion_audio + 0.3 and duracion_audio > 0:
                    # El video es más largo (p.ej. por los clips de hook): extender el
                    # audio con silencio para que audio y video queden EXACTAMENTE parejos
                    _falta_a = _dur_video_mudo - duracion_audio
                    ruta_audio_ext = os.path.join(carpeta_reciente, "audio_ext.m4a")
                    cmd_pad_a = [
                        'ffmpeg', '-y', '-i', ruta_audio.replace("\\", "/"),
                        '-af', f"apad=pad_dur={_falta_a:.2f}",
                        '-c:a', 'aac', '-b:a', '192k', ruta_audio_ext
                    ]
                    subprocess.run(cmd_pad_a, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if _clip_valido(ruta_audio_ext, 1.0):
                        ruta_audio = ruta_audio_ext
                        duracion_audio = _dur(ruta_audio_ext)
                        print(f"   [FIX] Audio extendido +{_falta_a:.1f}s para igualar video (hooks)")

                # VALIDACIÓN: asegurar que el audio de narración existe y es válido
                # ANTES de pegarlo. Si falta, el video saldría mudo (bug TuIALista).
                _audio_ok = ruta_audio and os.path.exists(ruta_audio) and _clip_valido(ruta_audio, 0.5)
                if not _audio_ok:
                    print(f"   [⚠️ AUDIO] La narración NO existe o es inválida: {ruta_audio}")
                    _diag.setdefault("errores", []).append(f"Audio de narracion ausente antes del merge: {ruta_audio}")

                cmd_merge = [
                    'ffmpeg', '-y',
                    '-i', ruta_video_mudo,
                    '-i', ruta_audio.replace("\\", "/"),
                    '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    ruta_base
                ]
                _r_merge = subprocess.run(cmd_merge, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                # VALIDACIÓN: confirmar que el video resultante TIENE pista de audio
                _tiene_audio = False
                try:
                    _chk = subprocess.run(
                        ['ffprobe', '-v', 'error', '-select_streams', 'a',
                         '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', ruta_base],
                        capture_output=True, text=True)
                    _tiene_audio = 'audio' in _chk.stdout
                except Exception:
                    pass
                if not _tiene_audio:
                    print(f"   [⚠️ AUDIO] El video tras el merge quedó SIN pista de audio.")
                    if _r_merge.stderr:
                        print(f"   [⚠️ AUDIO] FFmpeg: {_r_merge.stderr[-300:]}")
                    _diag.setdefault("errores", []).append("Video sin pista de audio tras merge")
                else:
                    print(f"   [OK] Audio de narración integrado al video.")

                try: os.remove(ruta_video_mudo)
                except Exception: pass

                for clip in clips_temp:
                    try:
                        os.remove(clip)
                    except Exception:
                        pass
                try:
                    os.remove(list_file)
                except Exception:
                    pass

                # Limpiar temporales de audio de los hooks (no llenar el disco del Xeon)
                for _tmp_audio in ["locucion_hooks.m4a", "audio_ext.m4a"]:
                    try: os.remove(os.path.join(carpeta_reciente, _tmp_audio))
                    except Exception: pass

                print("🎵 FASE 2: Inyección de música dinámica (fondo aleatorio + tensión al 60%)...")
                ruta_actual = ruta_base
                ruta_actual = _mezclar_musica_dinamica(
                    ruta_video       = ruta_actual,
                    carpeta_marca    = carpeta_marca_assets,
                    marca            = marca_audio,
                    duracion_total   = duracion_audio
                )

                print("🎬 FASE 3: Evaluando inyección de Intro/Outro...")
                hay_intro = os.path.exists(ruta_intro_dinamico)
                hay_outro = os.path.exists(ruta_outro_dinamico)

                if hay_intro or hay_outro:
                    inputs         = []
                    filter_parts   = []
                    concat_elements = ""
                    idx = 0

                    if hay_intro:
                        print(f"   [OK] Detectado Intro: {os.path.basename(ruta_intro_dinamico)}")
                        inputs.extend(['-i', ruta_intro_dinamico.replace("\\", "/")])
                        filter_parts.append(f"[{idx}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{idx}];")
                        concat_elements += f"[v{idx}][{idx}:a]"
                        idx += 1

                    inputs.extend(['-i', ruta_actual.replace("\\", "/")])
                    filter_parts.append(f"[{idx}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{idx}];")
                    concat_elements += f"[v{idx}][{idx}:a]"
                    idx += 1

                    if hay_outro:
                        print(f"   [OK] Detectado Outro: {os.path.basename(ruta_outro_dinamico)}")
                        inputs.extend(['-i', ruta_outro_dinamico.replace("\\", "/")])
                        filter_parts.append(f"[{idx}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{idx}];")
                        concat_elements += f"[v{idx}][{idx}:a]"
                        idx += 1

                    filter_complex = "".join(filter_parts) + f"{concat_elements}concat=n={idx}:v=1:a=1[vout][aout]"
                    cmd_concat = (
                        ['ffmpeg', '-y'] + inputs + [
                            '-filter_complex', filter_complex,
                            '-map', '[vout]', '-map', '[aout]',
                            '-c:v', 'libx264', '-preset', 'fast', '-crf', '22', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '192k',
                            ruta_final
                        ]
                    )
                    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    try:
                        os.remove(ruta_actual)
                    except Exception:
                        pass
                else:
                    print("   [INFO] Sin Intro/Outro detectados. Finalizando arquitectura base.")
                    os.rename(ruta_actual, ruta_final)

                print(f"🏆 [OPERACIÓN EXITOSA V8.4.8] Video finalizado: {ruta_final}\n")

                # Recargar SD a la GPU para que el siguiente video pueda generar imágenes
                if usar_parallax_global:
                    _recargar_sd()

                print("📦 Generando paquete de publicación SEO...")
                paquete = {}
                try:
                    res_paquete = requests.post(
                        f"{RENDER_URL}/api/interna/generar_paquete",
                        json={
                            "clave_interna":  "admin1978_master_key",
                            "marca":          marca_audio,
                            "titulo":         tarea.get("titulo_sugerido", ""),
                            "texto_locucion": texto_locucion,   
                            "formato":        formato_ensamblaje
                        },
                        timeout=400
                    )
                    if res_paquete.status_code == 200:
                        paquete = res_paquete.json().get("paquete", {})
                        ruta_paquete = os.path.join(carpeta_reciente, "paquete_publicacion.json")
                        with open(ruta_paquete, "w", encoding="utf-8") as f:
                            json.dump(paquete, f, indent=4, ensure_ascii=False)
                        print(f"✅ [PAQUETE] Guardado en: {ruta_paquete}")
                        print("🖼️ [PAQUETE] Miniaturas desactivadas — usa los prompts del paquete_publicacion.docx en Canva.")
                        _diag["paquete"]["generado"] = True
                        # Si Gemini falló y se usó respaldo, el paquete trae la marca _respaldo
                        if isinstance(paquete, dict) and paquete.get("_respaldo"):
                            _diag["paquete"]["respaldo"] = True
                            print("⚠️ [PAQUETE] Metadatos de RESPALDO (Gemini no disponible) — revisar/mejorar antes de publicar.")
                    else:
                        print(f"⚠️ [PAQUETE] Error del servidor: {res_paquete.status_code}")
                        _diag["errores"].append(f"Paquete error servidor: {res_paquete.status_code}")
                except Exception as e:
                    print(f"⚠️ [PAQUETE] Error: {e}")
                    _diag["errores"].append(f"Paquete excepción: {str(e)[:100]}")

                try:
                    if paquete:
                        _generar_word_paquete(paquete, marca_audio, formato_ensamblaje, carpeta_reciente)
                        print("✅ [WORD] paquete_publicacion.docx generado.")
                except Exception as e:
                    print(f"⚠️ [WORD] Error paquete: {e}")

                try:
                    _generar_word_guion(texto_locucion, marca_audio, formato_ensamblaje, tarea, carpeta_reciente)
                except Exception as e:
                    print(f"⚠️ [WORD] Error guión: {e}")
                    
                # 🛑 FIX MAESTRO ANTI-BUCLE: Notificamos al servidor explícitamente para que la borre de su base de datos.
                try:
                    # Duración real del MP4 final (para el historial del panel)
                    _dur_real = 0.0
                    try:
                        _dur_real = _obtener_duracion_audio_simple(ruta_final)
                    except Exception:
                        _dur_real = 0.0
                    requests.post(
                        f"{RENDER_URL}/api/nodo/tarea_completada",
                        json={"tarea_id": tarea_id, "estado": "finalizado",
                              "duracion_real_seg": round(_dur_real, 1),
                              "marca": marca_audio, "formato": formato_ensamblaje},
                        timeout=30
                    )
                    print(f"✅ [TAREA {tarea_id}] Cerrada y purgada del servidor en la nube.")
                    # Completar y subir el diagnóstico del video a la rama diagnostico
                    _diag["fin"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    _diag["duracion_real_seg"] = round(_dur_real, 1)
                    _diag["video_final"] = os.path.basename(ruta_final)
                    subir_diagnostico_video(_diag)
                except Exception as e:
                    print(f"⚠️ Error reportando cierre de ensamblaje al servidor: {e}")

            # ══════════════════════════════════════════════════
            # RUTA 2: GENERACIÓN DE IMÁGENES/VIDEOS (SD + PEXELS)
            # ══════════════════════════════════════════════════
            else:
                raw_prompt = tarea["prompt"]
                print(f"\n🚀 [ORDEN VISUAL] ID: {tarea_id}")

                # PRE-FLIGHT: la generación de imágenes necesita SD. Si está caído,
                # abortar antes de empezar (la voz aún no hace falta aquí).
                nodos_ok, motivo = verificar_nodos_criticos(necesita_sd=True, necesita_voz=False)
                if not nodos_ok:
                    print(f"🛑 [ORDEN CANCELADA] {motivo}")
                    _tareas_completadas.discard(tarea_id)
                    return

                try:
                    escenas = json.loads(raw_prompt)
                except Exception:
                    escenas = [{"id": 1, "prompt": raw_prompt}]

                marca_tarea     = tarea.get("marca", "La Viuda")
                formato_tarea   = tarea.get("formato", "9:16")
                carpeta_destino = tarea.get("carpeta_destino", None)
                nombre_archivo  = tarea.get("nombre_archivo", None)
                pexels_api_key  = (
                    PEXELS_API_KEY_LOCAL
                    if PEXELS_API_KEY_LOCAL and PEXELS_API_KEY_LOCAL != "PEGA_TU_LLAVE_REAL_AQUI"
                    else tarea.get("pexels_api_key", "")
                )

                try:
                    import sys
                    sys.path.insert(0, "C:\\NODO_PINPINELA")
                    from pexels_engine import buscar_clip_pexels, usar_pexels
                    pexels_disponible = True
                except Exception as e:
                    print(f"   [PEXELS] Motor no disponible: {e}")
                    pexels_disponible = False

                if carpeta_destino and nombre_archivo:
                    w, h     = (1920, 1080)
                    carpeta_p = carpeta_destino
                else:
                    w, h     = (1024, 576) if "16:9" in formato_tarea else (576, 1024)
                    carpeta_p = os.path.join(CARPETA_LOCAL, tarea_id)
                    os.makedirs(carpeta_p, exist_ok=True)
                    with open(os.path.join(carpeta_p, "formato.txt"), "w") as f:
                        f.write(formato_tarea)

                ip_render = IP_GRAFICA_1
                if "16:9" in formato_tarea:
                    print(f"🎬 16:9 LARGO → 3060 [{IP_GRAFICA_1}]")
                else:
                    print(f"📱 9:16 SHORT → 3060 [{IP_GRAFICA_1}]")

                # Verificar que SD responda antes de generar (ping ligero, no toca VRAM)
                _asegurar_sd_cargado()

                img_prev = ""
                historial_fuentes = []
                titulo_tarea = tarea.get("titulo", "")

                for i, esc in enumerate(escenas):
                    p = esc.get("prompt", "")
                    if not p:
                        continue
                    nodo_num     = 1 if ip_render == IP_GRAFICA_1 else 2
                    prompt_esc   = esc.get("prompt_visual", p)
                    pexels_query = esc.get("pexels_query", None)
                    es_miniatura = bool(carpeta_destino and nombre_archivo)

                    if es_miniatura:
                        path_out_png = os.path.join(carpeta_p, nombre_archivo)
                        path_out_mp4 = path_out_png.replace(".png", ".mp4")
                    else:
                        path_out_png = os.path.join(carpeta_p, f"escena_{i+1:02d}.png")
                        path_out_mp4 = os.path.join(carpeta_p, f"escena_{i+1:02d}.mp4")

                    print(f"⚙️ NODO {nodo_num}: Escena {i+1}/{len(escenas)}...")

                    # ── Alternancia inteligente Pexels/SD ────────
                    def _decidir_pexels(prompt_esc, marca, es_miniatura):
                        if not pexels_disponible or not pexels_api_key or es_miniatura: return False
                        if marca.lower().replace(" ", "") == "laesquinarandom": return False
                        if not usar_pexels(marca): return False
                        txt = prompt_esc.lower()
                        sf = sum(1 for w2 in PALABRAS_FISICAS    if w2 in txt)
                        sa = sum(1 for w2 in PALABRAS_ABSTRACTAS if w2 in txt)
                        ult = historial_fuentes[-2:]
                        if len(ult)==2 and all(f=="pexels" for f in ult): return False
                        if len(ult)==2 and all(f=="sd"     for f in ult): return True
                        if sf > sa: return True
                        if sa > sf: return False
                        return usar_pexels(marca)

                    uso_pexels = _decidir_pexels(prompt_esc, marca_tarea, es_miniatura)

                    if uso_pexels:
                        ok_pexels = buscar_clip_pexels(
                            prompt_visual=prompt_esc, marca=marca_tarea,
                            formato=formato_tarea, api_key=pexels_api_key,
                            carpeta_destino=carpeta_p,
                            nombre_archivo=os.path.basename(path_out_mp4),
                            pexels_query=pexels_query
                        )
                        if ok_pexels:
                            historial_fuentes.append("pexels")
                            print(f"   [OK] Escena {i+1} — Pexels ✅")
                            continue
                        print(f"   [FALLBACK] Escena {i+1} → SD")

                    historial_fuentes.append("sd")

                    if es_miniatura:
                        prompt_limpio = (
                            f"{prompt_esc}, photorealistic, extreme detail, single focal element, "
                            f"dramatic lighting, high contrast, sharp focus, professional photography, "
                            f"no people, no humans, no text"
                        )
                        payload = {
                            "prompt": prompt_limpio,
                            "negative_prompt": (
                                "nude, naked, nudity, topless, nsfw, explicit, bare skin, "
                                "exposed body, breasts, nipples, cleavage, lingerie, underwear, "
                                "sensual, erotic, sexual, suggestive, genitalia, pornographic, "
                                "person, people, human, face, body, blurry, dark, underexposed, "
                                "low contrast, generic, boring, text, watermark, logo, multiple objects, "
                                "busy composition, dull, flat lighting, overexposed, washed out, "
                                "cartoon, anime, illustration, 3d render, cgi, "
                                "deformed, malformed, mutated, distorted, misshapen objects, "
                                "warped objects, melting objects, impossible geometry, broken perspective, "
                                "warped architecture, garbled details, gibberish text, scrambled text, "
                                "duplicated objects, floating objects, jpeg artifacts, glitches, "
                                "poorly drawn, sloppy details, incoherent details"
                            ),
                            "steps": 45, "cfg_scale": 10,
                            "width": w, "height": h,
                            "sampler_name": "DPM++ 3M SDE Karras",
                            "batch_size": 1, "n_iter": 1
                        }
                    else:
                        marca_limpia = marca_tarea.lower()
                        
                        if marca_limpia in ["la esquina random", "laesquinarandom"]:
                            prompt_limpio = (
                                f"{prompt_esc}, funny cartoon style, 2D animation, clean vector art, "
                                f"vibrant flat colors, comic book aesthetic, expressive caricature, "
                                f"exaggerated facial expressions, clear well-defined faces, "
                                f"correct anatomy, simple clean shapes, single main character in focus, "
                                f"clean uncluttered background, humorous situation, "
                                f"vibrant lighting, cel shaded, high quality cartoon illustration"
                            )
                            neg_prompt = (
                                "background crowd, distant people, crowd of people, many people, "
                                "tiny faces, small distant figures, blurry background figures, "
                                "deformed, bad anatomy, malformed, mutated, disfigured, distorted face, "
                                "ugly face, asymmetric face, extra limbs, extra fingers, missing fingers, "
                                "fused fingers, extra arms, extra legs, malformed hands, bad hands, "
                                "deformed eyes, crossed eyes, lazy eye, extra eyes, melted face, "
                                "twisted body, broken anatomy, blurry, low quality, jpeg artifacts, "
                                "nonsense, gibberish, abstract mess, photorealistic, realistic, 3d render, "
                                "hyperrealistic, photography, raw photo, dark, gloomy, horror, serious, "
                                "monochrome, anime, manga, text, watermark, signature"
                            )
                        
                        elif marca_limpia in ["la viuda", "laviuda"]:
                            # Rotar el tipo de composición para dar variedad manteniendo el terror.
                            # El estilo (rojo, grano, chiaroscuro) es constante; el SUJETO varía.
                            _estilo_viuda = (
                                "extreme low key lighting, chiaroscuro, deep saturated red and pitch black shadows, "
                                "high contrast, rough decaying textures, heavy vintage analog film grain, macabre atmosphere"
                            )
                            _composiciones_viuda = [
                                "terrifying psychological horror, paranormal shadowy apparition, ghostly dark hooded figure standing",
                                "eerie empty haunted room, abandoned decaying interior, no figure, oppressive emptiness, creepy atmosphere",
                                "extreme close-up of a single ominous object, symbolic horror detail, dramatic shadow, mysterious",
                                "dark twisted hallway leading into blackness, perspective vanishing point, dread and unease",
                                "creepy old window with faint silhouette behind curtain, distant blurred shape, paranormal",
                                "macabre still life, old decaying objects on a table, candlelight, gothic horror mood",
                                "shadow cast on a wall by unseen presence, distorted silhouette, psychological dread",
                                "abandoned staircase descending into darkness, ominous depth, haunting",
                                "extreme close-up of weathered hands or eyes in shadow, fragmented horror, partial view",
                                "foggy desolate exterior at night, lone bare tree, isolation, supernatural dread",
                                "old mirror reflecting a dim distorted shape, broken glass, haunted reflection",
                                "antique door slightly ajar with darkness behind, threshold of dread, creaking",
                                "dusty abandoned bedroom, unmade old bed, faded wallpaper peeling, ghostly stillness",
                                "flickering candle in pitch darkness, single flame, wax dripping, eerie glow",
                                "old portrait painting on a wall, face obscured by shadow, watching eyes, gothic",
                                "creepy basement corner, cobwebs, faint red light, claustrophobic dread",
                                "rain-streaked window at night, blurry shape outside, melancholic horror",
                                "abandoned rocking chair moving alone, empty room, paranormal presence",
                                "long dark corridor with flickering light at the far end, isolation, fear",
                                "old wooden floorboards with a single object, top-down ominous angle, mystery",
                                "decaying religious shrine or altar, melted candles, unsettling silence, gothic",
                                "fog rolling across a graveyard at night, leaning tombstones, desolation",
                                "close-up of an old clock stopped at midnight, dust, frozen time, dread",
                                "silhouette of bare branches against a blood-red sky, twisted shapes, ominous",
                                "empty antique armchair facing away, dim room, sense of unseen watcher",
                                "shattered photograph on the floor, faded faces, broken memory, melancholy horror",
                                "dim attic with hanging dusty sheets, hidden shapes, suffocating dread",
                                "single bare lightbulb swinging in darkness, harsh shadows, interrogation of fear",
                                "overgrown abandoned house exterior at dusk, broken windows, red haze",
                                "close-up of a trembling candle flame reflected in a dark eye, extreme intimacy of fear",
                            ]
                            # Barajar el orden por video (semilla = id de tarea) para que
                            # no salga siempre la misma secuencia, sin repetir dentro del video
                            import random as _rnd_v
                            _orden = list(range(len(_composiciones_viuda)))
                            _rnd_v.Random(str(tarea.get("id", "")) + "viuda").shuffle(_orden)
                            _comp = _composiciones_viuda[_orden[i % len(_composiciones_viuda)]]
                            # Variación extra: alternar plano (amplio/cerrado) según paridad
                            _plano = "wide establishing shot, full scene" if i % 2 == 0 else "tight intimate framing, shallow focus"
                            prompt_limpio = (
                                f"{prompt_esc}, {_comp}, {_plano}, {_estilo_viuda}, no realistic humans, no blood"
                            )
                            neg_prompt = (
                                "normal living person, clear human face, detailed human body, realistic human, "
                                "deformed eyes, malformed eyes, asymmetric eyes, crossed eyes, lazy eye, "
                                "extra eyes, misaligned pupils, googly eyes, bulging eyes, uneven eyes, "
                                "distorted face, malformed face, disfigured face, twisted face, melted face, "
                                "bad anatomy, deformed, mutated, extra limbs, malformed hands, bad hands, "
                                "alien, extraterrestrial, grey alien, UFO, martian, sci-fi, science fiction, mutant, creature, monster, tentacles, "
                                "blood, gore, red liquid, violent, text, watermark, blurry, low quality, "
                                "anime, cartoon, 3d render, cgi, clean, modern architecture, office, hospital, "
                                "subway, safe, bright, mundane, well lit, symmetrical, empty liminal space"
                            )

                        elif marca_limpia in ["monkygraff"]:
                            _estilo_monky = (
                                "RAW photo, photojournalism, real photography, shot on location, "
                                "harsh natural lighting, gritty texture, physical environment"
                            )
                            _composiciones_monky = [
                                "aerial view of a military base at dawn, runways and hangars",
                                "industrial port with stacked cargo containers, cranes, logistics",
                                "control room with screens and maps, empty, tactical operations",
                                "satellite dish array against a clear sky, signals intelligence",
                                "oil refinery at dusk, pipes and towers, industrial complex",
                                "cargo ship crossing open ocean, aerial drone shot, maritime trade",
                                "radar station on a remote hill, surveillance infrastructure",
                                "power plant cooling towers releasing steam, energy infrastructure",
                                "underground bunker corridor with concrete walls, secure facility",
                                "military vehicles parked in formation, aerial top-down view",
                                "data center server racks with blinking lights, digital infrastructure",
                                "border checkpoint with fencing and watchtowers, geopolitical tension",
                                "pipeline stretching across barren landscape, energy transport",
                                "naval fleet at sea seen from above, strategic maritime power",
                                "abandoned factory interior with rusted machinery, industrial decay",
                                "aerial night view of a city grid with glowing lights, urban scale",
                                "warehouse stacked with crates and pallets, supply chain",
                                "communication tower silhouette at sunset, network infrastructure",
                                "desert airstrip with parked aircraft, remote military outpost",
                                "stock exchange or financial district exterior, economic power",
                            ]
                            import random as _rnd_m
                            _ord_m = list(range(len(_composiciones_monky)))
                            _rnd_m.Random(str(tarea.get("id", "")) + "monky").shuffle(_ord_m)
                            _comp_m = _composiciones_monky[_ord_m[i % len(_composiciones_monky)]]
                            _plano_m = "wide aerial establishing shot" if i % 2 == 0 else "tight detail shot"
                            prompt_limpio = (
                                f"{prompt_esc}, {_comp_m}, {_plano_m}, {_estilo_monky}, "
                                f"no people, no faces, no cgi, no digital art"
                            )
                            neg_prompt = (
                                "person, people, human, face, body, horror, dark, terror, ghost, shadow figure, "
                                "neon, glowing, hologram, digital, abstract, wireframe, sci-fi, futuristic, "
                                "3d render, cartoon, anime, text, watermark, blurry, low quality, "
                                "psychological horror, paranormal, supernatural, creepy"
                            )

                        elif marca_limpia in ["filtradmx", "filtrado mx", "filtradomx"]:
                            # MATRIZ VISUAL TELENOVELA MEXICANA — variedad de composiciones
                            _estilo_filtrado = (
                                "dramatic mexican telenovela atmosphere, natural soft daylight, "
                                "muted neutral tones, white walls, natural wood, soft shadows, "
                                "shallow depth of field, RAW photo iPhone portrait mode, "
                                "cinematic drama lighting, subtle film grain, cool white light"
                            )
                            _composiciones_filtrado = [
                                "wedding ring left on a table, intimate betrayal, emotional weight",
                                "phone screen with a notification glowing in a dark room, secret revealed",
                                "two coffee cups on a table, one untouched, tension of absence",
                                "open suitcase on a bed, clothes half packed, departure imminent",
                                "empty chair at a dinner table, plate set, someone missing",
                                "letter or note folded on a kitchen counter, unspoken words",
                                "front door slightly open, keys in the lock, dramatic threshold",
                                "wilting flowers in a vase by a window, fading love metaphor",
                                "wine glass with lipstick mark on a nightstand, evidence of another",
                                "framed photo turned face down on a shelf, hidden past",
                                "rumpled bedsheets in soft morning light, intimacy and betrayal",
                                "rain on a window with warm interior light, melancholy waiting",
                                "a single earring on the floor, clue of an affair",
                                "clock on the wall showing late hour, waiting in vain",
                                "half-empty closet with one side cleared out, someone left",
                                "smartphone face down vibrating on a wooden table, hidden messages",
                                "untouched birthday cake with candles burned out, forgotten celebration",
                                "car keys and a packed bag by the entrance, decision made",
                                "blurred figure leaving through a doorway in the background, departure",
                                "torn photograph pieces on a desk, broken relationship",
                            ]
                            import random as _rnd_f
                            _ord_f = list(range(len(_composiciones_filtrado)))
                            _rnd_f.Random(str(tarea.get("id", "")) + "filtrado").shuffle(_ord_f)
                            _comp_f = _composiciones_filtrado[_ord_f[i % len(_composiciones_filtrado)]]
                            _plano_f = "wide establishing shot" if i % 2 == 0 else "extreme close-up detail"
                            prompt_limpio = (
                                f"{prompt_esc}, {_comp_f}, {_plano_f}, {_estilo_filtrado}, "
                                f"everyday object with emotional weight, no people, no children, no faces"
                            )
                            neg_prompt = (
                                "nude, naked, topless, nsfw, explicit, bare skin, exposed body, "
                                "cleavage, lingerie, underwear, sensual, erotic, sexual, "
                                "person, people, human, face, body, child, children, kid, kids, "
                                "baby, teen, teenager, minor, school, playground, toy, "
                                "horror, terror, dark, gore, violence, blood, "
                                "neon, glowing, sci-fi, futuristic, digital art, "
                                "3d render, cartoon, anime, text, watermark, blurry, low quality, "
                                "office, corporate, business, medical, hospital, outdoor, nature"
                            )

                        else:
                            prompt_limpio = (
                                f"{prompt_esc}, RAW photo, photorealistic, real photography, "
                                f"no people, no humans, no persons, natural lighting, film grain, "
                                f"gritty texture, shot on location, physical environment, "
                                f"no cgi, no digital art, no abstract"
                            )
                            neg_prompt = (
                                "person, people, human, man, woman, boy, girl, face, body, character, "
                                "figure, portrait, selfie, eye, eyes, closeup face, macro face, skin pores, "
                                "eyelash, eyebrow, iris, pupil, canon, nikon, sony, logo, brand, watermark, "
                                "text, collage, split screen, multiple panels, deformed, blurry, low quality, "
                                "nude, naked, nsfw, explicit, anime, cartoon, illustration, 3d render, "
                                "videogame, cgi, digital art, concept art, abstract, glowing lines, neon, "
                                "hologram, sci-fi, futuristic, cyber, wireframe, network visualization, "
                                "data visualization, particle effects, blue glow, tron, virtual, simulation, "
                                "render, unreal engine, octane, vray, digital painting, fantasy, surreal, vfx"
                            )

                        # ── BLOQUEO NSFW GLOBAL OBLIGATORIO (todos los canales) ──
                        # Se antepone a CUALQUIER negative prompt, sin excepción
                        NSFW_BLOCK = (
                            "nude, naked, nudity, topless, bottomless, nsfw, explicit, "
                            "bare skin, exposed body, exposed breasts, breasts, nipples, "
                            "cleavage, lingerie, underwear, panties, bra, thong, bikini, "
                            "sensual, erotic, sexual, suggestive, provocative, seductive, "
                            "genitalia, genitals, crotch, pubic, intimate body parts, "
                            "porn, pornographic, fetish, nude body, undressed, stripping, "
                        )
                        # ── BLOQUE ANTI-DEFORMACIÓN GLOBAL (todos los canales) ──
                        # Refuerza contra detalles deformes que se cuelan: objetos retorcidos,
                        # manos/dedos malos, texto inventado, arquitectura imposible, artefactos.
                        ANTI_DEFORM = (
                            "deformed, malformed, mutated, disfigured, distorted, misshapen, "
                            "extra fingers, missing fingers, fused fingers, too many fingers, "
                            "extra hands, malformed hands, bad hands, mangled hands, extra limbs, "
                            "extra arms, extra legs, fused limbs, twisted limbs, broken anatomy, "
                            "deformed objects, melting objects, warped objects, distorted objects, "
                            "impossible geometry, broken perspective, warped architecture, "
                            "distorted background, garbled details, incoherent details, "
                            "gibberish text, fake text, scrambled text, nonsensical symbols, "
                            "duplicated objects, cloned details, floating objects, "
                            "jpeg artifacts, compression artifacts, glitches, smudged details, "
                            "low quality details, poorly drawn, sloppy details, "
                        )
                        neg_prompt = NSFW_BLOCK + ANTI_DEFORM + neg_prompt

                        payload = {
                            "prompt": prompt_limpio,
                            "negative_prompt": neg_prompt,
                            "steps": 45,
                            "cfg_scale": 7 if marca_limpia in ["la esquina random", "laesquinarandom"] else 8,
                            "width": w, "height": h,
                            "sampler_name": "DPM++ 3M SDE Karras",
                            "batch_size": 1, "n_iter": 1
                        }

                        # ADetailer: corrige rostros/ojos automáticamente en canales con caras
                        if marca_limpia in ["la esquina random", "laesquinarandom"]:
                            payload["alwayson_scripts"] = {
                                "ADetailer": {
                                    "args": [
                                        True,   # enable
                                        False,  # skip_img2img
                                        {
                                            "ad_model": "face_yolov8n.pt",
                                            "ad_prompt": "clear well-defined cartoon face, correct anatomy, expressive eyes, clean lines, high quality",
                                            "ad_negative_prompt": "deformed, malformed, distorted face, ugly, asymmetric, extra eyes, crossed eyes, melted, blurry, bad anatomy",
                                            "ad_confidence": 0.15,
                                            "ad_denoising_strength": 0.4,
                                            "ad_inpaint_only_masked": True,
                                            "ad_inpaint_only_masked_padding": 32
                                        }
                                    ]
                                }
                            }
                        elif marca_limpia in ["la viuda", "laviuda"]:
                            # ADetailer para terror: corrige ojos/rostro manteniendo la estética macabra
                            payload["alwayson_scripts"] = {
                                "ADetailer": {
                                    "args": [
                                        True,
                                        False,
                                        {
                                            "ad_model": "face_yolov8n.pt",
                                            "ad_prompt": "eerie face with correct anatomy, well-formed symmetric eyes, aligned pupils, dark horror atmosphere, low key red lighting, film grain, realistic proportions",
                                            "ad_negative_prompt": "deformed eyes, asymmetric eyes, crossed eyes, extra eyes, bulging eyes, googly eyes, misaligned pupils, distorted face, malformed, melted, bad anatomy, bright, cartoon, anime",
                                            "ad_confidence": 0.25,
                                            "ad_denoising_strength": 0.35,
                                            "ad_inpaint_only_masked": True,
                                            "ad_inpaint_only_masked_padding": 32
                                        }
                                    ]
                                }
                            }
                        elif not es_miniatura:
                            # RED DE SEGURIDAD anti-deformación para TODOS los demás canales
                            # (FiltradoMX, Monkygraff, Tuialista y futuros).
                            # Son canales "sin personas", pero si se cuela un rostro/figura,
                            # ADetailer lo corrige. ad_confidence alto = solo actúa si hay
                            # una cara clara (no molesta en escenas de puro objeto/paisaje).
                            payload["alwayson_scripts"] = {
                                "ADetailer": {
                                    "args": [
                                        True,
                                        False,
                                        {
                                            "ad_model": "face_yolov8n.pt",
                                            "ad_prompt": "realistic well-formed face, correct anatomy, symmetric eyes, aligned pupils, natural proportions, photographic",
                                            "ad_negative_prompt": "deformed eyes, asymmetric eyes, crossed eyes, extra eyes, bulging eyes, googly eyes, misaligned pupils, distorted face, malformed, melted, bad anatomy, cartoon, anime",
                                            "ad_confidence": 0.4,
                                            "ad_denoising_strength": 0.35,
                                            "ad_inpaint_only_masked": True,
                                            "ad_inpaint_only_masked_padding": 32
                                        }
                                    ]
                                }
                            }

                    sd_ok = False
                    for intento_sd in range(3):
                        try:
                            print(f"   [SD] Intento {intento_sd+1}/3 escena {i+1}...")
                            res_sd = requests.post(
                                f"http://{ip_render}:7861/sdapi/v1/txt2img",
                                json=payload, timeout=600
                            )
                            if res_sd.status_code == 200:
                                b64 = res_sd.json()['images'][0]
                                with open(path_out_png, "wb") as f:
                                    f.write(base64.b64decode(b64))
                                # RED DE SEGURIDAD: ¿la imagen salió negra? (censura NSFW
                                # o fallo del modelo devuelven negro con HTTP 200).
                                if _imagen_es_negra(path_out_png):
                                    print(f"   ⚠️ Escena {i+1}: imagen NEGRA detectada — regenerando (intento {intento_sd+1})...")
                                    # variar la semilla para no repetir el mismo negro
                                    try:
                                        payload["seed"] = random.randint(1, 2_000_000_000)
                                    except Exception:
                                        pass
                                    time.sleep(2)
                                    continue  # reintentar
                                if not img_prev:
                                    img_prev = b64
                                print(f"   [OK] Nodo {nodo_num} — Escena {i+1} SD ✅")
                                if es_miniatura and titulo_tarea:
                                    _quemar_titulo_miniatura(path_out_png, titulo_tarea, marca_tarea)
                                sd_ok = True
                                break
                            else:
                                print(f"   ⚠️ SD respondió {res_sd.status_code} — reintentando...")
                                time.sleep(5)
                        except Exception as e:
                            print(f"   ⚠️ SD error intento {intento_sd+1}: {e}")
                            time.sleep(5)
                    if not sd_ok:
                        # Agotados los 3 intentos (o todas salieron negras): SUSTITUIR
                        # por la escena anterior válida, para no dejar un hueco negro
                        # que corte la retención.
                        print(f"   ❌ Escena {i+1} sin imagen válida tras 3 intentos.")
                        _sustituida = False
                        # Buscar la escena previa válida (no negra) ya generada
                        for _prev_i in range(i, 0, -1):
                            _prev_png = os.path.join(carpeta_p, f"escena_{_prev_i:02d}.png")
                            if os.path.exists(_prev_png) and not _imagen_es_negra(_prev_png):
                                try:
                                    import shutil as _sh
                                    _sh.copy(_prev_png, path_out_png)
                                    print(f"   [FIX] Escena {i+1} sustituida por la escena {_prev_i} (evita pantalla negra).")
                                    _sustituida = True
                                    sd_ok = True
                                    break
                                except Exception:
                                    pass
                        if not _sustituida and img_prev:
                            # Último recurso: usar la primera imagen válida de la tarea
                            try:
                                with open(path_out_png, "wb") as f:
                                    f.write(base64.b64decode(img_prev))
                                print(f"   [FIX] Escena {i+1} sustituida por la primera imagen válida.")
                                sd_ok = True
                            except Exception:
                                pass

                try:
                    payload_upload = {"tarea_id": tarea_id}
                    if img_prev:
                        payload_upload["image_b64"] = f"data:image/png;base64,{img_prev}"
                    requests.post(
                        f"{RENDER_URL}/api/nodo/upload_result",
                        json=payload_upload, timeout=400
                    )
                    
                    # 🛑 FIX MAESTRO ANTI-BUCLE: Notificamos también aquí por si acaso tu servidor usa este endpoint para cerrar
                    requests.post(
                        f"{RENDER_URL}/api/nodo/tarea_completada",
                        json={"tarea_id": tarea_id, "estado": "finalizado"},
                        timeout=30
                    )

                    # ENCOLAR EL ENSAMBLAJE LOCALMENTE (no depende de /tmp de Render, que es efímero).
                    # El worker tiene todos los datos, así que arma el ensamblaje y lo guarda en disco local.
                    if tarea.get("texto_locucion") or tarea.get("origen", "").startswith("bot"):
                        try:
                            voice_id = "PHKlYg202ODwQRa3Fxuo" if tarea.get("marca") == "Monkygraff" else "GTY55jD77hLBRrnQOhNk"
                            ensamblaje_local = {
                                "id": f"{tarea_id}_asm",
                                "tipo": "ENSAMBLAJE",
                                "formato": tarea.get("formato", "9:16"),
                                "marca": tarea.get("marca", "La Viuda"),
                                "texto_locucion": tarea.get("texto_locucion", ""),
                                "escenas_texto": tarea.get("escenas_texto", []),
                                "escenas": tarea.get("escenas", []),
                                "titulo_sugerido": tarea.get("titulo_sugerido", ""),
                                "hooks": tarea.get("hooks", []),
                                "voice_id": voice_id,
                                "origen": tarea.get("origen", "bot"),
                            }
                            os.makedirs(r"C:\NODO_PINPINELA\cola_local", exist_ok=True)
                            with open(rf"C:\NODO_PINPINELA\cola_local\ensamblaje_{tarea_id}.json", "w", encoding="utf-8") as f:
                                json.dump(ensamblaje_local, f, ensure_ascii=False)
                            print(f"   [PIPELINE] Ensamblaje encolado localmente → continuará automáticamente")
                        except Exception as e:
                            print(f"   ⚠️ No se pudo encolar ensamblaje local: {e}")

                    print(f"✅ [LOTE COMPLETADO] Nodo local sincronizado y tarea cerrada.\n")
                except Exception as e:
                    print(f"⚠️ Error al sincronizar cierre de lote: {e}")

    except Exception as e:
        print(f"⚠️ Error en ciclo de ejecución: {e}")
    finally:
        # Avisar a Render que el worker quedó LIBRE (solo si tomó una tarea en este ciclo)
        try:
            if _worker_tomo_tarea[0]:
                requests.post(f"{RENDER_URL}/api/nodo/worker_estado",
                              json={"ocupado": False, "tarea_actual": ""}, timeout=10)
                _worker_tomo_tarea[0] = False
                print("   [LIBRE] Worker disponible para la siguiente orden.")
        except:
            pass
        # Evitar que _tareas_completadas crezca sin límite (mantener solo las últimas 50)
        try:
            if len(_tareas_completadas) > 50:
                # conservar las más recientes no es trivial en un set; lo vaciamos
                # cuando crece demasiado (las tareas viejas ya no se reenvían)
                _tareas_completadas.clear()
                print("   [LIMPIEZA] Registro de tareas completadas reiniciado.")
        except:
            pass


print("⚡ NODO XEON ONLINE - FIX ANTI-BUCLE APLICADO")
while True:
    procesar()
    time.sleep(2)