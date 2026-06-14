"""
TEST DEL MOTOR DEL ORQUESTADOR (lógica de crear_lote y procesar_lote)
Valida: creación del lote por marca, orden shorts/largos, espera de nodo,
persistencia, y el flujo de estados. No necesita Render real (mockea las llamadas).
"""
import os, sys, json, time

sys.path.insert(0, "/home/claude")

# Cargar el orquestador parcheando sus llamadas a Render y rutas
import importlib.util

# Parchear la ruta de estado a un temp local y las funciones de red
codigo = open("/home/claude/orquestador_lote.py").read()
codigo = codigo.replace(r'CARPETA_ESTADO = r"C:\NODO_PINPINELA\estado_lote"',
                        'CARPETA_ESTADO = "/home/claude/test_env/estado_lote_test"')
# Quitar el main() bucle infinito al cargar
codigo = codigo.replace('if __name__ == "__main__":\n    main()', '')
ruta = "/home/claude/test_env/orq_test.py"
open(ruta, "w").write(codigo)

spec = importlib.util.spec_from_file_location("orq_test", ruta)
orq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orq)

print("=" * 60)
print("TEST DEL MOTOR DEL ORQUESTADOR")
print("=" * 60)

# Estado simulado de Render
ESTADO = {"control": {"accion": ""}, "videos_listos": set(), "encolados": [], "nodos_ok": True}

def mock_obtener_control(): return ESTADO["control"]
def mock_consumir_control(): ESTADO["control"] = {"accion": ""}
def mock_reportar_progreso(lote): pass
def mock_encolar_video(marca, formato, dur=None):
    tid = f"vid-{len(ESTADO['encolados'])+1}"
    ESTADO["encolados"].append({"tid": tid, "marca": marca, "formato": formato, "dur": dur})
    return tid
def mock_video_listo(tid): return tid in ESTADO["videos_listos"]
def mock_nodos_vivos(): return (ESTADO["nodos_ok"], [] if ESTADO["nodos_ok"] else ["SD (imagenes)"])

orq.obtener_control = mock_obtener_control
orq.consumir_control = mock_consumir_control
orq.reportar_progreso = mock_reportar_progreso
orq.encolar_video = mock_encolar_video
orq.video_esta_listo = mock_video_listo
orq.nodos_criticos_vivos = mock_nodos_vivos

# TEST 1: crear_lote con el modelo simple
print("\n[1] Crear lote (La Viuda 2s+1L, Monkygraff 1s+2L, shorts primero)...")
plan = {
    "marcas": [
        {"marca": "La Viuda", "shorts": 2, "largos": 1, "duracion_min": 28},
        {"marca": "Monkygraff", "shorts": 1, "largos": 2, "duracion_min": 45},
    ],
    "enfriamiento_seg": 1, "orden": "shorts_primero",
}
lote = orq.crear_lote(plan)
total = len(lote["trabajos"])
shorts = sum(1 for t in lote["trabajos"] if t["formato"] == "9:16")
largos = sum(1 for t in lote["trabajos"] if t["formato"] == "16:9")
print(f"    Total trabajos: {total} (esperado 6) | shorts: {shorts} (3) | largos: {largos} (3)")
# Verificar orden: shorts primero
primeros_3 = [t["formato"] for t in lote["trabajos"][:3]]
print(f"    Orden primeros 3: {primeros_3} {'✅ shorts primero' if all(f=='9:16' for f in primeros_3) else '❌'}")
# Verificar duración de largos
largos_dur = [(t["marca"], t["duracion_min"]) for t in lote["trabajos"] if t["formato"] == "16:9"]
print(f"    Duración largos: {largos_dur}")
print(f"    {'✅ Lote correcto' if total==6 and shorts==3 and largos==3 else '❌ Falla'}")

# TEST 2: procesar el lote completo (simular que cada video termina)
print("\n[2] Procesar lote completo (cada video se completa)...")
orq.ENFRIAMIENTO_DEFAULT = 0
lote["enfriamiento"] = 0
ciclos = 0
while lote["estado_lote"] not in ("completado", "cancelado") and ciclos < 100:
    lote = orq.procesar_lote(lote)
    # Cuando hay un video en proceso, marcarlo como listo (simular que terminó)
    for t in lote["trabajos"]:
        if t["estado"] == "en_proceso" and t["tarea_id"]:
            ESTADO["videos_listos"].add(t["tarea_id"])
    lote["enfriando_hasta"] = 0  # saltar enfriamiento en el test
    ciclos += 1
completados = sum(1 for t in lote["trabajos"] if t["estado"] == "completado")
print(f"    Estado final: {lote['estado_lote']} | completados: {completados}/{total}")
print(f"    {'✅ Lote completado entero' if lote['estado_lote']=='completado' and completados==6 else '❌ Falla'}")

# TEST 3: espera de nodo caído
print("\n[3] Nodo caído → el lote espera (no abandona)...")
ESTADO["nodos_ok"] = False
ESTADO["videos_listos"] = set()
lote2 = orq.crear_lote(plan)
lote2["enfriamiento"] = 0
orq.ESPERA_NODO_CAIDO = 0  # no dormir en el test
lote2 = orq.procesar_lote(lote2)
print(f"    Estado con nodo caído: {lote2['estado_lote']}")
print(f"    {'✅ Espera el nodo (no abandona)' if lote2['estado_lote']=='esperando_nodo' else '❌'}")
# Cuando el nodo vuelve, debe seguir
ESTADO["nodos_ok"] = True
lote2 = orq.procesar_lote(lote2)
en_proceso = any(t["estado"] == "en_proceso" for t in lote2["trabajos"])
print(f"    Tras volver el nodo: {'✅ retoma producción' if en_proceso else '❌ no retoma'}")

# TEST 4: cancelar
print("\n[4] Cancelar el lote...")
ESTADO["control"] = {"accion": "cancelar"}
lote2 = orq.procesar_lote(lote2)
print(f"    Estado: {lote2['estado_lote']} {'✅ cancelado' if lote2['estado_lote']=='cancelado' else '❌'}")

# TEST 5: persistencia (retomar tras corte de luz)
print("\n[5] Persistencia: el lote se guardó en disco...")
guardado = orq.leer_lote()
print(f"    {'✅ Lote en disco (sobrevive corte de luz)' if guardado else '❌ No se guardó'}")

print("\n" + "=" * 60)
print("FIN DEL TEST DEL MOTOR")
print("=" * 60)
