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
            # Intentar leer el archivo físico primero
            datos = {"gemini_keys": [], "voice_api": "", "youtube_api": "", "tiktok_api": ""}
            if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    datos = json.load(f)
            
            # BLINDAJE RENDER: Si el archivo no tiene llaves, forzar lectura de Variables de Entorno
            if not datos.get("gemini_keys") or len(datos.get("gemini_keys")) == 0:
                env_keys = os.environ.get("GEMINI_KEYS", "")
                if env_keys:
                    datos["gemini_keys"] = [k.strip() for k in env_keys.split(",") if k.strip()]
            
            # Cargar el resto de APIs desde el entorno si no están en el JSON
            if not datos.get("voice_api"): datos["voice_api"] = os.environ.get("VOICE_API", "")
            if not datos.get("youtube_api"): datos["youtube_api"] = os.environ.get("YOUTUBE_API", "")
            if not datos.get("tiktok_api"): datos["tiktok_api"] = os.environ.get("TIKTOK_API", "")
                
            return datos
        except Exception as e:
            print(f"[DEBUG BOVEDA] Fallo crítico al obtener datos: {e}")
            return {"gemini_keys": [], "voice_api": "", "youtube_api": "", "tiktok_api": ""}

    def obtener_llaves(self):
        datos = self.obtener_datos()
        llaves = datos.get("gemini_keys", [])
        print(f"[DEBUG BOVEDA] Llaves recuperadas: {len(llaves)}") # Sonda para consola
        return llaves

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
