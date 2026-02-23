import json
import os

class UsuarioManager:
    def __init__(self):
        self.db_path = os.path.join(os.getcwd(), "usuarios_db.json")
        self._inicializar_db()

    def _inicializar_db(self):
        # Si no existe o está vacío (corrupto), lo regenera con el Master
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            self._escribir_default()

    def _escribir_default(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump({"admin": {"rol": "Master", "status": "Activo"}}, f, indent=4)

    def listar_usuarios(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Si el archivo se rompió, lo repara y devuelve el admin
            self._escribir_default()
            return {"admin": {"rol": "Master", "status": "Reparado Automáticamente"}}
        except Exception as e:
            return {"admin": {"rol": "Error Critico", "status": str(e)}}

    def agregar_usuario(self, username, rol):
        try:
            usuarios = self.listar_usuarios()
            usuarios[username] = {"rol": rol, "status": "Activo"}
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(usuarios, f, indent=4)
            return True
        except Exception:
            return False
