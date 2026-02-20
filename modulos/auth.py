import hashlib
import json
import os

# Ruta para persistir usuarios en un archivo JSON (Base de datos ligera)
DB_PATH = 'usuarios_db.json'

def cargar_db():
    if not os.path.exists(DB_PATH):
        # Credenciales iniciales del Administrador 1978
        admin_pw = hashlib.sha256("1978".encode()).hexdigest()
        db = {"1978": admin_pw}
        guardar_db(db)
        return db
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def guardar_db(db):
    with open(DB_PATH, 'w') as f:
        json.dump(db, f)

def verificar_usuario(username, password):
    db = cargar_db()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    return db.get(username) == pw_hash

def registrar_nuevo_usuario(username, password):
    db = cargar_db()
    if username in db:
        return False, "El usuario ya existe."
    db[username] = hashlib.sha256(password.encode()).hexdigest()
    guardar_db(db)
    return True, "Usuario registrado con éxito."
