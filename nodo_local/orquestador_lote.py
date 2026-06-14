"""
ORQUESTADOR DE LOTE — Motor de Produccion Industrial (Sistema Pinpinela)
Vive en el XEON. Orquesta la produccion masiva por lotes.

QUE HACE:
  - Lee el PLAN del lote (por marca: # shorts, # largos, duracion de largos)
  - Cuando el operador pulsa INICIAR (panel), crea el lote
  - Produce uno por uno: pide al worker generar cada video, ESPERA
    INDEFINIDAMENTE a que termine, espera el ENFRIAMIENTO, pide el siguiente
  - PERSISTENCIA TOTAL: guarda el estado en disco tras cada paso
  - Nodo caido -> espera LAS HORAS QUE SEAN a que vuelva
  - Corte de luz -> al reiniciar RETOMA donde quedo (no repite lo hecho)
  - CONTROLES: iniciar / pausar / reanudar / cancelar
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import os, json, time, requests
from datetime import datetime, timezone, timedelta

RENDER_URL = "https://prompt-engineer-system-l2r6.onrender.com"
TZ_MEXICO = timezone(timedelta(hours=-6))
CARPETA_ESTADO = r"C:\NODO_PINPINELA\estado_lote"
os.makedirs(CARPETA_ESTADO, exist_ok=True)
ARCHIVO_LOTE = os.path.join(CARPETA_ESTADO, "lote_actual.json")
INTERVALO_CICLO = 20
ENFRIAMIENTO_DEFAULT = 180
ESPERA_NODO_CAIDO = 60
IP_GRAFICA = "192.168.0.215"
IP_VOZ = "192.168.0.251"
NODOS = {"sd": f"http://{IP_GRAFICA}:7861/sdapi/v1/options", "voz": f"http://{IP_VOZ}:8000"}

def leer_lote():
    try:
        with open(ARCHIVO_LOTE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def guardar_lote(lote):
    try:
        tmp = ARCHIVO_LOTE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(lote, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ARCHIVO_LOTE)
    except Exception as e:
        print(f"Error guardando lote: {e}")

def obtener_plan():
    try:
        r = requests.get(f"{RENDER_URL}/api/bot/plan_semanal", timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"No se pudo leer el plan: {e}")
    return {"marcas": [], "enfriamiento_seg": ENFRIAMIENTO_DEFAULT, "orden": "shorts_primero"}

def obtener_control():
    try:
        r = requests.get(f"{RENDER_URL}/api/bot/lote_control", timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"accion": ""}

def consumir_control():
    try:
        requests.post(f"{RENDER_URL}/api/bot/lote_control", json={"accion": ""}, timeout=20)
    except Exception:
        pass

def reportar_progreso(lote):
    try:
        completados = sum(1 for t in lote["trabajos"] if t["estado"] == "completado")
        requests.post(f"{RENDER_URL}/api/bot/lote_progreso", json={
            "estado_lote": lote.get("estado_lote"),
            "total": len(lote["trabajos"]),
            "completados": completados,
            "trabajo_actual": lote.get("trabajo_actual_desc", ""),
            "mensaje": lote.get("mensaje", ""),
            "resumen": lote.get("resumen", ""),
        }, timeout=20)
    except Exception:
        pass

def encolar_video(marca, formato, duracion_min=None):
    try:
        r = requests.post(f"{RENDER_URL}/api/bot/lanzar_orden_motor",
                          json={"marca": marca, "formato": formato, "duracion_min": duracion_min}, timeout=120)
        if r.status_code == 200:
            return r.json().get("tarea_id")
    except Exception as e:
        print(f"Error encolando video: {e}")
    return None

def video_esta_listo(tarea_id):
    try:
        r = requests.get(f"{RENDER_URL}/api/bot/video_estado", params={"tarea_id": tarea_id}, timeout=20)
        if r.status_code == 200:
            return r.json().get("completado", False)
    except Exception:
        pass
    return False

def ping_nodo(url, timeout=6):
    try:
        requests.get(url, timeout=timeout)
        return True
    except Exception:
        return False

def nodos_criticos_vivos():
    caidos = []
    if not ping_nodo(NODOS["sd"]): caidos.append("SD (imagenes)")
    if not ping_nodo(NODOS["voz"]): caidos.append("Voz")
    return (len(caidos) == 0, caidos)

def crear_lote(plan):
    marcas = plan.get("marcas", [])
    if not marcas:
        return None
    orden = plan.get("orden", "shorts_primero")
    trabajos = []
    contador = [0]
    resumen_partes = []
    def agregar(marca, formato, duracion, n):
        for _ in range(n):
            contador[0] += 1
            trabajos.append({"n": contador[0], "marca": marca, "formato": formato,
                             "duracion_min": duracion if formato == "16:9" else None,
                             "estado": "pendiente", "tarea_id": None})
    for entrada in marcas:
        m = entrada.get("marca")
        ns = int(entrada.get("shorts", 0)); nl = int(entrada.get("largos", 0))
        resumen_partes.append(f"{m}: {ns}s+{nl}L")
    if orden == "largos_primero":
        for e in marcas: agregar(e.get("marca"), "16:9", int(e.get("duracion_min", 28)), int(e.get("largos", 0)))
        for e in marcas: agregar(e.get("marca"), "9:16", None, int(e.get("shorts", 0)))
    else:
        for e in marcas: agregar(e.get("marca"), "9:16", None, int(e.get("shorts", 0)))
        for e in marcas: agregar(e.get("marca"), "16:9", int(e.get("duracion_min", 28)), int(e.get("largos", 0)))
    if not trabajos:
        return None
    return {
        "creado": datetime.now(TZ_MEXICO).strftime("%Y-%m-%d %H:%M"),
        "resumen": " | ".join(resumen_partes),
        "enfriamiento": int(plan.get("enfriamiento_seg", ENFRIAMIENTO_DEFAULT)),
        "trabajos": trabajos, "estado_lote": "produciendo",
        "trabajo_actual_desc": "", "mensaje": "Lote creado, iniciando produccion.",
    }

def procesar_lote(lote):
    accion = obtener_control().get("accion", "")
    if accion == "cancelar":
        print("[CONTROL] Lote cancelado")
        lote["estado_lote"] = "cancelado"; lote["mensaje"] = "Lote cancelado por el operador."
        consumir_control(); guardar_lote(lote); reportar_progreso(lote); return lote
    elif accion == "pausar":
        print("[CONTROL] Lote pausado")
        lote["estado_lote"] = "pausado"; lote["mensaje"] = "Pausado por el operador."
        consumir_control(); guardar_lote(lote); reportar_progreso(lote); return lote
    elif accion == "reanudar":
        print("[CONTROL] Lote reanudado")
        lote["estado_lote"] = "produciendo"; lote["mensaje"] = "Reanudado por el operador."
        consumir_control()
    if lote["estado_lote"] in ("pausado", "cancelado"):
        reportar_progreso(lote); return lote
    # Video en proceso: esperar INDEFINIDAMENTE
    en_proceso = next((t for t in lote["trabajos"] if t["estado"] == "en_proceso"), None)
    if en_proceso:
        if en_proceso.get("tarea_id") and video_esta_listo(en_proceso["tarea_id"]):
            en_proceso["estado"] = "completado"
            lote["mensaje"] = f"Video {en_proceso['n']} completado"
            lote["enfriando_hasta"] = time.time() + lote.get("enfriamiento", ENFRIAMIENTO_DEFAULT)
            print(f"OK Video {en_proceso['n']} ({en_proceso['marca']}) completado")
            guardar_lote(lote)
        else:
            dur = f" {en_proceso['duracion_min']}min" if en_proceso.get("duracion_min") else ""
            lote["trabajo_actual_desc"] = f"Generando video {en_proceso['n']}/{len(lote['trabajos'])} ({en_proceso['marca']} {en_proceso['formato']}{dur})"
        reportar_progreso(lote); return lote
    # Enfriamiento
    if time.time() < lote.get("enfriando_hasta", 0):
        restante = int(lote["enfriando_hasta"] - time.time())
        lote["trabajo_actual_desc"] = f"Enfriando nodos... {restante}s"
        lote["mensaje"] = f"Enfriamiento entre videos: {restante}s"
        reportar_progreso(lote); return lote
    # Siguiente pendiente
    siguiente = next((t for t in lote["trabajos"] if t["estado"] == "pendiente"), None)
    if not siguiente:
        if all(t["estado"] == "completado" for t in lote["trabajos"]):
            lote["estado_lote"] = "completado"; lote["mensaje"] = "Lote completado."
            print("LOTE COMPLETADO"); guardar_lote(lote); reportar_progreso(lote)
        return lote
    # Nodos vivos? Esperar las horas que sean
    ok, caidos = nodos_criticos_vivos()
    if not ok:
        lote["estado_lote"] = "esperando_nodo"
        lote["mensaje"] = f"Nodo(s) caido(s): {', '.join(caidos)}. Esperando que vuelvan..."
        lote["trabajo_actual_desc"] = f"Esperando nodo: {', '.join(caidos)}"
        print(f"Nodo caido: {caidos} - esperando (sin limite)")
        guardar_lote(lote); reportar_progreso(lote); time.sleep(ESPERA_NODO_CAIDO); return lote
    # Lanzar siguiente
    lote["estado_lote"] = "produciendo"
    print(f"Lanzando video {siguiente['n']}/{len(lote['trabajos'])}: {siguiente['marca']} {siguiente['formato']}")
    tarea_id = encolar_video(siguiente["marca"], siguiente["formato"], siguiente.get("duracion_min"))
    if tarea_id:
        siguiente["estado"] = "en_proceso"; siguiente["tarea_id"] = tarea_id; siguiente["inicio_ts"] = time.time()
        lote["trabajo_actual_desc"] = f"Generando video {siguiente['n']} ({siguiente['marca']})"
        lote["mensaje"] = f"Produccion del video {siguiente['n']} iniciada."
    else:
        lote["mensaje"] = f"No se pudo encolar el video {siguiente['n']}, reintentando..."
    guardar_lote(lote); reportar_progreso(lote); return lote

def main():
    print("=" * 60)
    print("ORQUESTADOR DE LOTE - Motor de Produccion Industrial")
    print("Vive en el Xeon - Espera indefinida - Retoma tras cortes de luz")
    print("=" * 60)
    lote = leer_lote()
    if lote and lote.get("estado_lote") not in ("completado", "cancelado"):
        completados = sum(1 for t in lote["trabajos"] if t["estado"] == "completado")
        print(f"RECUPERACION: lote encontrado - {completados}/{len(lote['trabajos'])} hechos")
        for t in lote["trabajos"]:
            if t["estado"] == "en_proceso":
                t["estado"] = "pendiente"
                print(f"   Video {t['n']} estaba a medias - se reintentara")
        guardar_lote(lote)
    else:
        lote = None
    while True:
        try:
            accion = obtener_control().get("accion", "")
            if accion == "iniciar":
                consumir_control()
                nuevo = crear_lote(obtener_plan())
                if nuevo:
                    lote = nuevo; guardar_lote(lote)
                    print(f"LOTE CREADO: {lote['resumen']}"); reportar_progreso(lote)
                else:
                    print("Plan vacio - nada que producir")
            if lote and lote.get("estado_lote") not in ("completado", "cancelado"):
                lote = procesar_lote(lote)
        except Exception as e:
            print(f"Error en ciclo del orquestador: {e}")
        time.sleep(INTERVALO_CICLO)

if __name__ == "__main__":
    main()
