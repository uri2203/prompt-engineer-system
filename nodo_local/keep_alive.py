import requests
import time

# Script para mantener Render despierto + reportar estado de nodos locales.
# Corre esto en el Xeon en una terminal separada.
# El Xeon SÍ puede ver tanto los nodos locales como Render, por eso reporta desde aquí.

RENDER_URL = "https://prompt-engineer-system-l2r6.onrender.com"
INTERVALO  = 60  # cada 60 segundos (ping a nodos + keep-alive)

# Archivos de log/estado del Xeon (para reportar diagnóstico a Render)
import os
LOG_WORKER = r"C:\NODO_PINPINELA\worker_log.txt"
WORKER_PY  = r"C:\NODO_PINPINELA\worker_cpu.py"
ESTADO_LOTE = r"C:\NODO_PINPINELA\estado_lote\lote_actual.json"

# Nodos locales a vigilar
NODOS = {
    "sd":       "http://192.168.0.215:7861/sdapi/v1/options",  # Stable Diffusion
    "voz":      "http://192.168.0.251:8000",                    # Motor de voz
    "parallax": "http://192.168.0.215:8500/health",            # DepthFlow
}

def ping(url, timeout=6):
    try:
        requests.get(url, timeout=timeout)
        return "on"   # cualquier respuesta HTTP = vivo
    except Exception:
        return "off"

def reportar_diagnostico():
    """Lee el log del worker y el estado del lote, los reporta a Render para diagnóstico remoto."""
    import json as _json
    datos = {}
    # Versión del worker (nº de líneas)
    try:
        with open(WORKER_PY, encoding="utf-8") as f:
            datos["worker_version"] = f"{len(f.readlines())} lineas"
    except Exception:
        datos["worker_version"] = "no encontrado"
    # Últimas líneas del log del worker
    try:
        with open(LOG_WORKER, encoding="utf-8", errors="ignore") as f:
            lineas = f.readlines()
            datos["worker_logs"] = [l.rstrip() for l in lineas[-50:]]
            # buscar último error
            errores = [l.rstrip() for l in lineas if "error" in l.lower() or "⚠️" in l or "❌" in l]
            datos["ultimo_error"] = errores[-1] if errores else ""
    except Exception:
        datos["worker_logs"] = ["(sin log; el worker debe redirigir su salida a worker_log.txt)"]
    # Estado del lote del orquestador
    try:
        with open(ESTADO_LOTE, encoding="utf-8") as f:
            datos["orquestador_estado"] = _json.load(f)
    except Exception:
        datos["orquestador_estado"] = {}
    try:
        requests.post(f"{RENDER_URL}/api/diagnostico/reportar", json=datos, timeout=20)
    except Exception:
        pass

print("💓 KEEP-ALIVE + MONITOR DE NODOS ACTIVO")
contador_keepalive = 0

while True:
    # Consultar a Render si el worker está ocupado generando un video.
    # Si lo está, NO hacemos ping a los nodos de la GPU (SD y DepthFlow) para
    # no interferir con la generación de parallax (evita saturar la GPU).
    worker_ocupado = False
    try:
        rw = requests.get(f"{RENDER_URL}/api/nodo/worker_estado", timeout=10)
        worker_ocupado = rw.json().get("ocupado", False)
    except Exception:
        worker_ocupado = False

    # 1. Ping a cada nodo local (saltando los de GPU si el worker está ocupado)
    estado = {}
    for clave, url in NODOS.items():
        if worker_ocupado and clave in ("sd", "parallax"):
            estado[clave] = "on"   # no molestar a la GPU mientras genera
        else:
            estado[clave] = ping(url)

    # 2. Reportar estado de nodos a Render
    try:
        requests.post(f"{RENDER_URL}/api/nodos/reportar", json=estado, timeout=30)
        ocup = " (worker ocupado, GPU sin molestar)" if worker_ocupado else ""
        print(f"📡 Nodos: SD={estado['sd']} VOZ={estado['voz']} PARALLAX={estado['parallax']}{ocup}")
    except Exception as e:
        print(f"⚠️ No se pudo reportar nodos: {e}")

    # 2b. Reportar diagnóstico (logs del worker, estado del lote) para revisión remota
    reportar_diagnostico()

    # 3. Tick del cronjob del Bot Pinpinela (dispara órdenes programadas)
    try:
        rc = requests.post(f"{RENDER_URL}/api/bot/cron/tick", timeout=30)
        estado_cron = rc.json().get("status", "?")
        if estado_cron == "disparado":
            print(f"🤖 CRONJOB DISPARADO: {rc.json().get('ordenes', [])}")
    except Exception as e:
        pass

    # 4. Keep-alive de Render (cada 10 min para no gastar las 750h)
    contador_keepalive += 1
    if contador_keepalive >= 10:  # 10 ciclos de 60s = 10 min
        try:
            res = requests.get(RENDER_URL, timeout=30)
            print(f"✅ Keep-alive Render: {res.status_code}")
        except Exception as e:
            print(f"⚠️ Keep-alive fallido: {e}")
        contador_keepalive = 0

    time.sleep(INTERVALO)
