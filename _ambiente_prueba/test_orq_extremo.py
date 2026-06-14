"""
PRUEBAS EXTREMAS — los casos que rompen en producción real.
"""
import sys, os, json
sys.path.insert(0, "/home/claude")
import importlib.util

def cargar_orq(estado, archivo_lote):
    spec = importlib.util.spec_from_file_location("orq_x", "/home/claude/orquestador_lote.py")
    orq = importlib.util.module_from_spec(spec); spec.loader.exec_module(orq)
    TIEMPO=[1000.0]
    class FR:
        def __init__(s,st,d): s.status_code=st; s._d=d
        def json(s): return s._d
    def fget(url,*a,**k):
        if "plan_semanal" in url: return FR(200,estado["plan"])
        if "lote_control" in url: return FR(200,estado["control"])
        if "video_estado" in url:
            tid=k.get("params",{}).get("tarea_id","")
            return FR(200,{"completado":tid in estado["completados"],"tarea_id":tid})
        if "7861" in url or "8000" in url:  # ping nodos
            return FR(200,{}) if estado.get("nodos_vivos",True) else (_ for _ in ()).throw(Exception("caido"))
        return FR(200,{})
    def fpost(url,*a,**k):
        if "lanzar_orden_motor" in url:
            b=k.get("json",{}); estado["cont"]=estado.get("cont",0)+1
            clave=f"{b.get('marca')}_{b.get('formato')}"
            if clave in estado.get("fallar",[]): return FR(500,{"status":"error"})
            tid=f"t{estado['cont']}"; estado["encolados"].append((b.get("marca"),b.get("formato")))
            return FR(200,{"status":"PENDING_REVIEW","tarea_id":tid})
        if "lote_control" in url: estado["control"]={"accion":""}; return FR(200,{})
        if "lote_progreso" in url: estado["progreso"]=k.get("json",{}); return FR(200,{})
        return FR(200,{})
    orq.requests.get=fget; orq.requests.post=fpost; orq.RENDER_URL="http://fake"
    orq.CARPETA_ESTADO=os.path.dirname(archivo_lote); orq.ARCHIVO_LOTE=archivo_lote
    os.makedirs(orq.CARPETA_ESTADO,exist_ok=True)
    if os.path.exists(archivo_lote): os.remove(archivo_lote)
    orq.ESPERA_NODO_CAIDO=0; orq.time.time=lambda:TIEMPO[0]
    return orq,TIEMPO

PLAN={"marcas":[{"marca":"La Viuda","shorts":1,"largos":1,"duracion_min":15},
                {"marca":"Monkygraff","shorts":1,"largos":1,"duracion_min":28}],
      "enfriamiento_seg":0,"orden":"shorts_primero"}
res=[]

# TEST A: CLICS REPETIDOS en reanudar (lo que atascó la cola antes)
print("="*64); print("TEST A: clics repetidos en 'reanudar' no duplican producción")
est={"plan":PLAN,"control":{"accion":""},"completados":set(),"encolados":[]}
orq,T=cargar_orq(est,"/home/claude/test_env/ex_a/l.json")
lote=orq.crear_lote(PLAN)
# Simular 5 clics de reanudar seguidos mientras produce
for c in range(20):
    ep=next((t for t in lote["trabajos"] if t["estado"]=="en_proceso"),None)
    if ep and ep.get("tarea_id"): est["completados"].add(ep["tarea_id"])
    if c in (1,2,3): est["control"]={"accion":"reanudar"}  # clics repetidos
    lote=orq.procesar_lote(lote)
    if lote.get("estado_lote")=="completado": break
    T[0]+=60
# No debe haber encolado mas videos que trabajos
okA = len(est["encolados"]) <= len(lote["trabajos"])
print(f"  Trabajos: {len(lote['trabajos'])} | Encolados: {len(est['encolados'])}")
print(f"  ✅ No duplica producción con clics repetidos: {okA}")
res.append(("Clics repetidos no duplican", okA))

# TEST B: RECUPERACIÓN tras corte de luz (video en proceso → reintenta)
print("\n"+"="*64); print("TEST B: recuperación tras corte de luz")
est={"plan":PLAN,"control":{"accion":""},"completados":set(),"encolados":[]}
orq,T=cargar_orq(est,"/home/claude/test_env/ex_b/l.json")
lote=orq.crear_lote(PLAN)
# Avanzar hasta tener un video en proceso
for c in range(3):
    lote=orq.procesar_lote(lote); T[0]+=60
en_proc=[t for t in lote["trabajos"] if t["estado"]=="en_proceso"]
print(f"  Video en proceso antes del corte: {len(en_proc)}")
orq.guardar_lote(lote)
# Simular reinicio: recargar desde disco como hace main()
lote_recuperado = orq.leer_lote()
for t in lote_recuperado["trabajos"]:
    if t["estado"]=="en_proceso":
        t["estado"]="pendiente"  # lo que hace main() al recuperar
