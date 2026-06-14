"""
TEST DE LOS ENDPOINTS DEL ORQUESTADOR (Etapa 2)
Simula que orquestador_lote.py llama a los 5 endpoints y verifica las respuestas.
"""
import os, sys, json

BASE = "/home/claude/test_env"
sys.path.insert(0, BASE)
sys.path.insert(0, "/home/claude")

import stubs_modulos
stubs_modulos.instalar_stubs()

import requests as _real_requests
AGENDA = {"agenda": [], "ejecuciones": {}}
GH_FILES = {}  # simula archivos en la rama diagnostico

class FakeResponse:
    def __init__(self, status, data): self.status_code = status; self._data = data
    def json(self): return self._data

def fake_get(url, *a, **k):
    import base64
    # Archivos de diagnostico (plan, control, progreso, agenda, cola)
    for nombre in ["plan_lote", "lote_control", "lote_progreso", "agenda", "cola_ordenes"]:
        if f"{nombre}.json" in url:
            if nombre in GH_FILES:
                contenido = base64.b64encode(json.dumps(GH_FILES[nombre]).encode()).decode()
                return FakeResponse(200, {"content": contenido, "sha": "x"})
            return FakeResponse(404, {})
    return FakeResponse(200, {"items": []})

def fake_put(url, *a, **k):
    import base64
    body = k.get("json", {})
    for nombre in ["plan_lote", "lote_control", "lote_progreso", "agenda", "cola_ordenes"]:
        if f"{nombre}.json" in url:
            GH_FILES[nombre] = json.loads(base64.b64decode(body.get("content","")).decode())
    return FakeResponse(200, {"commit": {"sha": "x"}})

_real_requests.get = fake_get
_real_requests.put = fake_put
os.environ["GH_DIAG_TOKEN"] = "fake"
os.chdir("/home/claude")

import importlib.util
spec = importlib.util.spec_from_file_location("app_test", "/home/claude/app.py")
app_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_mod)
app_mod.requests.get = fake_get
app_mod.requests.put = fake_put
app = app_mod.app
app.config["TESTING"] = True
client = app.test_client()
with client.session_transaction() as s:
    s["user"] = "test"

print("=" * 60)
print("TEST ENDPOINTS DEL ORQUESTADOR")
print("=" * 60)

# TEST 1: Guardar y leer el plan del lote
print("\n[1] Plan del lote (guardar por marca + leer)...")
plan = {
    "marcas": [
        {"marca": "La Viuda", "shorts": 2, "largos": 1, "duracion_min": 28},
        {"marca": "Monkygraff", "shorts": 3, "largos": 2, "duracion_min": 45},
    ],
    "enfriamiento_seg": 180, "orden": "shorts_primero",
}
r = client.post("/api/bot/plan_semanal", json=plan)
print(f"    Guardar: HTTP {r.status_code}")
r2 = client.get("/api/bot/plan_semanal")
leido = r2.get_json()
print(f"    Marcas en el plan: {len(leido.get('marcas', []))}")
if leido.get("marcas"):
    for m in leido["marcas"]:
        print(f"      {m['marca']}: {m['shorts']} shorts + {m['largos']} largos ({m['duracion_min']}min)")
    print("    ✅ Plan persiste correctamente")

# TEST 2: Lanzar orden del motor
print("\n[2] Lanzar orden del motor (un video del lote)...")
r = client.post("/api/bot/lanzar_orden_motor", json={"marca": "La Viuda", "formato": "9:16"})
data = r.get_json()
tid = data.get("tarea_id")
print(f"    HTTP {r.status_code} | tarea_id: {str(tid)[:12] if tid else 'NINGUNO'}")
print(f"    {'✅ Orden lanzada' if tid else '❌ No se lanzó'}")

# TEST 3: Estado del video (antes y después de completarse)
print("\n[3] Estado del video (completado o no)...")
r = client.get(f"/api/bot/video_estado?tarea_id={tid}")
print(f"    Antes de terminar: completado={r.get_json().get('completado')}")
# Simular que el worker reporta el ensamblaje terminado
app_mod._videos_completados.add(tid)
r2 = client.get(f"/api/bot/video_estado?tarea_id={tid}")
print(f"    Después de terminar: completado={r2.get_json().get('completado')}")
print(f"    {'✅ Detecta video terminado' if r2.get_json().get('completado') else '❌ No detecta'}")

# TEST 4: Control del lote (pausar / reanudar / cancelar)
print("\n[4] Control del lote (pausar → reanudar → cancelar)...")
for accion in ["pausar", "reanudar", "cancelar", ""]:
    client.post("/api/bot/lote_control", json={"accion": accion})
    r = client.get("/api/bot/lote_control")
    actual = r.get_json().get("accion")
    estado = "✅" if actual == accion else "❌"
    print(f"    {estado} Acción '{accion or '(ninguna)'}' → leída: '{actual}'")

# TEST 5: Progreso del lote
print("\n[5] Progreso del lote (reportar + leer)...")
client.post("/api/bot/lote_progreso", json={
    "estado_lote": "produciendo", "total": 8, "completados": 3,
    "trabajo_actual": "Monkygraff largo 45min",
})
r = client.get("/api/bot/lote_progreso")
prog = r.get_json()
print(f"    Estado: {prog.get('estado_lote')} | {prog.get('completados')}/{prog.get('total')} | {prog.get('trabajo_actual','')}")
print(f"    {'✅ Progreso funciona' if prog.get('total') == 8 else '❌ Falla'}")

print("\n" + "=" * 60)
print("FIN DEL TEST DEL ORQUESTADOR")
print("=" * 60)
