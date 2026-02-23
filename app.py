from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'pinpinela_secure_key_2026'  # Clave para cifrar la sesión

# CREDENCIALES ESTRICTAS DEFINIDAS
USER_DATA = {
    "admin": "admin1978"
}

# DECORADOR PARA PROTEGER RUTAS
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
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USER_DATA and USER_DATA[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash('Credenciales inválidas', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', active_page='workspace')

@app.route('/bot')
@login_required
def bot():
    return render_template('bot.html', active_page='bot')

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
    return render_template('mantenimiento.html', active_page='mantenimiento')

@app.route('/api/telemetria')
@login_required
def api_telemetria():
    # Mantiene vivo el panel de telemetría de su layout original
    return jsonify({
        "uptime": "2h 45m",
        "latencia": "0.08s",
        "tokens_totales": 24500,
        "api_status": "ONLINE",
        "historial_latencia": [0.08, 0.09, 0.07, 0.10, 0.08, 0.08],
        "historial_tokens": [150, 300, 450, 200, 600, 350]
    })

if __name__ == '__main__':
    app.run(debug=True)
