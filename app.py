import os
import time
from flask import Flask, render_template, request, jsonify

# Importación de Silos
try:
    from modulos.adn_manager import ADNManager
    from modulos.ai_engine import AIEngine
    from modulos.auditoria import AuditoriaSystem
    from modulos.usuarios import UsuarioManager
    from modulos.bot_orquestador import PinpinelaOrchestrator
except Exception as e:
    print(f"ALERTA: Algunos módulos no cargaron: {e}")

app = Flask(__name__)
app.secret_key = "admin_secret_1978_secure"

# Inicialización de Motores
adn_db = ADNManager()
logger = AuditoriaSystem()
user_db = UsuarioManager()
bot_pinpinela = PinpinelaOrchestrator()

# --- RUTAS DE NAVEGACIÓN (EL MAPA DEL MENÚ) ---
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

# --- API DE DATOS (PARA RELLENAR LAS TABLAS) ---
@app.route('/api/get_usuarios')
def get_usuarios():
    return jsonify(user_db.listar_usuarios())

@app.route('/api/get_adn')
def get_adn():
    return jsonify(adn_db.cargar_todo())

@app.route('/api/get_logs')
def get_logs():
    return jsonify({'logs': logger.leer_ultimos()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
