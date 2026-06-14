"""
TEST INTEGRAL FINAL DEL ORQUESTADOR — orquestador real + app.py real + worker real.
Usa el test_client de Flask como puente (sin servidor HTTP, mas robusto).
"""
import os, sys, json, time, shutil
sys.path.insert(0, "/home/claude/test_env"); sys.path.insert(0, "/home/claude")

BASE = "/home/claude/test_env"
shutil.rmtree(os.path.join(BASE,"estado_lote_e2e"), ignore_errors=True)
shutil.rmtree(os.path.join(BASE,"sandbox"), ignore_errors=True)

import runner_prep; runner_prep.preparar()
import mocks_nodos; _srv = mocks_nodos.iniciar_todos(); time.sleep(1)

import stubs_modulos; stubs_modulos.instalar_stubs()
import requests as rr
GH = {}
class FR:
    def __init__(s,st,d): s.status_code=st; s._d=d
    def json(s): return s._d
def fget(url,*a,**k):
    import base64
    for n in ["plan_lote","lote_control","lote_progreso","cola_ordenes","agenda"]:
        if f"{n}.json" in url:
            if n in GH: return FR(200,{"content":base64.b64encode(json.dumps(GH[n]).encode()).decode(),"sha":"x"})
            return FR(404,{})
    return FR(200,{"items":[]})
def fput(url,*a,**k):
    import base64; b=k.get("json",{})
    for n in ["plan_lote","lote_control","lote_progreso","cola_ordenes","agenda"]:
        if f"{n}.json" in url: GH[n]=json.loads(base64.b64decode(b.get("content","")).decode())
    return FR(200,{"commit":{"sha":"x"}})
os.environ["GH_DIAG_TOKEN"]="fake"; os.chdir("/home/claude")
import importlib.util
spec=importlib.util.spec_from_file_location("a","/home/claude/app.py")
am=importlib.util.module_from_spec(spec); spec.loader.exec_module(am)
am.requests.get=fget; am.requests.put=fput
try: os.remove(am.CRON_FILE)
except: pass
# Servidor HTTP real en 9999 para el worker (hace polling HTTP)
import socketserver
socketserver.TCPServer.allow_reuse_address = True
from werkzeug.serving import make_server
import threading
_appsrv = make_server("127.0.0.1", 9999, am.app)
threading.Thread(target=_appsrv.serve_forever, daemon=True).start()
time.sleep(1)
client=am.app.test_client()
with client.session_transaction() as s: s["user"]="test"

# Cargar orquestador, pero sus llamadas de red van al test_client (puente)
codigo=open("/home/claude/orquestador_lote.py").read()
codigo=codigo.replace(r'CARPETA_ESTADO = r"C:\NODO_PINPINELA\estado_lote"','CARPETA_ESTADO = "/home/claude/test_env/estado_lote_e2e"')
codigo=codigo.replace('if __name__ == "__main__":\n    main()','')
open("/home/claude/test_env/orq_f.py","w").write(codigo)
spec2=importlib.util.spec_from_file_location("orq_f","/home/claude/test_env/orq_f.py")
orq=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(orq)

# PUENTE: las funciones de red del orquestador usan el test_client
def _plan(): return client.get("/api/bot/plan_semanal").get_json()
def _control(): return client.get("/api/bot/lote_control").get_json()
def _consumir(): client.post("/api/bot/lote_control", json={"accion":""})
def _progreso(lote):
    comp=sum(1 for t in lote["trabajos"] if t["estado"]=="completado")
    client.post("/api/bot/lote_progreso", json={"estado_lote":lote.get("estado_lote"),"total":len(lote["trabajos"]),"completados":comp,"trabajo_actual":lote.get("trabajo_actual_desc",""),"mensaje":lote.get("mensaje","")})
def _encolar(marca,formato,dur=None):
    r=client.post("/api/bot/lanzar_orden_motor", json={"marca":marca,"formato":formato,"duracion_min":dur})
    return r.get_json().get("tarea_id")
def _listo(tid):
    return client.get(f"/api/bot/video_estado?tarea_id={tid}").get_json().get("completado",False)
orq.obtener_plan=_plan; orq.obtener_control=_control; orq.consumir_control=_consumir
orq.reportar_progreso=_progreso; orq.encolar_video=_encolar; orq.video_esta_listo=_listo
orq.nodos_criticos_vivos=lambda:(True,[])  # nodos OK (mocks vivos)

from cargador_worker import cargar_worker_parcheado
worker=cargar_worker_parcheado()

print("="*60)
print("TEST INTEGRAL ORQUESTADOR: orq REAL + app.py REAL + worker REAL")
print("="*60)
plan={"marcas":[{"marca":"La Viuda","shorts":1,"largos":0,"duracion_min":28},{"marca":"Monkygraff","shorts":1,"largos":0,"duracion_min":28}],"enfriamiento_seg":0,"orden":"shorts_primero"}
client.post("/api/bot/plan_semanal", json=plan)
print("Plan: La Viuda 1 short + Monkygraff 1 short")

lote=orq.crear_lote(orq.obtener_plan())
print(f"Lote creado: {len(lote['trabajos']) if lote else 0} videos | resumen: {lote['resumen'] if lote else 'N/A'}")
orq.guardar_lote(lote)

for ciclo in range(80):
    if lote and lote.get("estado_lote") not in ("completado","cancelado"):
        lote=orq.procesar_lote(lote)
    worker.procesar()
    if lote and lote.get("estado_lote")=="completado":
        print(f"LOTE COMPLETADO en ciclo {ciclo+1}")
        break
    time.sleep(0.2)

print("="*60)
videos=[]
sb=os.path.join(BASE,"sandbox")
if os.path.isdir(sb):
    for car in os.listdir(sb):
        mp4=os.path.join(sb,car,"00_FINAL_EXTREME_DYNAMICS.mp4")
        if os.path.exists(mp4): videos.append((car,os.path.getsize(mp4)))
print(f"Videos producidos por el orquestador: {len(videos)} de 2")
for v,t in videos: print(f"  OK {v} ({t} bytes)")
print(f"Estado final del lote: {lote.get('estado_lote') if lote else 'N/A'}")
if len(videos)>=2 and lote and lote.get("estado_lote")=="completado":
    print("\nRESULTADO: EL ORQUESTADOR PRODUJO EL LOTE COMPLETO DE PUNTA A PUNTA")
else:
    print(f"\nRESULTADO PARCIAL: videos={len(videos)}, estado={lote.get('estado_lote') if lote else 'N/A'}")
_appsrv.shutdown()
for s in _srv:
    try: s.shutdown(); s.server_close()
    except: pass
print("="*60)
