import json
import os

class BovedaManager:
    def __init__(self):
        self.db_path = os.path.join(os.getcwd(), "boveda_db.json")
        self._inicializar_db()

    def _inicializar_db(self):
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            self._guardar({
                "gemini_keys": [],
                "voice_api": "",
                "youtube_api": "",
                "tiktok_api": ""
            })

    def _guardar(self, datos):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4)

    def obtener_datos(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                datos = json.load(f)
                # Persistencia: Si la Bóveda está vacía, intenta leer del Servidor
                if not datos.get("gemini_keys"):
                    env_keys = os.environ.get("GEMINI_KEYS", "")
                    if env_keys:
                        datos["gemini_keys"] = [k.strip() for k in env_keys.split(",") if k.strip()]
                return datos
        except Exception:
            return {"gemini_keys": [], "voice_api": "", "youtube_api": "", "tiktok_api": ""}

    def obtener_llaves(self):
        datos = self.obtener_datos()
        return datos.get("gemini_keys", [])

    def guardar_boveda_completa(self, gemini_list, voice, youtube, tiktok):
        llaves_limpias = [llave.strip() for llave in gemini_list if llave.strip()]
        datos = {
            "gemini_keys": llaves_limpias,
            "voice_api": voice.strip(),
            "youtube_api": youtube.strip(),
            "tiktok_api": tiktok.strip()
        }
        self._guardar(datos)
        return True
