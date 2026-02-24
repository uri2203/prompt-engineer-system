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
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4)
        except Exception:
            pass # Falla silenciosa permitida para entornos de nube estrictos

    def obtener_datos(self):
        datos_locales = {"gemini_keys": [], "voice_api": "", "youtube_api": "", "tiktok_api": ""}
        
        # 1. Recuperación de caché efímera (Sesión Activa de UI)
        try:
            if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    datos_locales = json.load(f)
        except Exception:
            pass

        # 2. INYECCIÓN ABSOLUTA (Variables de Entorno)
        # Las variables del servidor siempre tendrán prioridad y sobrevivirán a cualquier reinicio.
        env_gemini = os.environ.get("GEMINI_KEYS", "")
        env_voice = os.environ.get("VOICE_API", "")
        env_youtube = os.environ.get("YOUTUBE_API", "")
        env_tiktok = os.environ.get("TIKTOK_API", "")

        if env_gemini:
            # Soporta múltiples llaves separadas por coma
            datos_locales["gemini_keys"] = [k.strip() for k in env_gemini.split(",") if k.strip()]
        if env_voice:
            datos_locales["voice_api"] = env_voice.strip()
        if env_youtube:
            datos_locales["youtube_api"] = env_youtube.strip()
        if env_tiktok:
            datos_locales["tiktok_api"] = env_tiktok.strip()

        return datos_locales

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
