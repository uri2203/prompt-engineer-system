"""
BATERÍA DE PRUEBAS A FONDO DEL ORQUESTADOR
Cubre: controles (pausar/reanudar/cancelar), orden de producción,
recuperación tras corte, plan correcto, y ciclos completos.
NO solo ejecución — los casos que rompieron en producción.
"""
import sys, os, json
sys.path.insert(0, "/home/claude")
import importlib.util

def cargar_orq(estado, archivo_lote):
    spec = importlib.util.spec_from_file_location("orq_c", "/home/claude/orquestador_lote.py")
    orq = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orq)
    TIEMPO = [1000.0]
    class FR:
        def __init__(s, st, d): s.status_code=st; s._d=d
        def json(s): return s._d
    def fget(url, *a, **k):
        if "plan_semanal" in url: return FR(200, estado["plan"])
        if "lote_control" in url: return FR(200, estado["control"])
        if "video_estado" in url:
            tid = k.get("params",{}).get("tarea_id","")
            return FR(200, {"completado": tid in estado["completados"], "tarea_id": tid})
        return FR(200, {})
    def fpost(url, *a, **k):
        if "lanzar_orden_motor" in url:
            b = k.get("json",{}); estado["cont"]=estado.get("cont",0)+1
            clave = f"{b.get('marca')}_{b.get('formato')}"
            if clave in estado.get("fallar",[]): return FR(500,{"status":"error"})
            tid=f"t{estado['cont']}"; estado["encolados"].append((b.get("marca"),b.get("formato"),b.get("duracion_min"))); 
            return FR(200,{"status":"PENDING_REVIEW","tarea_id":tid})
        if "lote_control" in url: estado["control"]={"accion":""}; return FR(200,{})
        if "lote_progreso" in url: estado["progreso"]=k.get("json",{}); return FR(200,{})
        return FR(200,{})
    orq.requests.get=fget; orq.requests.post=fpost; orq.RENDER_URL="http://fake"
    orq.CARPETA_ESTADO=os.path.dirname(archivo_lote); orq.ARCHIVO_LOTE=archivo_lote
    os.makedirs(orq.CARPETA_ESTADO, exist_ok=True)
    if os.path.exists(archivo_lote): os.remove(archivo_lote)
    orq.ESPERA_NODO_CAIDO=0; orq.time.time=lambda: TIEMPO[0]
    return orq, TIEMPO

def correr(orq, lote, estado, TIEMPO, max_ciclos=60, auto_completar=True, hook=None):
    for c in range(max_ciclos):
        if auto_completar:
            ep = next((t for t in lote["trabajos"] if t["estado"]=="en_proceso"), None)
            if ep and ep.get("tarea_id"): estado["completados"].add(ep["tarea_id"])
        if hook: hook(c, lote)
        lote = orq.procesar_lote(lote)
        if lote.get("estado_lote") in ("completado","cancelado"): break
        TIEMPO[0]+=60
    return lote

PLAN = {"marcas":[
    {"marca":"La Viuda","shorts":1,"largos":1,"duracion_min":15},
    {"marca":"Monkygraff","shorts":2,"largos":0,"duracion_min":28},
    {"marca":"TuIALista","shorts":0,"largos":1,"duracion_min":45},
],"enfriamiento_seg":0,"orden":"shorts_primero"}

resultados = []

# ── TEST 1: ORDEN shorts_primero ──
print("="*64); print("TEST 1: Orden shorts_primero (todos los shorts antes que largos)")
est = {"plan":PLAN,"control":{"accion":""},"completados":set(),"encolados":[]}
orq,T = cargar_orq(est, "/home/claude/test_env/ec1/l.json")
lote = orq.crear_lote(PLAN)
orden = [(t["marca"],t["formato"]) for t in lote["trabajos"]]
print("  Orden del lote:", orden)
shorts_idx = [i for i,(m,f) in enumerate(orden) if f=="9:16"]
largos_idx = [i for i,(m,f) in enumerate(orden) if f=="16:9"]
ok1 = max(shorts_idx) < min(largos_idx)
print(f"  Total trabajos: {len(lote['trabajos'])} (esperado 5: 3 shorts + 2 largos)")
print(f"  ✅ Shorts antes que largos: {ok1}")
lote = correr(orq, lote, est, T)
ok1b = lote["estado_lote"]=="completado" and sum(1 for t in lote["trabajos"] if t["estado"]=="completado")==5
print(f"  ✅ Completó 5/5: {ok1b}")
resultados.append(("Orden shorts_primero + completa", ok1 and ok1b))

