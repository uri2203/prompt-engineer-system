import json
import os

class UsuarioManager:
    def __init__(self):
        self.db_path = os.path.join(os.getcwd(), "data", "usuarios.json")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            # Usuario maestro por defecto
            with open(self.db_path, "w") as f:
                json.dump({"admin": {"rol": "Master", "status": "Activo"}}, f)

    def listar_usuarios(self):
        with open(self.db_path, "r") as f:
            return json.load(f)

    def agregar_usuario(self, username, rol):
        usuarios = self.listar_usuarios()
        usuarios[username] = {"rol": rol, "status": "Activo"}
        with open(self.db_path, "w") as f:
            json.dump(usuarios, f, indent=4)
        return True
