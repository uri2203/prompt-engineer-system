"""Test: Gemini sin cuota → lote espera con mensaje claro, no quema reintentos en todos."""
import sys, os
sys.path.insert(0, "/home/claude")
import importlib.util
spec = importlib.util.spec_from_file_location("orq_q", "/home/claude/orquestador_lote.py")
orq = importlib.util.module_from_spec(spec); spec.loader.exec_module(orq)
TIEMPO=[1000.0]
EST={"control":{"accion":""},"completados":set(),"cuota_agotada":True,"intentos_encolado":0}
class FR:
    def __init__(s,st,d): s.status_code=st; s._d=d
    def json(s): return s._d
    @property
    def text(s): return str(s._d)
def fget(url,*a,**k):
    if "lote_control" in url: return FR(200,EST["control"])
    if "video_estado" in url:
        tid=k.get("params",{}).get("tarea_id","")
        return FR(200,{"completado":tid in EST["completados"],"tarea_id":tid})
    return FR(200,{})
def fpost(url,*a,**k):
    if "lanzar_orden_motor" in url:
        EST["intentos_encolado"]+=1
        if EST["cuota_agotada"]:
            return FR(500,{"status":"error","message":"ERROR CRÍTICO API GEMINI:"})
        EST["completados"]  # noop
        return FR(200,{"status":"PENDING_REVIEW","tarea_id":f"t{EST['intentos_encolado']}"})
    if "lote_control" in url: EST["control"]={"accion":""}; return FR(200,{})
    if "lote_progreso" in url: EST["progreso"]=k.get("json",{}); return FR(200,{})
    return FR(200,{})
orq.requests.get=fget; orq.requests.post=fpost; orq.RENDER_URL="http://fake"
orq.CARPETA_ESTADO="/home/claude/test_env/eq"; orq.ARCHIVO_LOTE="/home/claude/test_env/eq/l.json"
os.makedirs(orq.CARPETA_ESTADO,exist_ok=True)
if os.path.exists(orq.ARCHIVO_LOTE): os.remove(orq.ARCHIVO_LOTE)
orq.time.time=lambda:TIEMPO[0]; orq.ESPERA_NODO_CAIDO=0

PLAN={"marcas":[{"marca":"La Viuda","shorts":1,"largos":1,"duracion_min":15},
                {"marca":"Monkygraff","shorts":1,"largos":1,"duracion_min":28}],
      "enfriamiento_seg":0,"orden":"shorts_primero"}

print("="*64); print("TEST: Gemini sin cuota"); print("="*64)
lote=orq.crear_lote(PLAN)
# Correr con cuota agotada
for c in range(5):
    lote=orq.procesar_lote(lote); TIEMPO[0]+=60
print(f"Intentos de encolado con cuota agotada: {EST['intentos_encolado']}")
print(f"Estado del lote: {lote.get('estado_lote')}")
print(f"Mensaje: {lote.get('mensaje','')[:70]}")
ok1 = lote.get("estado_lote")=="esperando_cuota"
ok2 = EST["intentos_encolado"] <= 2   # NO quemó muchos intentos
print(f"  ✅ Lote en espera por cuota: {ok1}")
print(f"  ✅ No quemó la cuota con reintentos masivos: {ok2}")

# Ahora la cuota se restablece y el tiempo avanza > ESPERA_CUOTA
print("\n--- Cuota restablecida + pasa el tiempo de espera ---")
EST["cuota_agotada"]=False
TIEMPO[0]+=2000  # supera ESPERA_CUOTA (1800)
for c in range(20):
    ep=next((t for t in lote["trabajos"] if t["estado"]=="en_proceso"),None)
    if ep and ep.get("tarea_id"): EST["completados"].add(ep["tarea_id"])
    lote=orq.procesar_lote(lote)
    if lote.get("estado_lote")=="completado": break
    TIEMPO[0]+=60
ok3 = lote.get("estado_lote")=="completado"
completados=sum(1 for t in lote["trabajos"] if t["estado"]=="completado")
print(f"Estado final: {lote.get('estado_lote')} | Completados: {completados}/{len(lote['trabajos'])}")
print(f"  ✅ Reanudó solo y completó al volver la cuota: {ok3}")
print("\n"+("✅ MANEJO DE CUOTA CORRECTO" if (ok1 and ok2 and ok3) else "❌ REVISAR"))
