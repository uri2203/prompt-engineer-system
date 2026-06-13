"""
TEST: el worker debe tomar la SIGUIENTE orden en cola al terminar la anterior,
SIN reiniciar. Reproduce el bug reportado.
"""
import os, sys, time, json, subprocess

for p in [7861, 8500, 8000, 9999]:
    subprocess.run(f"fuser -k {p}/tcp 2>/dev/null", shell=True)
time.sleep(2)

BASE = "/home/claude/test_env"
sys.path.insert(0, BASE)
SANDBOX = os.path.join(BASE, "sandbox")
NODO = os.path.join(BASE, "nodo_pinpinela")

import runner_prep
runner_prep.preparar()
import mocks_nodos
_servidores = mocks_nodos.iniciar_todos()
time.sleep(1)
from cargador_worker import cargar_worker_parcheado
worker = cargar_worker_parcheado()

def crear_tarea(tid, n=3):
    escenas = [{"id": i+1, "prompt": f"scene {i+1}", "prompt_visual": f"scene {i+1}",
                "texto_locucion": f"Narración escena {i+1} con texto suficiente."} for i in range(n)]
    return {
        "id": tid, "tipo": "IMAGEN",
        "prompt": json.dumps(escenas, ensure_ascii=False),
        "formato": "9:16", "marca": "La Viuda",
        "texto_locucion": " ".join(e["texto_locucion"] for e in escenas),
        "titulo_sugerido": f"Video {tid}",
        "escenas": escenas, "escenas_texto": [e["texto_locucion"] for e in escenas],
        "origen": "bot_pinpinela",
    }

print("=" * 60)
print("TEST: ÓRDENES SECUENCIALES (sin reiniciar el worker)")
print("=" * 60)

# Escenario real: VIDEO-1 ya completada reenviada + VIDEO-2 nueva detras
mocks_nodos.ESTADO["cola"].append(crear_tarea("VIDEO-1"))
worker._tareas_completadas.add("VIDEO-1")  # simula que Render reenvia una ya hecha
mocks_nodos.ESTADO["cola"].append(crear_tarea("VIDEO-2"))
print(f"\nEscenario: VIDEO-1 ya hecha (reenviada) + VIDEO-2 nueva. Cola: {len(mocks_nodos.ESTADO['cola'])}")

# Simular el bucle del worker (varias pasadas de procesar)
print("\n--- Simulando el bucle while True: procesar() ---")
videos_completados = []
for pasada in range(40):  # máximo 40 pasadas
    worker.procesar()
    # Ver qué videos finales existen
    if os.path.isdir(SANDBOX):
        for carpeta in os.listdir(SANDBOX):
            mp4 = os.path.join(SANDBOX, carpeta, "00_FINAL_EXTREME_DYNAMICS.mp4")
            if os.path.exists(mp4) and carpeta not in videos_completados:
                videos_completados.append(carpeta)
                print(f"  ✅ Video completado: {carpeta} (pasada {pasada+1})")
    if len(videos_completados) >= 2:
        break

print("\n" + "=" * 60)
print("RESULTADO:")
print(f"  Videos completados: {len(videos_completados)} de 2")
print(f"  {videos_completados}")
if len(videos_completados) >= 2:
    print("  ✅ El worker tomó AMBAS órdenes sin reiniciar")
else:
    print("  ❌ BUG CONFIRMADO: el worker NO tomó la segunda orden")
    print(f"  Cola Render restante: {len(mocks_nodos.ESTADO['cola'])}")
    print(f"  _tareas_completadas: {worker._tareas_completadas}")
print("=" * 60)

for s in _servidores:
    try: s.shutdown(); s.server_close()
    except: pass
