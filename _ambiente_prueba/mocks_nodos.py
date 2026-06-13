"""
SIMULADORES DE NODOS — Ambiente de prueba del Sistema Pinpinela
Levanta servidores HTTP falsos que responden como los nodos reales (SD, DepthFlow,
Render, Voz) pero con datos sintéticos rápidos. Permite ejecutar el worker_cpu.py
REAL en este entorno y validar TODA la lógica de ensamblaje sin los nodos físicos.
"""
import http.server
import socketserver
import json
import threading
import base64
import os

# Imagen PNG mínima válida (1x1 pixel) en base64, para simular lo que devuelve SD
PNG_1X1 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

# Estado compartido para inspección desde el test
ESTADO = {
    "cola": [],                  # tareas pendientes que el worker pedirá
    "tareas_completadas": [],    # tareas que el worker reportó terminadas
    "uploads": [],               # resultados subidos
    "worker_estados": [],        # reportes de ocupado/libre
    "sd_llamadas": 0,
    "depthflow_llamadas": 0,
    "depthflow_fallos_forzados": 0,  # para simular el error 500
    "sd_descargado": False,
}


class MockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silenciar logs del servidor

    def _responder(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        # SD: consultar opciones (verificar que está vivo / modelo cargado)
        if "/sdapi/v1/options" in self.path:
            modelo = "" if ESTADO["sd_descargado"] else "juggernautXL.safetensors"
            self._responder(200, {"sd_model_checkpoint": modelo})
        # DepthFlow: health check
        elif "/health" in self.path:
            self._responder(200, {"depthflow": True, "status": "ok"})
        else:
            self._responder(200, {"ok": True})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        # ── STABLE DIFFUSION ──
        if "/sdapi/v1/txt2img" in self.path:
            ESTADO["sd_llamadas"] += 1
            # Generar una imagen realista (con detalle) y devolverla en base64,
            # para que los clips de FFmpeg no salgan corruptos
            import subprocess, tempfile
            try:
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.close()
                subprocess.run(
                    f"ffmpeg -y -f lavfi -i testsrc=s=576x1024:d=1 -frames:v 1 {tmp.name}",
                    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                with open(tmp.name, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                os.remove(tmp.name)
                self._responder(200, {"images": [img_b64]})
            except Exception:
                self._responder(200, {"images": [PNG_1X1]})
        elif "/sdapi/v1/unload-checkpoint" in self.path:
            ESTADO["sd_descargado"] = True
            self._responder(200, {"ok": True})
        elif "/sdapi/v1/reload-checkpoint" in self.path:
            ESTADO["sd_descargado"] = False
            self._responder(200, {"ok": True})

        # ── DEPTHFLOW ──
        elif "/parallax" in self.path:
            ESTADO["depthflow_llamadas"] += 1
            # Simular fallos 500 si se configuró (para probar el fallback a zoompan)
            if ESTADO["depthflow_fallos_forzados"] > 0:
                ESTADO["depthflow_fallos_forzados"] -= 1
                self._responder(500, {"error": "VRAM insuficiente (simulado)"})
            else:
                # Generar un MP4 falso en la ruta que pидe
                ruta = data.get("ruta_salida", "")
                if ruta:
                    try:
                        # MP4 mínimo (no válido pero con tamaño > 1000 bytes para pasar el check)
                        os.makedirs(os.path.dirname(ruta), exist_ok=True)
                        with open(ruta, "wb") as f:
                            f.write(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 2000)
                    except Exception:
                        pass
                self._responder(200, {"ok": True, "preset": "zoom"})

        # ── RENDER: polling (el worker pide trabajo) ──
        elif "/api/nodo/polling" in self.path:
            if ESTADO["cola"]:
                tarea = ESTADO["cola"].pop(0)
                self._responder(200, {"hay_trabajo": True, "tarea": tarea})
            else:
                self._responder(200, {"hay_trabajo": False})

        # ── RENDER: tarea completada ──
        elif "/api/nodo/tarea_completada" in self.path:
            ESTADO["tareas_completadas"].append(data.get("tarea_id"))
            self._responder(200, {"status": "ok"})

        # ── RENDER: upload result ──
        elif "/api/nodo/upload_result" in self.path:
            ESTADO["uploads"].append(data.get("tarea_id"))
            self._responder(200, {"status": "ok"})

        # ── RENDER: worker estado ──
        elif "/api/nodo/worker_estado" in self.path:
            ESTADO["worker_estados"].append(data)
            self._responder(200, {"status": "ok"})

        # ── RENDER: generar paquete ──
        elif "/api/interna/generar_paquete" in self.path:
            self._responder(200, {"status": "ok", "paquete": {"titulo": "Test", "descripcion": "Test"}})

        else:
            self._responder(200, {"ok": True})


def iniciar_servidor(puerto):
    httpd = socketserver.TCPServer(("127.0.0.1", puerto), MockHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def iniciar_todos():
    """Inicia los servidores en los puertos que el worker espera."""
    servidores = []
    # El worker usa estos puertos: SD=7861, DepthFlow=8500, Voz=8000
    # y Render en una URL. Todos apuntarán a 127.0.0.1 con port-forward lógico.
    for puerto in [7861, 8500, 8000, 9999]:  # 9999 = Render simulado
        try:
            servidores.append(iniciar_servidor(puerto))
        except Exception as e:
            print(f"No se pudo iniciar mock en puerto {puerto}: {e}")
    return servidores
