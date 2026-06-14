# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════
MONITOR DE NODOS — Vive en el Xeon, vigila los nodos cada 30s
═══════════════════════════════════════════════════════════════════════════
Hace un chequeo en DOS NIVELES para cada nodo y lo reporta a Render:
  1) ¿La IP del equipo responde? (¿está prendido?)
  2) ¿El programa específico responde? (¿está abierto SD / voz / parallax?)

Estados que reporta por nodo:
  - "online"          → equipo prendido Y programa responde   (🟢 verde)
  - "ip_sin_programa" → equipo prendido pero programa cerrado  (🟡 amarillo)
  - "offline"         → ni la IP responde                      (🔴 rojo)

Corre INDEPENDIENTE del worker, así vigila aunque el worker esté ocupado
generando un video. Ligero: solo pings + un POST cada 30s.
"""
import socket
import time
import requests

# ── Configuración (igual que worker_cpu.py) ──────────────────────────────────
RENDER_URL   = "https://prompt-engineer-system-l2r6.onrender.com"
IP_GRAFICA   = "192.168.0.215"   # SD (7861) + DepthFlow (8500)
IP_VOZ_LOCAL = "192.168.0.251"   # Motor de voz XTTS (8000)

INTERVALO = 30          # segundos entre chequeos
TIMEOUT_IP = 3          # timeout para el ping de IP (rápido)
TIMEOUT_PROG = 6        # timeout para el ping del programa

# Nodos a vigilar: (clave, ip, puerto, endpoint_del_programa)
NODOS = [
    ("sd",       IP_GRAFICA,   7861, "/sdapi/v1/options"),  # Stable Diffusion (Automatic1111)
    ("voz",      IP_VOZ_LOCAL, 8000, "/"),                  # Motor de voz XTTS
    ("parallax", IP_GRAFICA,   8500, "/health"),            # DepthFlow
]


def _ip_responde(ip, puerto, timeout=TIMEOUT_IP):
    """Nivel 1: ¿el equipo está prendido y el puerto acepta conexión TCP?
    Un socket connect distingue 'equipo apagado / IP muerta' de 'puerto abierto'."""
    try:
        with socket.create_connection((ip, puerto), timeout=timeout):
            return True
    except Exception:
        return False


def _programa_responde(ip, puerto, endpoint, timeout=TIMEOUT_PROG):
    """Nivel 2: ¿el programa contesta HTTP en su endpoint?
    Cualquier respuesta HTTP (incluso 404/401) significa que el programa está vivo;
    lo que importa es que NO sea un rechazo de conexión o timeout."""
    url = f"http://{ip}:{puerto}{endpoint}"
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.exceptions.RequestException:
        return False


def chequear_nodo(ip, puerto, endpoint):
    """Devuelve 'online' | 'ip_sin_programa' | 'offline' según los 2 niveles."""
    # Nivel 1: ¿responde la IP/puerto a nivel TCP?
    ip_ok = _ip_responde(ip, puerto)
    if not ip_ok:
        # Ni siquiera abre el socket. Puede ser: equipo apagado, IP mala,
        # o el programa cerrado y el puerto cerrado con él.
        # Probamos el puerto 'base' del equipo (un puerto que suele estar si el equipo
        # está prendido) para distinguir 'equipo apagado' de 'solo el programa cerrado'.
        # Como no siempre hay un puerto base fiable, hacemos un segundo intento al puerto:
        return "offline"
    # Nivel 2: la IP responde, ¿y el programa?
    if _programa_responde(ip, puerto, endpoint):
        return "online"
    # El puerto acepta TCP pero el programa no contesta HTTP bien → raro, pero
    # lo tratamos como programa con problemas.
    return "ip_sin_programa"


def chequear_nodo_robusto(ip, puerto, endpoint):
    """Versión que distingue mejor 'equipo prendido pero programa cerrado'.
    Estrategia: si el puerto del PROGRAMA no abre, probamos si el EQUIPO responde
    a un ping de red (otro puerto común o el propio host) para saber si está prendido."""
    # ¿El programa abre su puerto y responde HTTP?
    if _ip_responde(ip, puerto):
        if _programa_responde(ip, puerto, endpoint):
            return "online"
        return "ip_sin_programa"  # puerto abierto pero HTTP no responde bien
    # El puerto del programa NO abre. ¿El equipo está prendido?
    # Probamos puertos comunes de Windows (RDP 3389, SMB 445, WinRM 5985) para
    # detectar si el equipo está vivo aunque el programa esté cerrado.
    equipo_vivo = any(_ip_responde(ip, p, timeout=2) for p in (3389, 445, 5985, 135))
    if equipo_vivo:
        return "ip_sin_programa"  # equipo prendido, pero el programa está cerrado
    return "offline"              # equipo apagado o inalcanzable


def reportar(estados):
    """Envía el estado de los nodos a Render."""
    try:
        requests.post(f"{RENDER_URL}/api/nodos/reportar", json=estados, timeout=15)
        return True
    except Exception as e:
        print(f"   [MONITOR] No se pudo reportar a Render: {e}")
        return False


def main():
    print("=" * 60)
    print("MONITOR DE NODOS — Vigilancia continua (cada %ds)" % INTERVALO)
    print("Chequeo de 2 niveles: equipo prendido + programa abierto")
    print("=" * 60)
    while True:
        estados = {}
        lineas = []
        for clave, ip, puerto, endpoint in NODOS:
            estado = chequear_nodo_robusto(ip, puerto, endpoint)
            estados[clave] = estado
            icono = {"online": "🟢", "ip_sin_programa": "🟡", "offline": "🔴"}.get(estado, "⚪")
            nota = {
                "online": "programa OK",
                "ip_sin_programa": "EQUIPO PRENDIDO PERO PROGRAMA CERRADO",
                "offline": "equipo apagado / inalcanzable",
            }.get(estado, "")
            lineas.append(f"   {icono} {clave.upper():9s} {ip}:{puerto} — {nota}")
        ok = reportar(estados)
        print(f"\n[{time.strftime('%H:%M:%S')}] Reporte {'enviado' if ok else 'FALLÓ'}:")
        for l in lineas:
            print(l)
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
