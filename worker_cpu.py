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
    """Libera la VRAM de Stable Diffusion antes del parallax.
    En el ensamblaje las imágenes ya están generadas, así que SD no se necesita,
    y DepthFlow necesita esa VRAM para no fallar (causa raíz del error 500)."""
    try:
        # Automatic1111: descargar el modelo de la GPU libera la mayor parte de la VRAM
        requests.post(f"{URL_NODO_SD}/sdapi/v1/unload-checkpoint", timeout=30)
        print("   [VRAM] Stable Diffusion descargado de la GPU (libera memoria para DepthFlow)")
        import time as _t
        _t.sleep(3)  # dar tiempo a que la VRAM se libere
        return True
    except Exception as e:
        print(f"   [VRAM] No se pudo descargar SD ({str(e)[:60]}) — DepthFlow puede fallar por VRAM")
        return False

def _recargar_sd():
    """Recarga el modelo de SD después del parallax (para el siguiente video)."""
    try:
        requests.post(f"{URL_NODO_SD}/sdapi/v1/reload-checkpoint", timeout=60)
        print("   [VRAM] Stable Diffusion recargado para el siguiente trabajo")
    except Exception:
        pass

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
                              files=archivos, data=datos, timeout=300)
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

# ══════════════════════════════════════════════════════════════
# SISTEMA DE HOOKS — PAUSA DRAMÁTICA CADA N ESCENAS
# ══════════════════════════════════════════════════════════════
HOOK_CADA_N_ESCENAS = 9
HOOK_DURACION       = 2.5

def _elegir_stinger(carpeta_marca, contador_hook):
    idx = (contador_hook % 2) + 1
    ruta = os.path.join(carpeta_marca, f"stinger{idx}.mp3")
    if os.path.exists(ruta):
        return ruta
    ruta_alt = os.path.join(carpeta_marca, f"stinger{3-idx}.mp3")
    return ruta_alt if os.path.exists(ruta_alt) else None

