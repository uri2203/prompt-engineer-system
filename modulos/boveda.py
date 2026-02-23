import json
import os

class BovedaManager:
    def __init__(self):
        self.db_path = os.path.join(os.getcwd(), "boveda_db.json")
        self._inicializar_db()

    def _inicializar_db(self):
        # Si la bóveda no existe, crea la estructura blindada por defecto
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            self._guardar({"gemini_keys": []})

    def _guardar(self, datos):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4)

    def obtener_llaves(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                datos = json.load(f)
                return datos.get("gemini_keys", [])
        except Exception:
            return []

    def guardar_llaves(self, llaves_list):
        # Limpia espacios en blanco accidentales al pegar las llaves
        llaves_limpias = [llave.strip() for llave in llaves_list if llave.strip()]
        datos = {"gemini_keys": llaves_limpias}
        self._guardar(datos)
        return True