okB1 = lote_recuperado is not None
# Continuar produccion tras recuperar
est["completados"]=set()
lote_recuperado = correr_b = lote_recuperado
for c in range(30):
    ep=next((t for t in lote_recuperado["trabajos"] if t["estado"]=="en_proceso"),None)
    if ep and ep.get("tarea_id"): est["completados"].add(ep["tarea_id"])
    lote_recuperado=orq.procesar_lote(lote_recuperado)
    if lote_recuperado.get("estado_lote")=="completado": break
    T[0]+=60
okB = lote_recuperado.get("estado_lote")=="completado"
print(f"  ✅ Recuperó el lote y lo completó tras el corte: {okB}")
res.append(("Recuperación tras corte de luz", okB and okB1))

# TEST C: NODO CAÍDO → espera, no falla
print("\n"+"="*64); print("TEST C: nodo caído → espera sin romper")
est={"plan":PLAN,"control":{"accion":""},"completados":set(),"encolados":[],"nodos_vivos":False}
orq,T=cargar_orq(est,"/home/claude/test_env/ex_c/l.json")
lote=orq.crear_lote(PLAN)
lote=orq.procesar_lote(lote)  # con nodos caidos
okC1 = lote.get("estado_lote")=="esperando_nodo"
print(f"  Estado con nodo caído: {lote.get('estado_lote')}")
# Revivir nodos y continuar
est["nodos_vivos"]=True
lote=correr_c = lote
for c in range(20):
    ep=next((t for t in lote["trabajos"] if t["estado"]=="en_proceso"),None)
    if ep and ep.get("tarea_id"): est["completados"].add(ep["tarea_id"])
    lote=orq.procesar_lote(lote)
    if lote.get("estado_lote")=="completado": break
    T[0]+=60
okC = lote.get("estado_lote")=="completado"
print(f"  ✅ Esperó nodo caído y luego completó: {okC and okC1}")
res.append(("Nodo caído espera y recupera", okC and okC1))

# TEST D: TODOS los videos fallan al encolar → lote termina, no se cuelga
print("\n"+"="*64); print("TEST D: todos fallan al encolar → termina sin colgarse")
est={"plan":PLAN,"control":{"accion":""},"completados":set(),"encolados":[],
     "fallar":["La Viuda_9:16","La Viuda_16:9","Monkygraff_9:16","Monkygraff_16:9"]}
orq,T=cargar_orq(est,"/home/claude/test_env/ex_d/l.json")
lote=orq.crear_lote(PLAN)
for c in range(60):
    lote=orq.procesar_lote(lote)
    if lote.get("estado_lote") in ("completado","cancelado"): break
    T[0]+=60
fallidos=sum(1 for t in lote["trabajos"] if t["estado"]=="fallido")
okD = lote.get("estado_lote")=="completado" and fallidos==len(lote["trabajos"])
print(f"  Estado: {lote.get('estado_lote')} | Fallidos: {fallidos}/{len(lote['trabajos'])}")
print(f"  ✅ Terminó sin colgarse aunque todo falló: {okD}")
res.append(("Todos fallan → termina sin colgarse", okD))

# TEST E: enfriamiento entre videos se respeta
print("\n"+"="*64); print("TEST E: enfriamiento entre videos")
plan_e=dict(PLAN); plan_e["enfriamiento_seg"]=120
est={"plan":plan_e,"control":{"accion":""},"completados":set(),"encolados":[]}
orq,T=cargar_orq(est,"/home/claude/test_env/ex_e/l.json")
lote=orq.crear_lote(plan_e)
# completar primer video
for c in range(3):
    ep=next((t for t in lote["trabajos"] if t["estado"]=="en_proceso"),None)
    if ep and ep.get("tarea_id"): est["completados"].add(ep["tarea_id"])
    lote=orq.procesar_lote(lote)
    if any(t["estado"]=="completado" for t in lote["trabajos"]): break
    T[0]+=60
# Justo despues de completar, debe estar enfriando (sin avanzar tiempo)
lote=orq.procesar_lote(lote)
okE = "Enfriamiento" in lote.get("mensaje","") or lote.get("enfriando_hasta",0) > T[0]
print(f"  Mensaje: {lote.get('mensaje','')[:50]}")
print(f"  ✅ Respeta enfriamiento entre videos: {okE}")
res.append(("Enfriamiento se respeta", okE))

print("\n"+"="*64); print("RESUMEN PRUEBAS EXTREMAS"); print("="*64)
for n,ok in res: print(f"  {'✅' if ok else '❌'} {n}")
print(f"\n{'✅ TODAS LAS PRUEBAS EXTREMAS PASAN' if all(ok for _,ok in res) else '❌ HAY FALLOS'}")
