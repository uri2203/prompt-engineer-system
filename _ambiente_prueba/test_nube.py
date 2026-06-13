"""
TEST DEL SISTEMA EN LA NUBE (app.py / Render)
Prueba la lógica real de app.py SIN desplegar: agenda, cron, persistencia, endpoints.
Usa el cliente de prueba de Flask (no necesita servidor ni red).
"""
import os
import sys
import json
import types

BASE = "/home/claude/test_env"
sys.path.insert(0, BASE)
sys.path.insert(0, "/home/claude")

# 1. Instalar stubs de los módulos pesados ANTES de importar app
import stubs_modulos
stubs_modulos.instalar_stubs()

# 2. Evitar que app.py escriba al GitHub real: simular la agenda en un archivo local
#    Parcheamos requests para que las llamadas a la API de agenda usen un dict en memoria
import requests as _real_requests

AGENDA_SIMULADA = {"agenda": [], "ejecuciones": {}}
CRON_LOG_SIMULADO = []

class FakeResponse:
    def __init__(self, status, data):
        self.status_code = status
        self._data = data
    def json(self): return self._data

_orig_get = _real_requests.get
_orig_put = _real_requests.put

def fake_get(url, *a, **k):
    if "agenda.json" in url:
        import base64
        contenido = base64.b64encode(json.dumps(AGENDA_SIMULADA).encode()).decode()
        return FakeResponse(200, {"content": contenido, "sha": "fake_sha"})
    if "_diagnostico" in url:
        return FakeResponse(404, {})
    # Llamadas a YouTube u otras: devolver vacío
    return FakeResponse(200, {"items": []})

def fake_put(url, *a, **k):
    if "agenda.json" in url:
        # Decodificar lo que se quiere guardar y actualizarlo en memoria
        import base64
        body = k.get("json", {})
        contenido = base64.b64decode(body.get("content", "")).decode()
        global AGENDA_SIMULADA
        AGENDA_SIMULADA = json.loads(contenido)
        return FakeResponse(200, {"commit": {"sha": "fake"}})
    return FakeResponse(200, {"commit": {"sha": "fake"}})

_real_requests.get = fake_get
_real_requests.put = fake_put

# 3. Configurar token falso para que app use la rama de GitHub
os.environ["GH_DIAG_TOKEN"] = "fake_token_para_prueba"

# 4. Importar app.py (con los stubs activos)
os.chdir("/home/claude")
import importlib.util
spec = importlib.util.spec_from_file_location("app_test", "/home/claude/app.py")
app_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_mod)
app_mod.requests.get = fake_get
app_mod.requests.put = fake_put
try:
    os.remove(app_mod.CRON_FILE)
except Exception:
    pass
app = app_mod.app
app.config["TESTING"] = True
client = app.test_client()

# Saltarse el login: simular sesión
def con_sesion(c):
    with c.session_transaction() as s:
        s["user"] = "test"
    return c

print("=" * 60)
print("TEST DEL SISTEMA EN LA NUBE (app.py)")
print("=" * 60)

con_sesion(client)

# ── TEST 1: Programar un video en la agenda y verificar que PERSISTE ──
print("\n[TEST 1] Programar video largo y verificar persistencia...")
from datetime import datetime, timezone, timedelta
tz = timezone(timedelta(hours=-6))
manana = (datetime.now(tz) + timedelta(days=1)).strftime("%Y-%m-%d")

resp = client.post("/api/bot/cron/config", json={
    "accion": "agregar", "marca": "La Viuda", "formato": "16:9",
    "duracion_min": 15, "fecha": manana, "hora": "10:00", "repetir": "una_vez"
})
print(f"    Guardar: HTTP {resp.status_code}")

# Leer la agenda de vuelta (simula que Render reinició y vuelve a leer)
resp2 = client.get("/api/bot/cron/config")
agenda = resp2.get_json().get("agenda", [])
print(f"    Entradas en agenda tras guardar: {len(agenda)}")
if agenda:
    e = agenda[0]
    print(f"    ✅ PERSISTE: {e.get('marca')} | {e.get('formato')} | {e.get('duracion_min')}min | {e.get('fecha')} {e.get('hora')}")
else:
    print(f"    ❌ NO PERSISTE — la agenda quedó vacía (BUG)")

# ── TEST 2: Verificar que el cron dispara cuando llega la hora ──
print("\n[TEST 2] Simular que llega la hora y el cron dispara...")
ahora = datetime.now(tz)
hace_un_min = (ahora - timedelta(minutes=1)).strftime("%H:%M")
AGENDA_SIMULADA["agenda"] = [{
    "id": "test1", "marca": "La Viuda", "formato": "9:16",
    "duracion_min": None, "fecha": ahora.strftime("%Y-%m-%d"),
    "hora": hace_un_min, "repetir": "una_vez",
    "activo": True, "ejecutado": False,
}]
app_mod._worker_estado["ocupado"] = False
resp3 = client.post("/api/bot/cron/tick")
data3 = resp3.get_json()
print(f"    Hora entrada: {hace_un_min} | Tick respondió: {data3.get('status')}")
if data3.get("status") == "disparado":
    print(f"    ✅ DISPARÓ: {data3.get('ordenes')}")
elif data3.get("status") == "worker_ocupado":
    print(f"    ⚠️ No disparó: worker reportado como ocupado")
else:
    print(f"    Detalle: {data3}")

# ── TEST 3: Verificar que un short llega a la cola de renderizado ──
print("\n[TEST 3] Verificar que la orden llegó a la cola del worker...")
import time
time.sleep(2)  # dar tiempo al thread de fondo
cola = len(app_mod.cola_de_renderizado)
print(f"    Tareas en cola_de_renderizado: {cola}")
print(f"    {'✅ La orden llegó a la cola' if cola > 0 else '❌ La cola está vacía (la orden no llegó)'}")

# ── TEST 4: Worker hace polling tras 'sueño' de Render ──
print("\n[TEST 4] Worker hace polling (simula que Render durmió y perdió memoria)...")
app_mod.cola_de_renderizado.clear()  # simular pérdida de memoria por sleep
resp4 = client.post("/api/nodo/polling", json={"nodo_id": "XEON_ASSEMBLER"})
data4 = resp4.get_json()
if data4.get("hay_trabajo"):
    t = data4["tarea"]
    print(f"    ✅ Worker RECIBIÓ la orden: {t.get('marca')} {str(t.get('id',''))[:8]}")
    print(f"    (Sobrevivió al sueño de Render gracias a la persistencia en GitHub)")
else:
    print(f"    ❌ El polling NO entregó la orden (se perdió con el sueño de Render)")

# ── TEST 5: Orden manual con duración (15/28/45 min) ──
print("\n[TEST 5] Orden manual de video largo con duración 45 min...")
resp5 = client.post("/api/bot/lanzar_orden", json={
    "marca": "Monkygraff", "formato": "16:9", "duracion_min": 45,
    "premisa": "Test de duración"
})
data5 = resp5.get_json()
if resp5.status_code == 200 and data5.get("status") in ("PENDING_REVIEW", "ok"):
    print(f"    ✅ Orden de 45 min aceptada: {data5.get('num_escenas', '?')} escenas, formato {data5.get('formato')}")
else:
    print(f"    Respuesta: HTTP {resp5.status_code} {data5}")

print("\n" + "=" * 60)
print("FIN DEL TEST DE LA NUBE")
print("=" * 60)
