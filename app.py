import os
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine
from modulos.auditoria import AuditoriaSystem
from modulos.usuarios import UsuarioManager
from modulos.bot_orquestador import PinpinelaOrchestrator

app = Flask(__name__)
# Llave de sesión blindada
app.secret_key = "admin_secret_1978_secure"

# INICIALIZACIÓN DE SILOS (Rutas simplificadas para Render)
try:
    logger = AuditoriaSystem()
    user_db = UsuarioManager()
    adn_db = ADNManager()
    ia_motor = AIEngine()
    bot_pinpinela = PinpinelaOrchestrator()
except Exception as e:
    print(f"FALLO CRÍTICO DE INICIO: {e}")

# --- MIDDLEWARE DE SEGURIDAD ---
@app.before_request
def verificar_acceso():
    # Permitir acceso libre a Login y archivos estáticos
    if request.endpoint in ['login', 'static'] or 'user' in session:
        return
    return redirect(url_for('login'))

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        if user == "admin" and pw == "admin_secret_1978_secure":
            session['user'] = user
            return redirect(url_for('index'))
        return "ERROR: Credenciales Inválidas", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index(): return render_template('workspace.html', active_page='workspace')

@app.route('/adn')
def adn(): return render_template('adn.html', active_page='adn')

@app.route('/bot')
def bot(): return render_template('bot_dashboard.html', active_page='bot')

@app.route('/usuarios')
def usuarios(): return render_template('usuarios.html', active_page='usuarios')

@app.route('/mantenimiento')
def mantenimiento(): return render_template('mantenimiento.html', active_page='mantenimiento')

@app.route('/configuracion')
def configuracion(): return render_template('configuracion.html', active_page='configuracion')

# --- API DE DATOS (PARA RELLENAR LOS APARTADOS) ---
@app.route('/api/get_adn')
def get_adn():
    return jsonify(adn_db.cargar_todo())

@app.route('/api/get_usuarios')
def get_usuarios():
    return jsonify(user_db.listar_usuarios())

@app.route('/api/get_logs')
def get_logs():
    return jsonify({'logs': logger.leer_ultimos()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
