import json
import os

class ConfigManager:
    def __init__(self):
        # La bóveda se almacena en la raíz para evitar bloqueos de permisos en Render
        self.db_path = os.path.join(os.getcwd(), "config_db.json")
        self._inicializar_db()

    def _inicializar_db(self):
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            self._escribir_default()

    def _escribir_default(self):
        default_config = {
            "gemini_master": "",
            "gemini_failover1": "",
            "gemini_failover2": "",
            "gemini_failover3": "",
            "gemini_reserva": "",
            "elevenlabs_master": ""
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)

    def leer_configuracion(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            self._escribir_default()
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def guardar_configuracion(self, config_data):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            return True
        except Exception:
            return False
