"""
═══════════════════════════════════════════════════════════════════════════
ORQUESTADOR DE LOTE — Motor de Producción Industrial (Sistema Pinpinela)
═══════════════════════════════════════════════════════════════════════════
Vive en el XEON (siempre encendido). Es el CEREBRO que orquesta la producción
masiva diaria por lotes, sin depender de Render (que se duerme).

QUÉ HACE:
  - Lee el PLAN SEMANAL (qué canal y cuántos shorts/largos por día)
  - A la hora de inicio del día, crea un LOTE de trabajos
  - Produce uno por uno: pide al worker (vía Render) que genere cada video,
    espera a que termine, espera el ENFRIAMIENTO, y pide el siguiente
  - PERSISTENCIA TOTAL: guarda el estado en disco tras cada paso
  - EVENTUALIDADES:
      * Nodo caído → PAUSA el lote, espera a que vuelva, reintenta
      * Corte de luz → al reiniciar, RETOMA donde quedó (no repite)
  - CONTROLES desde el panel: pausar / reanudar / reiniciar / cambiar hora

ARRANQUE: se ejecuta solo desde la carpeta Startup de Windows (iniciar_pinpinela.bat)
═══════════════════════════════════════════════════════════════════════════
"""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


import os
import json
import time
import uuid
import requests
from datetime import datetime, timezone, timedelta

# ── Configuración ────────────────────────────────────────────────────────────
RENDER_URL = "https://prompt-engineer-system-l2r6.onrender.com"
TZ_MEXICO = timezone(timedelta(hours=-6))

# Archivos de estado local (en el Xeon, sobreviven cortes de luz)
CARPETA_ESTADO = r"C:\NODO_PINPINELA\estado_lote"
os.makedirs(CARPETA_ESTADO, exist_ok=True)
ARCHIVO_LOTE = os.path.join(CARPETA_ESTADO, "lote_actual.json")

# Tiempos (segundos)
INTERVALO_CICLO       = 20      # cada cuánto el motor revisa qué hacer
ENFRIAMIENTO_DEFAULT  = 180     # 3 min entre videos (enfría nodos)
TIMEOUT_VIDEO         = 3600    # máx 1h por video antes de considerarlo colgado
ESPERA_NODO_CAIDO     = 60      # revisa cada 60s si un nodo caído ya volvió

# Nodos a vigilar
IP_GRAFICA = "192.168.0.215"
IP_VOZ     = "192.168.0.251"
NODOS = {
    "sd":       f"http://{IP_GRAFICA}:7861/sdapi/v1/options",
    "voz":      f"http://{IP_VOZ}:8000",
    "parallax": f"http://{IP_GRAFICA}:8500/health",
}


