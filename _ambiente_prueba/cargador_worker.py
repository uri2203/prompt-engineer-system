"""
CARGADOR DEL WORKER REAL — parchea rutas Windows y URLs para el ambiente de prueba.
NO modifica la lógica del worker; solo redirige:
  - C:\\DarkFactory_Renders  → sandbox local
  - C:\\DarkFactory_ASSETS    → sandbox_assets local
  - C:\\NODO_PINPINELA        → nodo_pinpinela local
  - IPs reales (192.168.x)    → 127.0.0.1 (mocks)
  - Render URL                → 127.0.0.1:9999 (mock)
"""
import os
import re

BASE = "/home/claude/test_env"
SANDBOX = os.path.join(BASE, "sandbox")
ASSETS = os.path.join(BASE, "sandbox_assets")
NODO = os.path.join(BASE, "nodo_pinpinela")

def cargar_worker_parcheado():
    """Lee worker_cpu.py, parchea rutas/URLs, y lo deja listo para importar."""
    with open("/home/claude/worker_cpu.py", encoding="utf-8") as f:
        codigo = f.read()

    # ── Parchear rutas Windows → sandbox local ──
    codigo = codigo.replace('"C:\\\\DarkFactory_Renders"', repr(SANDBOX))
    codigo = codigo.replace('"C:\\\\DarkFactory_ASSETS"', repr(ASSETS))
    codigo = codigo.replace('C:\\\\NODO_PINPINELA', NODO.replace("/", "/"))
    # Rutas con r"..." (raw strings)
    codigo = codigo.replace(r'r"C:\NODO_PINPINELA\cola_local"', repr(os.path.join(NODO, "cola_local")))
    codigo = codigo.replace(r'rf"C:\NODO_PINPINELA\cola_local\ensamblaje_{tarea_id}.json"',
                            f'os.path.join({repr(os.path.join(NODO, "cola_local"))}, f"ensamblaje_{{tarea_id}}.json")')
    codigo = codigo.replace('"C:\\\\NODO_PINPINELA"', repr(NODO))

    # ── Parchear IPs y URLs → mocks locales ──
    codigo = codigo.replace('192.168.0.215', '127.0.0.1')
    codigo = codigo.replace('192.168.0.251', '127.0.0.1')
    codigo = codigo.replace('"https://prompt-engineer-system-l2r6.onrender.com"', '"http://127.0.0.1:9999"')

    # ── El worker corre en bucle infinito (while True). Para la prueba, lo quitamos
    #    y exponemos procesar() para llamarlo manualmente ──
    codigo = codigo.replace(
        'print("⚡ NODO XEON ONLINE - FIX ANTI-BUCLE APLICADO")\nwhile True:\n    procesar()\n    time.sleep(2)',
        '# [TEST] bucle principal desactivado — se llama procesar() desde el test'
    )
    # Por si el formato del bucle es ligeramente distinto, quitarlo con regex
    codigo = re.sub(r'while True:\s*\n\s*procesar\(\)\s*\n\s*time\.sleep\(\d+\)',
                    '# [TEST] bucle desactivado', codigo)

    # ── Guardar el worker parcheado y cargarlo como módulo ──
    ruta_parcheado = os.path.join(BASE, "worker_test.py")
    with open(ruta_parcheado, "w", encoding="utf-8") as f:
        f.write(codigo)

    # Asegurar que el voice_local mock esté en el path
    import sys
    sys.path.insert(0, NODO)
    sys.path.insert(0, BASE)

    import importlib.util
    spec = importlib.util.spec_from_file_location("worker_test", ruta_parcheado)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    return worker
