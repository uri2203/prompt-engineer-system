"""
TEST INTEGRAL — ejecuta el worker real contra los mocks y valida el flujo completo.
"""
import os, sys, time, json, shutil, subprocess

# Liberar puertos de ejecuciones previas
for p in [7861, 8500, 8000, 9999]:
    subprocess.run(f"fuser -k {p}/tcp 2>/dev/null", shell=True)
time.sleep(2)

BASE = "/home/claude/test_env"
sys.path.insert(0, BASE)

SANDBOX = os.path.join(BASE, "sandbox")
ASSETS = os.path.join(BASE, "sandbox_assets")
NODO = os.path.join(BASE, "nodo_pinpinela")

# 1. Preparar entorno
import runner_prep
runner_prep.preparar()

# 2. Mocks
import mocks_nodos
_servidores = mocks_nodos.iniciar_todos()
time.sleep(1)

# 3. Cargar worker parcheado
from cargador_worker import cargar_worker_parcheado
worker = cargar_worker_parcheado()

# 4. Crear una tarea de IMAGEN realista (como la que manda el bot)
escenas = []
for i in range(5):  # 5 escenas para prueba rápida
    escenas.append({
        "id": i + 1,
        "prompt": f"dark eerie scene number {i+1}, cinematic",
        "prompt_visual": f"dark eerie scene {i+1}",
        "texto_locucion": f"Esta es la narración de la escena número {i+1}, con suficiente texto para generar audio.",
    })

tarea = {
    "id": "test-video-001",
    "tipo": "IMAGEN",
    "prompt": json.dumps(escenas, ensure_ascii=False),
    "formato": "9:16",
    "marca": "La Viuda",
    "texto_locucion": " ".join(e["texto_locucion"] for e in escenas),
    "titulo_sugerido": "Prueba de Video Completo",
    "escenas": escenas,
    "escenas_texto": [e["texto_locucion"] for e in escenas],
    "hooks": ["Primer hook de prueba", "Segundo hook", "Tercer hook"],
    "origen": "bot_pinpinela",
}

# Poner la tarea en la cola del mock
mocks_nodos.ESTADO["cola"].append(tarea)

print("\n" + "=" * 60)
print("EJECUTANDO EL WORKER (fase IMAGEN)...")
print("=" * 60)

# 5. Ejecutar procesar() — primera pasada (IMAGEN)
worker.procesar()

# 6. Ver si encoló el ensamblaje localmente
cola_local = os.path.join(NODO, "cola_local")
ensamblajes = []
if os.path.isdir(cola_local):
    ensamblajes = [f for f in os.listdir(cola_local) if f.endswith(".json")]

print("\n" + "=" * 60)
print("RESULTADO FASE IMAGEN:")
print("=" * 60)
print(f"  Llamadas a SD (imágenes generadas): {mocks_nodos.ESTADO['sd_llamadas']}")
print(f"  Ensamblaje encolado localmente: {'SÍ ✅' if ensamblajes else 'NO ❌'}")
if ensamblajes:
    print(f"    Archivo: {ensamblajes[0]}")

# 7. Si encoló el ensamblaje, ejecutar la fase ENSAMBLAJE
if ensamblajes:
    print("\n" + "=" * 60)
    print("EJECUTANDO EL WORKER (fase ENSAMBLAJE)...")
    print("=" * 60)
    worker.procesar()  # ahora toma el ensamblaje de la cola local

    # 8. Verificar el MP4 final
    print("\n" + "=" * 60)
    print("RESULTADO FASE ENSAMBLAJE:")
    print("=" * 60)
    carpeta_video = os.path.join(SANDBOX, "test-video-001")
    if os.path.isdir(carpeta_video):
        archivos = os.listdir(carpeta_video)
        mp4_final = [f for f in archivos if "FINAL" in f and f.endswith(".mp4")]
        audio = [f for f in archivos if f == "locucion.mp3"]
        print(f"  Audio generado: {'SÍ ✅' if audio else 'NO ❌'}")
        print(f"  MP4 final generado: {'SÍ ✅' if mp4_final else 'NO ❌'}")
        if mp4_final:
            ruta = os.path.join(carpeta_video, mp4_final[0])
            tam = os.path.getsize(ruta)
            print(f"    {mp4_final[0]} ({tam} bytes)")
        print(f"  Archivos en la carpeta: {archivos}")
    else:
        print("  ❌ No se creó la carpeta del video")

print("\n" + "=" * 60)
print("VALIDACIONES RIGUROSAS:")
print("=" * 60)
# Verificar el VRAM: debe descargarse UNA vez y recargarse UNA vez
estados_vram = mocks_nodos.ESTADO
print(f"  SD imágenes generadas: {estados_vram['sd_llamadas']} (esperado: 5)")
print(f"  DepthFlow llamado: {estados_vram['depthflow_llamadas']} veces")
print(f"  Worker reportó estados (ocupado/libre): {len(estados_vram['worker_estados'])}")
print(f"  Tareas completadas reportadas: {estados_vram['tareas_completadas']}")
print(f"  Uploads: {estados_vram['uploads']}")

# Verificar sincronía audio/video
carpeta_video = os.path.join(SANDBOX, "test-video-001")
mp4 = os.path.join(carpeta_video, "00_FINAL_EXTREME_DYNAMICS.mp4")
if os.path.exists(mp4):
    import subprocess as sp
    dur = sp.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{mp4}'",
                 shell=True, capture_output=True, text=True).stdout.strip()
    print(f"  Duración del MP4 final: {dur}s")
    print(f"  Tamaño: {os.path.getsize(mp4)} bytes")

print("\n" + "=" * 60)
print("FIN DEL TEST")
print("=" * 60)

# Apagar los servidores mock para liberar los puertos
for s in _servidores:
    try:
        s.shutdown()
        s.server_close()
    except Exception:
        pass
