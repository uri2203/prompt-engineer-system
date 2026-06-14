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
MAX_INTENTOS_ENCOLADO = 3      # reintentos de encolado antes de marcar fallido
ESPERA_REINTENTO = 45         # segundos entre reintentos de encolado
ESPERA_CUOTA = 900            # 15 min: alineado con el enfriamiento de llaves en ai_engine
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
        fallidos = sum(1 for t in lote["trabajos"] if t["estado"] == "fallido")
        requests.post(f"{RENDER_URL}/api/bot/lote_progreso", json={
            "estado_lote": lote.get("estado_lote"),
            "total": len(lote["trabajos"]),
            "completados": completados,
            "fallidos": fallidos,
            "trabajo_actual": lote.get("trabajo_actual_desc", ""),
            "mensaje": lote.get("mensaje", ""),
            "resumen": lote.get("resumen", ""),
            "historial": lote.get("historial", []),  # videos terminados (para la consola)
        }, timeout=20)
    except Exception:
        pass

def encolar_video(marca, formato, duracion_min=None):
    """Devuelve (tarea_id, motivo_error). tarea_id=None si falló.
    motivo_error indica si es un fallo de cuota de Gemini (para no martillar)."""
    try:
        r = requests.post(f"{RENDER_URL}/api/bot/lanzar_orden_motor",
                          json={"marca": marca, "formato": formato, "duracion_min": duracion_min}, timeout=120)
        if r.status_code == 200:
            return r.json().get("tarea_id"), None
        # Error: extraer el motivo para decidir si es cuota agotada
        try:
            msg = r.json().get("message", "")
        except Exception:
            msg = r.text[:200] if hasattr(r, "text") else ""
        motivo = "cuota" if ("GEMINI" in msg.upper() or "cuota" in msg.lower() or "quota" in msg.lower() or "limit" in msg.lower()) else "otro"
        return None, motivo
    except Exception as e:
        print(f"Error encolando video: {e}")
        return None, "red"

