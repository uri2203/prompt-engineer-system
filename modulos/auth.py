import hashlib
import json
import os

# Base de datos persistente en formato JSON
DB_PATH = 'usuarios_db.json'

def cargar_db():
    """Carga la base de datos desde el archivo JSON o crea la inicial."""
    if not os.path.exists(DB_PATH):
        # Credenciales maestras del Administrador 1978 por defecto
        admin_pw = hashlib.sha256("1978".encode()).hexdigest()
        db = {"1978": admin_pw}
        guardar_db(db)
        return db
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}

def guardar_db(db):
    """Guarda los usuarios en el archivo físico."""
    with open(DB_PATH, 'w') as f:
        json.dump(db, f)

def verificar_usuario(username, password):
    """Verifica credenciales contra la DB cifrada."""
    db = cargar_db()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    return db.get(username) == pw_hash

def registrar_nuevo_usuario(username, password):
    """Agrega un nuevo colaborador a la base de datos."""
    db = cargar_db()
    if username in db:
        return False, "El usuario ya existe."
    db[username] = hashlib.sha256(password.encode()).hexdigest()
    guardar_db(db)
    return True, f"Usuario {username} registrado con éxito."