def _generar_clip_hook(frase, ruta_imagen_base, ruta_stinger, ruta_salida, w, h, fps=30):
    try:
        total_frames = int(HOOK_DURACION * fps)
        ruta_vtmp = ruta_salida.replace('.mp4', '_vtmp.mp4')
        vf = (
            f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
            f"zoompan=z='1.0+0.6*(on/{total_frames})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={total_frames}:fps={fps}:s={w}x{h},"
            f"fade=t=in:st=0:d=0.1,fade=t=out:st={HOOK_DURACION-0.3:.1f}:d=0.3"
        )
        subprocess.run([
            'ffmpeg', '-y', '-i', ruta_imagen_base,
            '-vf', vf, '-t', str(HOOK_DURACION),
            '-c:v', 'libx264', '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p', '-r', str(fps), ruta_vtmp
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not os.path.exists(ruta_vtmp):
            return False

        # Quemar texto con Pillow
        if PIL_DISPONIBLE and frase:
            try:
                from PIL import Image, ImageDraw, ImageFont
                ruta_frame = ruta_salida.replace('.mp4', '_hframe.png')
                subprocess.run([
                    'ffmpeg', '-y', '-i', ruta_vtmp,
                    '-vf', 'select=eq(n,{})'.format(total_frames//2), '-vframes', '1', ruta_frame
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if os.path.exists(ruta_frame):
                    img = Image.open(ruta_frame).convert('RGBA')
                    iw, ih = img.size
                    font = None
                    for rf in FUENTES_WINDOWS:
                        if os.path.exists(rf):
                            try: font = ImageFont.truetype(rf, int(ih * 0.07)); break
                            except: continue
                    if not font: font = ImageFont.load_default()
                    ov = Image.new('RGBA', img.size, (0,0,0,0))
                    dr = ImageDraw.Draw(ov)
                    bb = dr.textbbox((0,0), frase.upper(), font=font)
                    tx = (iw-(bb[2]-bb[0]))//2
                    ty = ih//2-(bb[3]-bb[1])//2
                    dr.text((tx+3,ty+3), frase.upper(), font=font, fill=(0,0,0,200))
                    dr.text((tx,ty), frase.upper(), font=font, fill=(255,255,255,255))
                    Image.alpha_composite(img, ov).convert('RGB').save(ruta_frame)
                    ruta_vtxt = ruta_salida.replace('.mp4', '_vtxt.mp4')
                    subprocess.run([
                        'ffmpeg', '-y', '-i', ruta_vtmp, '-i', ruta_frame,
                        '-filter_complex',
                        f"[0:v][1:v]overlay=0:0:enable='between(t,0.2,{HOOK_DURACION-0.3:.1f})'[v]",
                        '-map', '[v]', '-c:v', 'libx264', '-preset', 'ultrafast',
                        '-pix_fmt', 'yuv420p', ruta_vtxt
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if os.path.exists(ruta_vtxt):
                        os.replace(ruta_vtxt, ruta_vtmp)
                    try: os.remove(ruta_frame)
                    except: pass
            except Exception as e:
                print(f"   [HOOK] Error texto: {e}")

        # Mezclar stinger
        if ruta_stinger and os.path.exists(ruta_stinger):
            subprocess.run([
                'ffmpeg', '-y', '-i', ruta_vtmp, '-i', ruta_stinger,
                '-filter_complex',
                f"[1:a]volume=0.8,atrim=0:{HOOK_DURACION},asetpts=PTS-STARTPTS[s];"
                f"[0:a][s]amix=inputs=2:duration=first[aout]",
                '-map', '0:v', '-map', '[aout]',
                '-c:v', 'copy', '-c:a', 'aac', ruta_salida
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['ffmpeg', '-y', '-i', ruta_vtmp, '-c', 'copy', ruta_salida],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try: os.remove(ruta_vtmp)
        except: pass
        return os.path.exists(ruta_salida)
    except Exception as e:
        print(f"   [HOOK] Error: {e}")
        return False

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


def _generar_subtitulos_shorts(ruta_audio, texto_locucion, escenas_texto, marca, carpeta_reciente, dur_total):
    """Subtítulos lineales anclados a los silencios reales del audio (mejor sincronía)."""
    ruta_srt = os.path.join(carpeta_reciente, "subtitulos.srt").replace("\\", "/")

    print(f"📝 Generando subtítulos — Canal: {marca} | Duración: {dur_total:.1f}s")

    texto_completo = " ".join(escenas_texto) if escenas_texto else texto_locucion

    if not texto_completo.strip():
        print("   [ERROR] Texto vacío.")
        return None

    # Detectar pausas reales del locutor para anclar los subtítulos
    silencios = _detectar_silencios(ruta_audio) if ruta_audio and os.path.exists(ruta_audio) else []
    if silencios:
        print(f"   [SUBS] {len(silencios)} pausas reales detectadas — anclando subtítulos")
        _generar_srt_anclado(texto_completo, dur_total, marca, ruta_srt, silencios)
    else:
        print(f"   [SUBS] Sin pausas detectadas — distribución lineal")
        _generar_srt_calibrado(texto_completo, dur_total, marca, ruta_srt)
    print(f"   [OK] SRT generado.")
    return ruta_srt


def _generar_srt_anclado(texto_completo, dur_total, marca, ruta_srt, silencios):
    """Distribuye chunks anclándolos a las pausas reales del audio.
    Cada chunk se alinea al silencio más cercano para que coincida con el habla real."""
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

    # Tiempos estimados de inicio de cada chunk (lineal)
    inicios_est = []
    t = 0.0
    for c in chunks:
        inicios_est.append(t)
        t += len(c.split()) * seg_por_palabra

    # Anclar cada inicio estimado al silencio real más cercano (si está cerca)
    silencios_sorted = sorted(silencios)
    inicios_finales = []
    for ini_est in inicios_est:
        # Buscar el silencio más cercano dentro de una ventana de 1.5s
        candidatos = [s for s in silencios_sorted if abs(s - ini_est) <= 1.5]
        if candidatos:
            mejor = min(candidatos, key=lambda s: abs(s - ini_est))
            inicios_finales.append(mejor)
        else:
            inicios_finales.append(ini_est)

    # Asegurar que sean monótonos crecientes
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


def procesar():
    global _tareas_completadas  # FIX: Llamamos al registro local
    
    try:
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

                # PRE-FLIGHT: el ensamblaje necesita SD (imágenes) y VOZ. Si falta
                # alguno, abortar AHORA y no perder el trabajo largo.
                nodos_ok, motivo = verificar_nodos_criticos(necesita_sd=True, necesita_voz=True)
                if not nodos_ok:
                    print(f"🛑 [ENSAMBLAJE CANCELADO] {motivo}")
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
                    resultado = generar_audio_local(texto_locucion, marca_audio, ruta_audio)
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

                duraciones_escenas = calcular_duraciones(num_escenas, duracion_audio, fps)

                efectos_por_tipo = {
                    'tension':    ['ken_burns_agresivo', 'pan_l_slow', 'pan_r_slow', 'vignette_pulse', 'push_in_slow', 'drift_diagonal'],
                    'impacto':    ['zoom_punch', 'flash_cut', 'snap_zoom', 'punch_in'],
                    'transicion': ['slide_l', 'slide_r', 'slide_up', 'ken_burns_diagonal', 'fade_pan', 'push_in_slow', 'drift_diagonal'],
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
                        # Pan suave + vignette pulsante — sensación de urgencia subconsciente
                        dist = 0.10 if es_largo else 0.08
                        return (
                            f"zoompan=z=1.50:x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/120)'"
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
                        # Empuje lento hacia el centro — cinematográfico, profesional
                        return (
                            f"zoompan=z='1.10+0.35*(on/{total_frames})'"
                            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'drift_diagonal':
                        # Deriva diagonal suave con zoom leve — movimiento orgánico
                        dist = 0.10 if es_largo else 0.08
                        return (
                            f"zoompan=z='1.35+0.05*sin(on/100)'"
                            f":x='iw/2-(iw/zoom/2)+(iw*{dist})*(on/{total_frames})'"
                            f":y='ih/2-(ih/zoom/2)+(ih*{dist*0.7:.2f})*(on/{total_frames})'"
                            f":d={total_frames}:fps={fps}:s={w}x{h}"
                        )
                    elif efecto == 'pan_l_slow':
                        dist = 0.12 if es_largo else 0.10
                        return f"zoompan=z=1.45:x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/120)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'pan_r_slow':
                        dist = 0.12 if es_largo else 0.10
                        return f"zoompan=z=1.45:x='iw/2-(iw/zoom/2)+(iw*{dist})*cos(on/120)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
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
                hooks_video    = tarea.get("hooks", [])
                clips_temp     = []
                contador_hook  = 0
                print(f"   [HOOKS] Recibidos: {len(hooks_video)} hooks: {hooks_video}")
                
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
                        vf_string = f"fade=t=in:st=0:d=0.1,noise=alls=5:allf=t+u,vignette=PI/4,setpts=PTS-STARTPTS{glitch_fx}"
                        cmd_scene = [
                            'ffmpeg', '-y', '-stream_loop', '-1', '-i', path_origen,
                            '-vf', vf_string, '-t', str(dur_exacta),
                            '-c:v', 'libx264', '-preset', 'ultrafast',
                            '-threads', '0', '-pix_fmt', 'yuv420p', '-r', str(fps), path_clip
                        ]

                    subprocess.run(cmd_scene, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    # Validar el clip; si está corrupto, regenerar simple
                    if not _clip_es_valido(path_clip, dur_exacta):
                        print(f"   [FIX] clip_{i:02d} corrupto — regenerando simple...")
                        _generar_clip_simple(path_origen, path_clip, dur_exacta, w, h, fps)
                    clips_temp.append(path_clip)
                    print(f"   [OK] Escena {i+1} ({'SD' if archivo.endswith('.png') else 'Pexels'}) — tipo:{tipo} efecto:{efecto}")

                filtro_sub = ""
                if not es_largo_video:
                    escenas_texto = tarea.get("escenas_texto", [])
                    ruta_srt = _generar_subtitulos_shorts(
                        ruta_audio, texto_locucion, escenas_texto, marca_audio, carpeta_reciente, duracion_audio
                    )
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
                    _dur_esp = duraciones_escenas[_ci] if _ci < len(duraciones_escenas) else None
                    if not _clip_es_valido(_clip):
                        print(f"   [FIX] clip_{_ci:02d} ilegible en validación final — regenerando...")
                        _dur_regen = _dur_esp if _dur_esp else 5.0
                        _generar_clip_simple(
                            os.path.join(carpeta_reciente, archivos_escenas[_ci]) if _ci < len(archivos_escenas) else _clip,
                            _clip, _dur_regen, w, h, fps
                        )
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

                cmd_merge = [
                    'ffmpeg', '-y',
                    '-i', ruta_video_mudo,
                    '-i', ruta_audio.replace("\\", "/"),
                    '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    ruta_base
                ]
                subprocess.run(cmd_merge, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
                    else:
                        print(f"⚠️ [PAQUETE] Error del servidor: {res_paquete.status_code}")
                except Exception as e:
                    print(f"⚠️ [PAQUETE] Error: {e}")

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
                    requests.post(
                        f"{RENDER_URL}/api/nodo/tarea_completada",
                        json={"tarea_id": tarea_id, "estado": "finalizado"},
                        timeout=30
                    )
                    print(f"✅ [TAREA {tarea_id}] Cerrada y purgada del servidor en la nube.")
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
                                "cartoon, anime, illustration, 3d render, cgi"
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
                        neg_prompt = NSFW_BLOCK + neg_prompt

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
                                json=payload, timeout=300
                            )
                            if res_sd.status_code == 200:
                                b64 = res_sd.json()['images'][0]
                                if not img_prev:
                                    img_prev = b64
                                with open(path_out_png, "wb") as f:
                                    f.write(base64.b64decode(b64))
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
                        print(f"   ❌ Escena {i+1} falló en SD después de 3 intentos.")

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
        except:
            pass


print("⚡ NODO XEON ONLINE - FIX ANTI-BUCLE APLICADO")
while True:
    procesar()
    time.sleep(2)