def video_esta_listo(tarea_id):
    """Devuelve (completado, detalles). detalles = {duracion_real_seg, marca, formato}."""
    try:
        r = requests.get(f"{RENDER_URL}/api/bot/video_estado", params={"tarea_id": tarea_id}, timeout=20)
        if r.status_code == 200:
            j = r.json()
            return j.get("completado", False), j.get("detalles", {})
    except Exception:
        pass
    return False, {}

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
        listo, detalles = (video_esta_listo(en_proceso["tarea_id"]) if en_proceso.get("tarea_id") else (False, {}))
        if listo:
            en_proceso["estado"] = "completado"
            lote["mensaje"] = f"Video {en_proceso['n']} completado"
            lote["enfriando_hasta"] = time.time() + lote.get("enfriamiento", ENFRIAMIENTO_DEFAULT)
            lote["reintentar_hasta"] = 0
            # Registrar en el historial del lote (para la consola del panel)
            dur_real = detalles.get("duracion_real_seg", 0)
            es_largo = en_proceso.get("formato") == "16:9"
            lote.setdefault("historial", []).append({
                "n": en_proceso["n"],
                "marca": en_proceso.get("marca", ""),
                "formato": en_proceso.get("formato", ""),
                "tipo": "Largo" if es_largo else "Short",
                "duracion_sel": en_proceso.get("duracion_min") if es_largo else None,
                "duracion_real_seg": dur_real,
                "hora": datetime.now(TZ_MEXICO).strftime("%H:%M"),
            })
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
    # Espera entre reintentos de encolado (no martillar a Render)
    if time.time() < lote.get("reintentar_hasta", 0):
        restante = int(lote["reintentar_hasta"] - time.time())
        lote["trabajo_actual_desc"] = f"Reintentando encolado en {restante}s"
        reportar_progreso(lote); return lote
    # Siguiente pendiente (los 'fallido' se saltan automáticamente)
    siguiente = next((t for t in lote["trabajos"] if t["estado"] == "pendiente"), None)
    if not siguiente:
        # El lote termina cuando ya no quedan pendientes ni en proceso
        terminados = all(t["estado"] in ("completado", "fallido") for t in lote["trabajos"])
        if terminados:
            n_ok = sum(1 for t in lote["trabajos"] if t["estado"] == "completado")
            n_fail = sum(1 for t in lote["trabajos"] if t["estado"] == "fallido")
            lote["estado_lote"] = "completado"
            if n_fail:
                lote["mensaje"] = f"Lote terminado: {n_ok} completados, {n_fail} fallidos (omitidos)."
            else:
                lote["mensaje"] = "Lote completado."
            print(f"LOTE COMPLETADO: {n_ok} OK, {n_fail} fallidos")
            guardar_lote(lote); reportar_progreso(lote)
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
    tarea_id, motivo = encolar_video(siguiente["marca"], siguiente["formato"], siguiente.get("duracion_min"))
    if tarea_id:
        siguiente["estado"] = "en_proceso"; siguiente["tarea_id"] = tarea_id; siguiente["inicio_ts"] = time.time()
        siguiente["intentos"] = 0  # reset
        lote["trabajo_actual_desc"] = f"Generando video {siguiente['n']} ({siguiente['marca']})"
        lote["mensaje"] = f"Produccion del video {siguiente['n']} iniciada."
    elif motivo == "cuota":
        # La API de Gemini se quedó sin cuota. TODOS los videos fallarían igual.
        # Pausar el lote con mensaje claro en vez de quemar reintentos en cada uno.
        lote["estado_lote"] = "esperando_cuota"
        lote["mensaje"] = ("La API de Gemini se quedó sin cuota (límite diario). "
                           "El lote se reanudará solo cuando la cuota se restablezca.")
        lote["trabajo_actual_desc"] = "Esperando cuota de Gemini (se reintenta periódicamente)"
        print("Gemini sin cuota — lote en espera (se reintenta cada ciclo largo)")
        lote["reintentar_hasta"] = time.time() + ESPERA_CUOTA
    else:
        # FALLO puntual al encolar: reintentar con límite. Si se agota, marcar
        # fallido y CONTINUAR con el siguiente (no bloquear todo el lote).
        siguiente["intentos"] = siguiente.get("intentos", 0) + 1
        if siguiente["intentos"] >= MAX_INTENTOS_ENCOLADO:
            siguiente["estado"] = "fallido"
            siguiente["error"] = f"No se pudo encolar tras {siguiente['intentos']} intentos ({motivo})"
            lote["mensaje"] = (f"Video {siguiente['n']} ({siguiente['marca']} {siguiente['formato']}) "
                               f"falló al encolar {siguiente['intentos']} veces — se omite y se continúa.")
            print(f"FALLIDO Video {siguiente['n']} tras {siguiente['intentos']} intentos — se omite")
        else:
            lote["reintentar_hasta"] = time.time() + ESPERA_REINTENTO
            lote["mensaje"] = (f"No se pudo encolar el video {siguiente['n']} "
                               f"(intento {siguiente['intentos']}/{MAX_INTENTOS_ENCOLADO}), reintentando...")
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
    ultimo_ts_iniciar = 0  # ts del último 'iniciar' procesado (idempotencia ante latencia)
    while True:
        try:
            control = obtener_control()
            accion = control.get("accion", "")
            ts_control = control.get("ts", 0)
            hay_lote_activo = bool(lote and lote.get("estado_lote") not in ("completado", "cancelado"))
            if accion == "iniciar":
                # Idempotencia: ignorar si ya procesamos este mismo 'iniciar' (mismo ts)
                # o si ya hay un lote en curso. Evita recrear el lote por latencia del control.
                if ts_control and ts_control == ultimo_ts_iniciar:
                    pass  # ya lo procesamos; señal repetida por propagación lenta
                elif hay_lote_activo:
                    print("[CONTROL] 'iniciar' ignorado: ya hay un lote en curso.")
                    ultimo_ts_iniciar = ts_control
                    consumir_control()
                else:
                    ultimo_ts_iniciar = ts_control
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
