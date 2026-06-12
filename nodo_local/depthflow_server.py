"""
DEPTHFLOW SERVER — Dark Factory Sistema Pinpinela
Corre en el PC GPU (192.168.0.215), junto a Stable Diffusion.
Recibe una imagen + parámetros y devuelve un clip parallax 2.5D.

El worker (en el Xeon) le manda cada escena por HTTP.

ARRANQUE (en el PC GPU, terminal NORMAL, no admin):
    D:\DepthFlow_env\Scripts\activate
    python depthflow_server.py

Escucha en el puerto 8500.
"""
import os
import subprocess
import tempfile
import uuid
import random
import threading
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

# Candado: DepthFlow usa la GPU, solo puede procesar UNA imagen a la vez.
# Las peticiones que lleguen mientras está ocupado ESPERAN su turno (no se rechazan).
_gpu_lock = threading.Lock()

# ── Rutas del entorno DepthFlow en el PC GPU ─────────────────────────────────
DEPTHFLOW_EXE = r"D:\DepthFlow_env\Scripts\depthflow.exe"
CARPETA_TMP   = r"D:\DepthFlow_env\tmp_parallax"
os.makedirs(CARPETA_TMP, exist_ok=True)

# ── Presets de movimiento variados ───────────────────────────────────────────
# Cada preset es una animación distinta de DepthFlow. Variamos para que no
# todas las escenas se muevan igual. Algunos presets aceptan intensidad.
PRESETS_MOVIMIENTO = [
    "orbital",      # órbita alrededor de un punto (cinematográfico)
    "zoom",         # acercamiento con profundidad
    "dolly",        # dolly zoom (efecto vértigo sutil)
    "horizontal",   # desplazamiento lateral
    "vertical",     # desplazamiento vertical
    "circle",       # movimiento circular suave
]

# Intensidad por canal: terror = lento/sutil; comedia = más movido
INTENSIDAD_CANAL = {
    "laviuda":          {"height": "0.15", "isometric": "0.4"},  # sutil, inquietante
    "la viuda":         {"height": "0.15", "isometric": "0.4"},
    "monkygraff":       {"height": "0.20", "isometric": "0.5"},
    "filtradomx":       {"height": "0.18", "isometric": "0.5"},
    "laesquinarandom":  {"height": "0.30", "isometric": "0.6"},  # más dinámico
    "la esquina random":{"height": "0.30", "isometric": "0.6"},
    "tuialista":        {"height": "0.25", "isometric": "0.5"},
}
INTENSIDAD_DEFAULT = {"height": "0.22", "isometric": "0.5"}


def _elegir_preset(marca, escena_idx, seed_extra=""):
    """Elige un preset variado y determinista según marca+escena.
    Determinista = la misma escena siempre da el mismo movimiento (reproducible)."""
    rnd = random.Random(f"{marca}_{escena_idx}_{seed_extra}")
    return rnd.choice(PRESETS_MOVIMIENTO)


