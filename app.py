import os
import time
from flask import Flask, render_template, request, jsonify

# Importación de Silos
try:
    from modulos.adn_manager import ADNManager
    from modulos.auditoria import AuditoriaSystem
    from modulos.usuarios import UsuarioManager
    from modulos.bot_orquestador import PinpinelaOrchestrator
except ImportError as e:
    print(f"ERROR DE IMPORTACIÓN: {e}")

app = Flask(__name__)
app.secret_key = "admin_secret_1978_secure"

# Inicialización de Motores
adn_db = ADNManager()
logger = AuditoriaSystem()
user_db = UsuarioManager()
bot_pinpinela = PinpinelaOrchestrator()

# --- RUTAS DE NAVEGACIÓN (Vínculos Directos) ---
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

# --- API DE DATOS (EL MOTOR DE LAS TABLAS) ---
@app.route('/api/get_usuarios')
def get_usuarios():
    # Retorna los datos directamente del silo de usuarios
    return jsonify(user_db.listar_usuarios())

@app.route('/api/get_adn')
def get_adn():
    # Retorna el ADN guardado en el sistema
    return jsonify(adn_db.cargar_todo())

@app.route('/api/get_logs')
def get_logs():
    # Retorna la bitácora de auditoría
    return jsonify({'logs': logger.leer_ultimos()})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
