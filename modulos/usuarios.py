import json
import os

class UsuarioManager:
    def __init__(self):
        self.db_path = os.path.join(os.getcwd(), "usuarios_db.json")
        self._inicializar_db()

    def _inicializar_db(self):
        # Si el archivo no existe, crea el admin por defecto
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            default_admin = {
                "admin": {
                    "pass": "admin1978", 
                    "nombre": "Administrador Master", 
                    "rol": "Master Control"
                }
            }
            self._guardar(default_admin)

    def _guardar(self, datos):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4)

    def listar_usuarios(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def agregar_usuario(self, user, pw, nombre, rol):
        datos = self.listar_usuarios()
        datos[user] = {
            "pass": pw,
            "nombre": nombre,
            "rol": rol
        }
        self._guardar(datos)
        return True
