import json
import os

class UsuarioManager:
    def __init__(self):
        # Cambiamos la ruta a la raíz para evitar problemas de permisos
        self.db_path = os.path.join(os.getcwd(), "usuarios_db.json")
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({"admin": {"rol": "Master", "status": "Activo"}}, f)

    def listar_usuarios(self):
        if not os.path.exists(self.db_path): return {}
        with open(self.db_path, "r") as f:
            return json.load(f)
