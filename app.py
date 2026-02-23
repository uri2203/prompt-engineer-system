import os
import time
from flask import Flask, render_template, request, jsonify, session
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine
from modulos.auditoria import AuditoriaSystem
from modulos.usuarios import UsuarioManager
from modulos.bot_orquestador import PinpinelaOrchestrator

app = Flask(__name__)
app.secret_key = "admin_secret_1978_secure"

# INICIALIZACIÓN PROTEGIDA
logger = AuditoriaSystem()
user_db = UsuarioManager()
adn_db = ADNManager()
ia_motor = AIEngine()
bot_pinpinela = PinpinelaOrchestrator()

# --- RUTAS DE NAVEGACIÓN ---
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

# --- API DE DATOS (EL PEGAMENTO) ---
# Estas rutas son las que llenan tus tablas. Si no están aquí, las tablas salen vacías.
@app.route('/api/get_usuarios')
def api_get_usuarios():
    return jsonify(user_db.listar_usuarios())

@app.route('/api/get_adn')
def api_get_adn():
    return jsonify(adn_db.cargar_todo())

@app.route('/api/get_logs')
def api_get_logs():
    return jsonify({'logs': logger.leer_ultimos()})

@app.route('/api/bot/lanzar_orden', methods=['POST'])
def bot_lanzar_orden():
    data = request.json
    tarea_id = f"ORD-{int(time.time())}"
    res = bot_pinpinela.procesar_orden(tarea_id, data.get('marca'), data.get('premisa'), data.get('formato', '16:9'))
    return jsonify(res)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
