import os
from datetime import datetime

class AuditoriaSystem:
    def __init__(self):
        self.log_file = os.path.join(os.getcwd(), "logs_sistema.txt")
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write(f"--- INICIO DE BITÁCORA DE PINPINELA - {datetime.now()} ---\n")

    def registrar(self, modulo, evento, estado="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entrada = f"[{timestamp}] [{estado}] [{modulo}] -> {evento}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entrada)

    def leer_ultimos(self, lineas=50):
        if not os.path.exists(self.log_file):
            return ["No hay registros previos."]
        with open(self.log_file, "r", encoding="utf-8") as f:
            contenido = f.readlines()
            return contenido[-lineas:]