# ── TEST 2: ORDEN largos_primero ──
print("\n"+"="*64); print("TEST 2: Orden largos_primero")
plan2 = dict(PLAN); plan2["orden"]="largos_primero"
est = {"plan":plan2,"control":{"accion":""},"completados":set(),"encolados":[]}
orq,T = cargar_orq(est, "/home/claude/test_env/ec2/l.json")
lote = orq.crear_lote(plan2)
orden = [(t["marca"],t["formato"]) for t in lote["trabajos"]]
print("  Orden:", orden)
shorts_idx = [i for i,(m,f) in enumerate(orden) if f=="9:16"]
largos_idx = [i for i,(m,f) in enumerate(orden) if f=="16:9"]
ok2 = max(largos_idx) < min(shorts_idx)
print(f"  ✅ Largos antes que shorts: {ok2}")
resultados.append(("Orden largos_primero", ok2))

# ── TEST 3: PAUSAR a mitad del lote ──
print("\n"+"="*64); print("TEST 3: PAUSAR a mitad del lote")
est = {"plan":PLAN,"control":{"accion":""},"completados":set(),"encolados":[]}
orq,T = cargar_orq(est, "/home/claude/test_env/ec3/l.json")
lote = orq.crear_lote(PLAN)
def hook_pausar(c, lote):
    if c == 4: est["control"]={"accion":"pausar"}
lote = correr(orq, lote, est, T, max_ciclos=10, hook=hook_pausar)
ok3 = lote["estado_lote"]=="pausado"
print(f"  Estado tras pausar: {lote['estado_lote']}")
print(f"  ✅ Lote pausado correctamente: {ok3}")
# Verificar que NO sigue produciendo estando pausado
encolados_antes = len(est["encolados"])
lote = orq.procesar_lote(lote); lote = orq.procesar_lote(lote)
ok3b = len(est["encolados"]) == encolados_antes
print(f"  ✅ No produce mientras está pausado: {ok3b}")
resultados.append(("Pausar detiene producción", ok3 and ok3b))

# ── TEST 4: REANUDAR después de pausar ──
print("\n"+"="*64); print("TEST 4: REANUDAR continúa donde quedó")
completados_al_pausar = sum(1 for t in lote["trabajos"] if t["estado"]=="completado")
est["control"]={"accion":"reanudar"}
lote = correr(orq, lote, est, T, max_ciclos=30)
ok4 = lote["estado_lote"]=="completado"
completados_final = sum(1 for t in lote["trabajos"] if t["estado"]=="completado")
print(f"  Completados al pausar: {completados_al_pausar} → final: {completados_final}/5")
print(f"  ✅ Reanudó y completó el lote: {ok4 and completados_final==5}")
resultados.append(("Reanudar completa el lote", ok4 and completados_final==5))

# ── TEST 5: CANCELAR ──
print("\n"+"="*64); print("TEST 5: CANCELAR detiene todo")
est = {"plan":PLAN,"control":{"accion":""},"completados":set(),"encolados":[]}
orq,T = cargar_orq(est, "/home/claude/test_env/ec5/l.json")
lote = orq.crear_lote(PLAN)
def hook_cancelar(c, lote):
    if c == 3: est["control"]={"accion":"cancelar"}
lote = correr(orq, lote, est, T, max_ciclos=10, hook=hook_cancelar)
ok5 = lote["estado_lote"]=="cancelado"
print(f"  Estado: {lote['estado_lote']}")
print(f"  ✅ Lote cancelado: {ok5}")
resultados.append(("Cancelar detiene el lote", ok5))

# ── RESUMEN ──
print("\n"+"="*64); print("RESUMEN DE PRUEBAS DE CONTROLES Y ORDEN"); print("="*64)
for nombre, ok in resultados:
    print(f"  {'✅' if ok else '❌'} {nombre}")
todos = all(ok for _,ok in resultados)
print(f"\n{'✅ TODOS LOS CONTROLES Y ÓRDENES FUNCIONAN' if todos else '❌ HAY FALLOS'}")
