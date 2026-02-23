import os
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine
from modulos.auditoria import AuditoriaSystem
from modulos.usuarios import UsuarioManager
from modulos.bot_orquestador import PinpinelaOrchestrator

app = Flask(__name__)
# Llave maestra para las sesiones
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978_secure")

# Instanciación de Silos
logger = AuditoriaSystem()
user_db = UsuarioManager()
adn_db = ADNManager()
ia_motor = AIEngine()
bot_pinpinela = PinpinelaOrchestrator()

# --- PROTECCIÓN DE RUTAS (Middleware) ---
@app.before_request
def verificar_acceso():
    # Rutas permitidas sin login
    rutas_publicas = ['login', 'static']
    if 'user' not in session and request.endpoint not in rutas_publicas:
        return redirect(url_for('login'))

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        # Credenciales de emergencia
        if user == "admin" and pw == "admin_secret_1978_secure":
            session['user'] = user
            logger.registrar("SEGURIDAD", f"Usuario {user} inició sesión.", "SUCCESS")
            return redirect(url_for('index'))
        return "Acceso Denegado", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index(): 
    return render_template('workspace.html', active_page='workspace')

@app.route('/mantenimiento')
def mantenimiento(): 
    return render_template('mantenimiento.html', active_page='mantenimiento')

@app.route('/configuracion')
def configuracion(): 
    return render_template('configuracion.html', active_page='configuracion')

@app.route('/bot')
def bot(): 
    return render_template('bot_dashboard.html', active_page='bot')

# --- API DE DATOS (Para que los apartados NO estén vacíos) ---
@app.route('/api/get_logs')
def get_logs():
    return jsonify({'logs': logger.leer_ultimos()})

@app.route('/api/get_adn')
def get_adn():
    return jsonify(adn_db.cargar_todo())

@app.route('/api/get_usuarios')
def get_usuarios():
    return jsonify(user_db.listar_usuarios())

@app.route('/api/bot/lanzar_orden', methods=['POST'])
def bot_lanzar_orden():
    data = request.json
    tarea_id = f"ORD-{int(time.time())}"
    marca = data.get('marca', 'La Viuda')
    formato = data.get('formato', '16:9')
    logger.registrar("ORQUESTADOR", f"Ejecutando orden {tarea_id} para {marca} ({formato})", "INFO")
    resultado = bot_pinpinela.procesar_orden(tarea_id, marca, data.get('premisa', ''), formato)
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