def generar_parallax(ruta_img, ruta_salida, marca, escena_idx, duracion, fps, w, h):
    """Llama a DepthFlow para convertir una imagen en un clip parallax.
    Reintenta automáticamente si falla (DepthFlow a veces falla de forma intermitente)."""
    marca_l = marca.lower().strip()
    intensidad = INTENSIDAD_CANAL.get(marca_l, INTENSIDAD_DEFAULT)
    preset = _elegir_preset(marca, escena_idx)

    cmd = [
        DEPTHFLOW_EXE,
        "input", "-i", ruta_img,
        "dav2",                          # DepthAnythingV2 (rápido, buena calidad)
        preset,                          # el preset variado elegido
        "main",
        "-t", str(duracion),
        "-o", ruta_salida,
        "--width", str(w),
        "--height", str(h),
        "--fps", str(fps),
    ]

    ultimo_error = ""
    # Hasta 3 intentos: DepthFlow a veces falla por VRAM ocupada momentáneamente
    for intento in range(1, 4):
        try:
            # Limpiar salida previa fallida
            if os.path.exists(ruta_salida):
                try: os.remove(ruta_salida)
                except: pass

            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

            if os.path.exists(ruta_salida) and os.path.getsize(ruta_salida) > 1000:
                if intento > 1:
                    print(f"   [DEPTHFLOW] escena {escena_idx} OK en intento {intento}")
                return True, preset

            # Falló: capturar el error real de DepthFlow
            ultimo_error = (r.stderr or r.stdout or "sin salida")[-400:]
            print(f"   [DEPTHFLOW] escena {escena_idx} intento {intento}/3 FALLÓ: {ultimo_error[:200]}")

            # Pausa para que la GPU libere VRAM antes de reintentar
            import time as _t
            _t.sleep(3)

        except subprocess.TimeoutExpired:
            ultimo_error = "Timeout (>180s)"
            print(f"   [DEPTHFLOW] escena {escena_idx} intento {intento}/3: TIMEOUT")
            import time as _t
            _t.sleep(3)
        except Exception as e:
            ultimo_error = str(e)
            print(f"   [DEPTHFLOW] escena {escena_idx} intento {intento}/3 EXCEPCIÓN: {e}")
            import time as _t
            _t.sleep(3)

    return False, f"Falló tras 3 intentos. Último error: {ultimo_error}"


@app.route("/parallax", methods=["POST"])
def parallax():
    """Recibe imagen + parámetros, devuelve clip parallax."""
    if "imagen" not in request.files:
        return jsonify({"error": "Falta la imagen"}), 400

    img = request.files["imagen"]
    marca       = request.form.get("marca", "La Viuda")
    escena_idx  = int(request.form.get("escena_idx", 0))
    duracion    = float(request.form.get("duracion", 5.0))
    fps         = int(request.form.get("fps", 30))
    w           = int(request.form.get("width", 1024))
    h           = int(request.form.get("height", 1024))

    job = uuid.uuid4().hex[:8]
    ruta_img    = os.path.join(CARPETA_TMP, f"{job}_in.png")
    ruta_salida = os.path.join(CARPETA_TMP, f"{job}_out.mp4")
    img.save(ruta_img)

    # Candado: una generación a la vez (la GPU no puede con dos simultáneas).
    # Las peticiones del worker que lleguen mientras está ocupado esperan aquí.
    with _gpu_lock:
        ok, info = generar_parallax(ruta_img, ruta_salida, marca, escena_idx, duracion, fps, w, h)

    # Limpieza de la imagen de entrada
    try: os.remove(ruta_img)
    except: pass

    if ok:
        # Leer el video a memoria, borrar el archivo, y enviar (no deja basura en disco)
        try:
            with open(ruta_salida, "rb") as f:
                datos_video = f.read()
            os.remove(ruta_salida)
        except Exception as e:
            return jsonify({"error": f"No se pudo leer salida: {e}"}), 500
        from flask import Response
        resp = Response(datos_video, mimetype="video/mp4")
        resp.headers["X-Preset"] = info
        return resp
    else:
        # Limpiar salida fallida si existe
        try: os.remove(ruta_salida)
        except: pass
        return jsonify({"error": info}), 500


@app.route("/health", methods=["GET"])
def health():
    """Para que el worker verifique si el servidor está vivo."""
    return jsonify({"status": "ok", "depthflow": os.path.exists(DEPTHFLOW_EXE)})


if __name__ == "__main__":
    print("=" * 50)
    print("DEPTHFLOW SERVER — Sistema Pinpinela")
    print(f"DepthFlow: {DEPTHFLOW_EXE}")
    print(f"Existe: {os.path.exists(DEPTHFLOW_EXE)}")
    print(f"Temp: {CARPETA_TMP}")
    print("Escuchando en puerto 8500...")
    print("=" * 50)
    app.run(host="0.0.0.0", port=8500, threaded=True)
