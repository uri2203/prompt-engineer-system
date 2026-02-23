import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps

app = Flask(__name__)
# Usamos una clave fija para evitar que la sesión expire al reiniciar Render
app.secret_key = 'pinpinela_master_vault_2026' 

# CREDENCIALES ESTRICTAS DEFINIDAS POR EL USUARIO
MASTER_USER = "admin"
MASTER_PASS = "admin1978"

# DECORADOR DE PROTECCIÓN DE RUTAS
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Aplicamos .strip() para eliminar espacios accidentales al copiar/pegar
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # BYPASS DE SEGURIDAD: Validación directa contra variables maestras
        if username == MASTER_USER and password == MASTER_PASS:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash('ACCESO DENEGADO: Verifique credenciales de Nivel 1', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# --- RUTAS PROTEGIDAS (NO TOCAN EL DISEÑO ORIGINAL) ---

@app.route('/')
@login_required
def index():
    return render_template('workspace.html', active_page='workspace')

@app.route('/bot')
@login_required
def bot():
    return render_template('bot_dashboard.html', active_page='bot')

@app.route('/adn')
@login_required
def adn():
    return render_template('adn.html', active_page='adn')

@app.route('/usuarios')
@login_required
def usuarios():
    return render_template('usuarios.html', active_page='usuarios')

@app.route('/configuracion')
@login_required
def configuracion():
    return render_template('configuracion.html', active_page='configuracion')

@app.route('/mantenimiento')
@login_required
def mantenimiento():
    return render_template('mantenimiento.html', active_page='logs')

@app.route('/api/telemetria')
@login_required
def api_telemetria():
    # Mantiene vivo el panel de telemetría de su layout original
    return jsonify({
        "uptime": "3h 12m",
        "latencia": "0.05s",
        "tokens_totales": 32800,
        "api_status": "ONLINE",
        "historial_latencia": [0.05, 0.06, 0.05, 0.07, 0.05, 0.05],
        "historial_tokens": [200, 450, 300, 500, 400, 650]
    })

if __name__ == '__main__':
    # Configuración para Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
