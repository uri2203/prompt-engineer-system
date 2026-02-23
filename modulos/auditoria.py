import os
from datetime import datetime

class AuditoriaSystem:
    def __init__(self):
        self.log_file = os.path.join(os.getcwd(), "logs_sistema.txt")
        if not os.path.exists(self.log_file):
            try:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.write(f"--- INICIO DE BITÁCORA DEL SISTEMA PINPINELA ---\n")
            except Exception:
                pass # Silencia el error para no tirar el servidor

    def registrar(self, modulo, evento, estado="INFO"):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entrada = f"[{timestamp}] [{estado}] [{modulo}] -> {evento}\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entrada)
        except Exception:
            pass # Si falla el disco, el bot sigue operando

    def leer_ultimos(self, lineas=50):
        try:
            if not os.path.exists(self.log_file) or os.path.getsize(self.log_file) == 0:
                return ["La bitácora está limpia o esperando eventos.\n"]
            with open(self.log_file, "r", encoding="utf-8") as f:
                contenido = f.readlines()
                return contenido[-lineas:]
        except Exception as e:
            return [f"ERROR DEL KERNEL AL LEER LOGS: {str(e)}\n"]
