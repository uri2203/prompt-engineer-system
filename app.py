import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import google.generativeai as genai
from modulos.config import obtener_prompt_base
from modulos.auth import verificar_usuario, registrar_nuevo_usuario

app = Flask(__name__)
# Llave secreta para mantener las sesiones seguras
app.secret_key = os.environ.get("FLASK_KEY", "secret_key_1978_secure")

# Configuración de la IA
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el acceso al sistema."""
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if verificar_usuario(user, pw):
            session['user'] = user
            # Marcamos si es el admin principal
            session['isAdmin'] = (user == '1978')
            return redirect(url_for('dashboard'))
        return "Acceso denegado: Usuario o contraseña incorrectos", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    """Panel principal protegido."""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', is_admin=session.get('isAdmin'))

@app.route('/api/registrar', methods=['POST'])
def registrar():
    """Permite al admin 1978 crear nuevos usuarios."""
    if 'user' not in session or not session.get('isAdmin'):
        return jsonify({'error': 'No autorizado. Solo el administrador puede registrar usuarios.'}), 403
    
    data = request.json
    nuevo_user = data.get('username')
    nuevo_pass = data.get('password')
    
    if not nuevo_user or not nuevo_pass:
        return jsonify({'error': 'Faltan datos'}), 400
        
    exito, msg = registrar_nuevo_usuario(nuevo_user, nuevo_pass)
    if exito:
        return jsonify({'status': 'success', 'message': msg})
    return jsonify({'status': 'error', 'message': msg}), 400

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar_prompt():
    """Procesa los prompts de IA solo para usuarios logueados."""
    if 'user' not in session:
        return jsonify({'error': 'Sesión expirada'}), 401
    try:
        payload = request.json
        prompt_blindado = obtener_prompt_base(payload.get('modulo_id'), payload.get('datos', {}))
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt_blindado)
        return jsonify({'status': 'success', 'resultado_ia': response.text})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)
