import requests
import time

# Script para mantener Render despierto + reportar estado de nodos locales.
# Corre esto en el Xeon en una terminal separada.
# El Xeon SÍ puede ver tanto los nodos locales como Render, por eso reporta desde aquí.

RENDER_URL = "https://prompt-engineer-system-l2r6.onrender.com"
INTERVALO  = 60  # cada 60 segundos (ping a nodos + keep-alive)

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

print("💓 KEEP-ALIVE + MONITOR DE NODOS ACTIVO")
contador_keepalive = 0

while True:
    # 1. Ping a cada nodo local
    estado = {clave: ping(url) for clave, url in NODOS.items()}

    # 2. Reportar estado de nodos a Render
    try:
        requests.post(f"{RENDER_URL}/api/nodos/reportar", json=estado, timeout=30)
        print(f"📡 Nodos: SD={estado['sd']} VOZ={estado['voz']} PARALLAX={estado['parallax']}")
    except Exception as e:
        print(f"⚠️ No se pudo reportar nodos: {e}")

    # 3. Keep-alive de Render (cada 10 min para no gastar las 750h)
    contador_keepalive += 1
    if contador_keepalive >= 10:  # 10 ciclos de 60s = 10 min
        try:
            res = requests.get(RENDER_URL, timeout=30)
            print(f"✅ Keep-alive Render: {res.status_code}")
        except Exception as e:
            print(f"⚠️ Keep-alive fallido: {e}")
        contador_keepalive = 0

    time.sleep(INTERVALO)