# ═══════════════════════════════════════════════════════════════════════════
# PERSISTENCIA — el estado del lote sobrevive cortes de luz
# ═══════════════════════════════════════════════════════════════════════════
def leer_lote():
    """Lee el lote en curso desde disco. None si no hay."""
    try:
        with open(ARCHIVO_LOTE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def guardar_lote(lote):
    """Guarda el estado del lote en disco (atómico para no corromper)."""
    try:
        tmp = ARCHIVO_LOTE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(lote, f, ensure_ascii=False, indent=2)
        os.replace(tmp, ARCHIVO_LOTE)  # reemplazo atómico
    except Exception as e:
        print(f"⚠️ Error guardando lote: {e}")

def borrar_lote():
    try:
        if os.path.exists(ARCHIVO_LOTE):
            os.remove(ARCHIVO_LOTE)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# COMUNICACIÓN CON RENDER — plan semanal, controles, y encolado
# ═══════════════════════════════════════════════════════════════════════════
def obtener_plan_semanal():
    """Lee el plan semanal configurado desde el panel (Render)."""
    try:
        r = requests.get(f"{RENDER_URL}/api/bot/plan_semanal", timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"⚠️ No se pudo leer el plan semanal: {e}")
    return {"dias": {}}

def obtener_control():
    """Lee las órdenes de control del panel (pausar/reanudar/reiniciar/hora)."""
    try:
        r = requests.get(f"{RENDER_URL}/api/bot/lote_control", timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}

def reportar_progreso(lote):
    """Envía el progreso del lote al panel para mostrarlo en vivo."""
    try:
        completados = sum(1 for t in lote["trabajos"] if t["estado"] == "completado")
        requests.post(f"{RENDER_URL}/api/bot/lote_progreso", json={
            "fecha": lote.get("fecha"),
            "canal_resumen": lote.get("canal_resumen", ""),
            "total": len(lote["trabajos"]),
            "completados": completados,
            "estado_lote": lote.get("estado_lote"),
            "trabajo_actual": lote.get("trabajo_actual_desc", ""),
            "mensaje": lote.get("mensaje", ""),
        }, timeout=20)
    except Exception:
        pass

def encolar_video(marca, formato):
    """Pide a Render que genere un video (el worker lo tomará). Devuelve tarea_id."""
    try:
        r = requests.post(f"{RENDER_URL}/api/bot/lanzar_orden_motor",
                          json={"marca": marca, "formato": formato}, timeout=120)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "PENDING_REVIEW" or data.get("tarea_id"):
                return data.get("tarea_id")
    except Exception as e:
        print(f"⚠️ Error encolando video: {e}")
    return None

def video_esta_listo(tarea_id):
    """Pregunta a Render si el video de esa tarea ya terminó."""
    try:
        r = requests.get(f"{RENDER_URL}/api/bot/video_estado",
                        params={"tarea_id": tarea_id}, timeout=20)
        if r.status_code == 200:
            return r.json().get("completado", False)
    except Exception:
        pass
    return False


# ═══════════════════════════════════════════════════════════════════════════
# VIGILANCIA DE NODOS — para pausar si se cae alguno
# ═══════════════════════════════════════════════════════════════════════════
def ping_nodo(url, timeout=6):
    try:
        requests.get(url, timeout=timeout)
        return True
    except Exception:
        return False

def nodos_criticos_vivos(necesita_voz=True):
    """Verifica que los nodos críticos estén vivos. Devuelve (ok, lista_caidos)."""
    caidos = []
    if not ping_nodo(NODOS["sd"]):
        caidos.append("SD (imágenes)")
    if necesita_voz and not ping_nodo(NODOS["voz"]):
        caidos.append("Voz")
    return (len(caidos) == 0, caidos)


# ═══════════════════════════════════════════════════════════════════════════
# CREACIÓN DEL LOTE DIARIO
# ═══════════════════════════════════════════════════════════════════════════
DIAS_SEMANA = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

def crear_lote_del_dia(plan, fecha_str, dia_nombre):
    """Crea el lote de trabajos para hoy según el plan semanal."""
    config_dia = plan.get("dias", {}).get(dia_nombre)
    if not config_dia or not config_dia.get("activo"):
        return None

    entradas = config_dia.get("entradas", [])  # [{marca, shorts, largos}]
    if not entradas:
        return None

    trabajos = []
    contador = 0
    resumen_partes = []
    for entrada in entradas:
        marca = entrada.get("marca")
        n_shorts = int(entrada.get("shorts", 0))
        n_largos = int(entrada.get("largos", 0))
        resumen_partes.append(f"{marca}: {n_shorts}s+{n_largos}L")
        for _ in range(n_shorts):
            contador += 1
            trabajos.append({"n": contador, "marca": marca, "formato": "9:16",
                             "estado": "pendiente", "tarea_id": None, "intentos": 0})
        for _ in range(n_largos):
            contador += 1
            trabajos.append({"n": contador, "marca": marca, "formato": "16:9",
                             "estado": "pendiente", "tarea_id": None, "intentos": 0})

    if not trabajos:
        return None

    return {
        "fecha": fecha_str,
        "dia": dia_nombre,
        "canal_resumen": " | ".join(resumen_partes),
        "enfriamiento": int(config_dia.get("enfriamiento", ENFRIAMIENTO_DEFAULT)),
        "trabajos": trabajos,
        "estado_lote": "produciendo",   # produciendo | pausado | esperando_nodo | completado
        "trabajo_actual_desc": "",
        "mensaje": "Lote creado, iniciando producción.",
        "creado_ts": time.time(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# MOTOR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
def procesar_lote(lote):
    """Procesa el siguiente trabajo pendiente del lote. Devuelve el lote actualizado."""

    # 1. Revisar controles del panel (pausar/reanudar/reiniciar)
    control = obtener_control()
    accion = control.get("accion", "")

    if accion == "reiniciar":
        print("🔄 [CONTROL] Reiniciar lote — empezando de cero")
        for t in lote["trabajos"]:
            t["estado"] = "pendiente"
            t["tarea_id"] = None
            t["intentos"] = 0
        lote["estado_lote"] = "produciendo"
        lote["mensaje"] = "Lote reiniciado por el operador."
        _consumir_control()
    elif accion == "pausar":
        print("⏸️ [CONTROL] Pausar lote")
        lote["estado_lote"] = "pausado"
        lote["mensaje"] = "Pausado por el operador."
        _consumir_control()
        guardar_lote(lote)
        reportar_progreso(lote)
        return lote
    elif accion == "reanudar":
        print("▶️ [CONTROL] Reanudar lote")
        lote["estado_lote"] = "produciendo"
        lote["mensaje"] = "Reanudado por el operador."
        _consumir_control()

    # Si está pausado, no hacer nada
    if lote["estado_lote"] == "pausado":
        reportar_progreso(lote)
        return lote

    # 2. ¿Hay un trabajo en proceso? (esperar a que termine)
    en_proceso = next((t for t in lote["trabajos"] if t["estado"] == "en_proceso"), None)
    if en_proceso:
        if en_proceso.get("tarea_id") and video_esta_listo(en_proceso["tarea_id"]):
            en_proceso["estado"] = "completado"
            lote["mensaje"] = f"Video {en_proceso['n']} completado ✅"
            lote["enfriando_hasta"] = time.time() + lote.get("enfriamiento", ENFRIAMIENTO_DEFAULT)
            print(f"✅ Video {en_proceso['n']} ({en_proceso['marca']}) completado")
            guardar_lote(lote)
            reportar_progreso(lote)
        else:
            # Sigue generándose, o timeout
            inicio = en_proceso.get("inicio_ts", time.time())
            if time.time() - inicio > TIMEOUT_VIDEO:
                print(f"⏱️ Video {en_proceso['n']} excedió el timeout — reintentando")
                en_proceso["estado"] = "pendiente"
                en_proceso["intentos"] += 1
            lote["trabajo_actual_desc"] = f"Generando video {en_proceso['n']} ({en_proceso['marca']} {en_proceso['formato']})"
            reportar_progreso(lote)
        return lote

    # 3. ¿Estamos en enfriamiento? (esperar antes del siguiente)
    enfriando_hasta = lote.get("enfriando_hasta", 0)
    if time.time() < enfriando_hasta:
        restante = int(enfriando_hasta - time.time())
        lote["estado_lote"] = "produciendo"
        lote["trabajo_actual_desc"] = f"Enfriando nodos... {restante}s"
        lote["mensaje"] = f"Enfriamiento entre videos: {restante}s restantes"
        reportar_progreso(lote)
        return lote

    # 4. Buscar el siguiente trabajo pendiente
    siguiente = next((t for t in lote["trabajos"] if t["estado"] == "pendiente"), None)
    if not siguiente:
        # No quedan pendientes → lote completado
        if all(t["estado"] == "completado" for t in lote["trabajos"]):
            lote["estado_lote"] = "completado"
            lote["mensaje"] = "🏆 Lote del día completado."
            print("🏆 LOTE DEL DÍA COMPLETADO")
            guardar_lote(lote)
            reportar_progreso(lote)
        return lote

    # 5. Antes de lanzar: verificar que los nodos estén vivos
    necesita_voz = True  # siempre se necesita voz para el video completo
    ok, caidos = nodos_criticos_vivos(necesita_voz)
    if not ok:
        lote["estado_lote"] = "esperando_nodo"
        lote["mensaje"] = f"⏸️ Nodo(s) caído(s): {', '.join(caidos)}. Esperando que vuelvan..."
        lote["trabajo_actual_desc"] = f"Pausado — esperando: {', '.join(caidos)}"
        print(f"🔴 Nodo caído: {caidos} — pausando lote hasta que vuelva")
        guardar_lote(lote)
        reportar_progreso(lote)
        time.sleep(ESPERA_NODO_CAIDO)  # esperar antes de revisar de nuevo
        return lote

    # 6. Lanzar el siguiente video
    print(f"🚀 Lanzando video {siguiente['n']}/{len(lote['trabajos'])}: {siguiente['marca']} {siguiente['formato']}")
    tarea_id = encolar_video(siguiente["marca"], siguiente["formato"])
    if tarea_id:
        siguiente["estado"] = "en_proceso"
        siguiente["tarea_id"] = tarea_id
        siguiente["inicio_ts"] = time.time()
        lote["estado_lote"] = "produciendo"
        lote["trabajo_actual_desc"] = f"Generando video {siguiente['n']} ({siguiente['marca']})"
        lote["mensaje"] = f"Producción del video {siguiente['n']} iniciada."
    else:
        siguiente["intentos"] += 1
        lote["mensaje"] = f"No se pudo encolar el video {siguiente['n']} (intento {siguiente['intentos']})"
        if siguiente["intentos"] >= 5:
            siguiente["estado"] = "fallido"
            lote["mensaje"] = f"Video {siguiente['n']} marcado como fallido tras 5 intentos."

    guardar_lote(lote)
    reportar_progreso(lote)
    return lote


def _consumir_control():
    """Marca el control como ya ejecutado en Render (para no repetirlo)."""
    try:
        requests.post(f"{RENDER_URL}/api/bot/lote_control", json={"accion": ""}, timeout=20)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# BUCLE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("═" * 60)
    print("⚙️  ORQUESTADOR DE LOTE — Motor de Producción Industrial")
    print("    Vive en el Xeon · Retoma tras cortes de luz")
    print("═" * 60)

    # Al arrancar: ¿había un lote en curso? (recuperación tras corte de luz)
    lote = leer_lote()
    if lote:
        fecha_lote = lote.get("fecha")
        hoy = datetime.now(TZ_MEXICO).strftime("%Y-%m-%d")
        if fecha_lote == hoy and lote.get("estado_lote") != "completado":
            completados = sum(1 for t in lote["trabajos"] if t["estado"] == "completado")
            print(f"🔁 RECUPERACIÓN: lote de hoy encontrado — {completados}/{len(lote['trabajos'])} hechos")
            print(f"   Estado: {lote.get('estado_lote')} — retomando donde quedó")
            # Si un video quedó "en_proceso" al cortarse la luz, lo reintentamos
            for t in lote["trabajos"]:
                if t["estado"] == "en_proceso":
                    t["estado"] = "pendiente"
                    print(f"   Video {t['n']} estaba a medias — se reintentará")
        else:
            lote = None  # el lote guardado es viejo, se ignora

    while True:
        try:
            ahora = datetime.now(TZ_MEXICO)
            hoy = ahora.strftime("%Y-%m-%d")
            dia_nombre = DIAS_SEMANA[ahora.weekday()]
            hora_actual = ahora.strftime("%H:%M")

            plan = obtener_plan_semanal()

            # ¿Hay un lote activo de hoy?
            if lote and lote.get("fecha") == hoy:
                if lote.get("estado_lote") != "completado":
                    lote = procesar_lote(lote)
                # si está completado, no hacer nada más hoy
            else:
                # ¿Es hora de crear el lote de hoy?
                config_dia = plan.get("dias", {}).get(dia_nombre, {})
                hora_inicio = config_dia.get("hora_inicio", "08:00")
                if config_dia.get("activo") and hora_actual >= hora_inicio:
                    # Evitar recrear si ya se hizo hoy
                    if not (lote and lote.get("fecha") == hoy):
                        nuevo = crear_lote_del_dia(plan, hoy, dia_nombre)
                        if nuevo:
                            lote = nuevo
                            guardar_lote(lote)
                            print(f"📋 LOTE CREADO para {dia_nombre} ({hoy}): {lote['canal_resumen']}")

        except Exception as e:
            print(f"⚠️ Error en ciclo del orquestador: {e}")

        time.sleep(INTERVALO_CICLO)


if __name__ == "__main__":
    main()
