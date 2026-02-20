import os
import json
import hashlib
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)
# Llave de seguridad basada en tu usuario administrador
app.secret_key = os.environ.get("FLASK_KEY", "secret_key_1978_secure")

# Configuración de IA
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# --- SISTEMA DE SEGURIDAD INTEGRADO (Para evitar fallos de importación) ---
DB_PATH = 'usuarios_db.json'

def inicializar_seguridad():
    """Crea la base de datos inicial si no existe para evitar el Internal Server Error."""
    if not os.path.exists(DB_PATH):
        admin_pw = hashlib.sha256("1978".encode()).hexdigest()
        with open(DB_PATH, 'w') as f:
            json.dump({"1978": admin_pw}, f)

def verificar_credenciales(u, p):
    if not os.path.exists(DB_PATH): inicializar_seguridad()
    with open(DB_PATH, 'r') as f:
        db = json.load(f)
    pw_hash = hashlib.sha256(p.encode()).hexdigest()
    return db.get(u) == pw_hash

def registrar_en_db(u, p):
    with open(DB_PATH, 'r') as f:
        db = json.load(f)
    if u in db: return False, "Usuario ya existe"
    db[u] = hashlib.sha256(p.encode()).hexdigest()
    with open(DB_PATH, 'w') as f:
        json.dump(db, f)
    return True, f"Usuario {u} creado."

# --- RUTAS DEL SISTEMA ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    inicializar_seguridad()
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if verificar_credenciales(u, p):
            session['user'] = u
            session['isAdmin'] = (u == '1978')
            return redirect(url_for('dashboard'))
        return "Acceso denegado", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html', is_admin=session.get('isAdmin'))

@app.route('/api/registrar', methods=['POST'])
def registrar():
    if not session.get('isAdmin'): return jsonify({'error': 'No autorizado'}), 403
    data = request.json
    exito, msg = registrar_en_db(data.get('username'), data.get('password'))
    return jsonify({'status': 'success' if exito else 'error', 'message': msg})

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar_prompt():
    if 'user' not in session: return jsonify({'error': 'No autorizado'}), 401
    try:
        payload = request.json
        # Lógica de prompts integrada para máxima estabilidad
        modulo = payload.get('modulo_id')
        datos = payload.get('datos', {})
        prompt = f"Actúa como experto en {modulo}. Tarea: {datos}" # Simplificado para test
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return jsonify({'status': 'success', 'resultado_ia': response.text})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    inicializar_seguridad()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
