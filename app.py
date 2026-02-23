import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from modulos.usuarios import UsuarioManager
from modulos.boveda import BovedaManager
from modulos.ai_engine import AIEngine

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin1978_master_key")

# Instancias de Bases de Datos Locales
user_db = UsuarioManager()
boveda_db = BovedaManager()
ai_engine = AIEngine() # El motor inicializado

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "message": "No autorizado"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pw = request.form.get('password', '').strip()
        usuarios = user_db.listar_usuarios()
        if user in usuarios and usuarios[user]['pass'] == pw:
            session.permanent = True
            session['user'] = user
            return redirect(url_for('index'))
        else:
            flash('ACCESO DENEGADO', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- RUTAS DE INTERFAZ ---
@app.route('/')
@login_required
def index(): return render_template('workspace.html', active_page='workspace')

@app.route('/usuarios')
@login_required
def usuarios(): return render_template('usuarios.html', active_page='usuarios')

@app.route('/configuracion')
@login_required
def configuracion(): return render_template('configuracion.html', active_page='configuracion')

@app.route('/mantenimiento')
@login_required
def mantenimiento(): return render_template('mantenimiento.html', active_page='logs')

@app.route('/bot')
@login_required
def bot(): return render_template('bot_dashboard.html', active_page='bot')

# --- APIS DEL SISTEMA ---
@app.route('/api/get_logs')
@login_required
def api_get_logs():
    return jsonify({"logs": ["[SISTEMA] Motor Pinpinela en Standby.", "[INFO] Enlace con Workspace establecido."] })

@app.route('/api/get_usuarios')
@login_required
def api_get_usuarios(): return jsonify(user_db.listar_usuarios())

@app.route('/api/telemetria')
@login_required
def api_telemetria():
    llaves_activas = len(boveda_db.obtener_llaves())
    return jsonify({
        "uptime": "Sincronizado", "latencia": "0.02s", "tokens_totales": 0,
        "api_status": f"TANQUES API: {llaves_activas}/5", 
        "historial_latencia": [0.02, 0.02, 0.02, 0.02, 0.02],
        "historial_tokens": [0, 0, 0, 0, 0]
    })

@app.route('/api/get_boveda')
@login_required
def api_get_boveda():
    return jsonify({"gemini_keys": boveda_db.obtener_llaves()})

@app.route('/api/save_boveda', methods=['POST'])
@login_required
def api_save_boveda():
    data = request.json
    llaves = data.get('gemini_keys', [])
    boveda_db.guardar_llaves(llaves)
    return jsonify({"status": "success", "message": "Bóveda actualizada"})

# --- API DEL MOTOR DE GUIONES (LA CONEXIÓN) ---
@app.route('/api/generate_script', methods=['POST'])
@login_required
def api_generate_script():
    data = request.json
    marca = data.get('marca', 'La Viuda')
    contexto = data.get('contexto', '')
    peticion = data.get('peticion', '')
    longitud = data.get('longitud', '4900 palabras') # Por defecto formato largo
    
    # Pasamos los datos al motor hermético
    resultado = ai_engine.generar_guion(marca, contexto, peticion, longitud)
    
    return jsonify({"status": "success", "data": resultado})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
