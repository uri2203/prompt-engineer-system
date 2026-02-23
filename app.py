import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from modulos.usuarios import UsuarioManager

app = Flask(__name__)
app.secret_key = 'admin_secret_1978_secure' 

# Instancia del gestor de usuarios persistente
user_db = UsuarioManager()

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
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pw = request.form.get('password', '').strip()
        
        usuarios = user_db.listar_usuarios()
        
        # Validación contra la base de datos persistente
        if user in usuarios and usuarios[user]['pass'] == pw:
            session['user'] = user
            return redirect(url_for('index'))
        else:
            flash('Credenciales Incorrectas', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- RUTAS DE INTERFAZ (Mantiene su diseño original) ---
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

# --- APIS DE DATOS ---
@app.route('/api/get_usuarios')
@login_required
def api_get_usuarios():
    return jsonify(user_db.listar_usuarios())

@app.route('/api/crear_usuario', methods=['POST'])
@login_required
def api_crear_usuario():
    data = request.json
    user_db.agregar_usuario(data['user'], data['pass'], data['nombre'], data['rol'])
    return jsonify({"status": "success"})

@app.route('/api/telemetria')
@login_required
def api_telemetria():
    return jsonify({
        "uptime": "5m 12s",
        "latencia": "0.04s",
        "tokens_totales": 0,
        "api_status": "STABLE",
        "historial_latencia": [0.04, 0.05, 0.04, 0.06, 0.04],
        "historial_tokens": [0, 0, 0, 0, 0]
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
