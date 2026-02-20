import hashlib

# Base de datos de usuario administrador (Cifrada)
USUARIOS_DB = {
    "1978": hashlib.sha256("1978".encode()).hexdigest()
}

def verificar_usuario(username, password):
    """Verifica si las credenciales coinciden con el registro cifrado."""
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if username in USUARIOS_DB and USUARIOS_DB[username] == pw_hash:
        return True
    return False
