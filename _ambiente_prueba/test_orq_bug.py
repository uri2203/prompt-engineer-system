"""
REPRODUCE EL BUG DE PRODUCCIÓN:
- Lote de 7 videos de varios canales
- El video 1 (short La Viuda) SÍ se encola
- El video 2 FALLA al encolar (Gemini error) → ¿se atasca el orquestador?
Verifica: orden correcto, progreso avanza, controles (pausar/cancelar) funcionan.
"""
import sys, os, json, time
sys.path.insert(0, "/home/claude")
sys.path.insert(0, "/home/claude/test_env")

# Cargar el orquestador REAL parcheando sus llamadas de red y rutas
import importlib.util
spec = importlib.util.spec_from_file_location("orq", "/home/claude/orquestador_lote.py")
orq = importlib.util.module_from_spec(spec)

# Estado simulado del "servidor"
ESTADO = {
    "plan": {
        "marcas": [
            {"marca": "La Viuda", "shorts": 1, "largos": 1, "duracion_min": 15},
            {"marca": "Monkygraff", "shorts": 0, "largos": 1, "duracion_min": 28},
            {"marca": "FiltradoMX", "shorts": 1, "largos": 1, "duracion_min": 15},
            {"marca": "LaesquinaRandom", "shorts": 1, "largos": 1, "duracion_min": 15},
        ],
        "enfriamiento_seg": 0,
        "orden": "shorts_primero",
    },
    "control": {"accion": ""},
    "progreso": {},
    "encolados": [],          # tareas que se encolaron OK
    "completados": set(),     # tareas marcadas como listas
    "fallar_encolado_en": [], # lista de marca+formato que deben FALLAR al encolar
    "contador_encolado": 0,
}

class FakeResp:
    def __init__(self, status, data): self.status_code = status; self._data = data
    def json(self): return self._data

def fake_get(url, *a, **k):
    if "plan_semanal" in url:
        return FakeResp(200, ESTADO["plan"])
    if "lote_control" in url:
        return FakeResp(200, ESTADO["control"])
    if "video_estado" in url:
        tid = k.get("params", {}).get("tarea_id", "")
        return FakeResp(200, {"completado": tid in ESTADO["completados"], "tarea_id": tid})
    # ping de nodos: siempre vivos
    return FakeResp(200, {})

def fake_post(url, *a, **k):
    if "lanzar_orden_motor" in url:
        body = k.get("json", {})
        clave = f"{body.get('marca')}_{body.get('formato')}"
        ESTADO["contador_encolado"] += 1
        # ¿Este debe fallar?
        if clave in ESTADO["fallar_encolado_en"]:
            return FakeResp(500, {"status": "error", "message": "Fallo puntual de red simulado"})
        tid = f"tarea_{ESTADO['contador_encolado']}"
        ESTADO["encolados"].append({"tarea_id": tid, "marca": body.get("marca"), "formato": body.get("formato")})
        return FakeResp(200, {"status": "PENDING_REVIEW", "tarea_id": tid})
    if "lote_control" in url:  # consumir control
        ESTADO["control"] = {"accion": ""}
        return FakeResp(200, {})
    if "lote_progreso" in url:
        ESTADO["progreso"] = k.get("json", {})
        return FakeResp(200, {})
    return FakeResp(200, {})

# Parchear requests del orquestador
import requests as _r
orq_requests_get = fake_get
orq_requests_post = fake_post

# Inyectar antes de ejecutar el modulo
spec.loader.exec_module(orq)
orq.requests.get = fake_get
orq.requests.post = fake_post
orq.RENDER_URL = "http://fake"
orq.ARCHIVO_LOTE = "/home/claude/test_env/estado_lote_bug/lote.json"
orq.CARPETA_ESTADO = "/home/claude/test_env/estado_lote_bug"
os.makedirs(orq.CARPETA_ESTADO, exist_ok=True)
# Limpiar estado previo
if os.path.exists(orq.ARCHIVO_LOTE): os.remove(orq.ARCHIVO_LOTE)
orq.ESPERA_NODO_CAIDO = 0

print("="*64)
print("REPRODUCCIÓN DEL BUG: video 2 falla al encolar")
print("="*64)

# Hacer que el SEGUNDO short (FiltradoMX 9:16) falle al encolar
ESTADO["fallar_encolado_en"] = ["FiltradoMX_9:16"]

# Crear el lote
lote = orq.crear_lote(ESTADO["plan"])
print(f"\nLote creado con {len(lote['trabajos'])} trabajos:")
for t in lote["trabajos"]:
    dur = f" {t['duracion_min']}min" if t.get("duracion_min") else ""
    print(f"  Video {t['n']}: {t['marca']} {t['formato']}{dur}")

# Simular ciclos del orquestador (cada ciclo = procesar_lote)
print("\n--- Simulando ciclos de producción ---")
MAX_CICLOS = 40
import time as _t
TIEMPO_SIM = [_t.time()]
# Parchear time.time del orquestador para simular avance de tiempo
_orig_time = orq.time.time
def fake_time():
    return TIEMPO_SIM[0]
orq.time.time = fake_time

for ciclo in range(MAX_CICLOS):
    # Auto-completar el video que está en proceso (simula que el worker terminó)
    en_proc = next((t for t in lote["trabajos"] if t["estado"]=="en_proceso"), None)
    if en_proc and en_proc.get("tarea_id"):
        ESTADO["completados"].add(en_proc["tarea_id"])
    lote = orq.procesar_lote(lote)
    completados = sum(1 for t in lote["trabajos"] if t["estado"]=="completado")
    estado = lote.get("estado_lote")
    msg = lote.get("mensaje","")[:50]
    if ciclo < 25 or completados > 0:
        print(f"  Ciclo {ciclo:2d}: {completados}/{len(lote['trabajos'])} | {estado} | {msg}")
    if estado in ("completado","cancelado"):
        break
    # Avanzar el tiempo simulado 60s por ciclo (supera enfriamiento 0 y espera reintento 45s)
    TIEMPO_SIM[0] += 60

print(f"\n--- RESULTADO ---")
completados = sum(1 for t in lote['trabajos'] if t['estado']=='completado')
print(f"Completados: {completados}/{len(lote['trabajos'])}")
print(f"Estado final: {lote.get('estado_lote')}")
print(f"Encolados OK: {[e['marca']+' '+e['formato'] for e in ESTADO['encolados']]}")
estados = {}
for t in lote["trabajos"]:
    estados[t["estado"]] = estados.get(t["estado"],0)+1
print(f"Estados de trabajos: {estados}")
if completados < len(lote['trabajos']) and lote.get('estado_lote') != 'completado':
    print("\n❌ BUG CONFIRMADO: el orquestador se ATASCÓ — no completó el lote")
    print("   El video que falló al encolar bloqueó todos los siguientes.")
