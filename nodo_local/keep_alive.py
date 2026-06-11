import requests
import time

# Script para mantener Render despierto
# Corre esto en el Xeon en una terminal separada

RENDER_URL = "https://prompt-engineer-system-l2r6.onrender.com"
INTERVALO  = 10 * 60  # cada 10 minutos

print("💓 KEEP-ALIVE ACTIVO — Render no se dormirá.")
while True:
    try:
        res = requests.get(RENDER_URL, timeout=30)
        print(f"✅ Ping a Render: {res.status_code}")
    except Exception as e:
        print(f"⚠️ Ping fallido: {e}")
    time.sleep(INTERVALO)
