import os
import time
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine
from modulos.auditoria import AuditoriaSystem
from modulos.usuarios import UsuarioManager
from modulos.bot_orquestador import PinpinelaOrchestrator
from modulos.config_manager import ConfigManager

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978_secure")

# Instanciación de Silos de Ingeniería
logger = AuditoriaSystem()
user_db = UsuarioManager()
adn_db = ADNManager()
config_db = ConfigManager()
ia_motor = AIEngine()
bot_pinpinela = PinpinelaOrchestrator()

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/')
def index(): 
    return render_template('workspace.html', active_page='workspace')

@app.route('/adn')
def adn(): 
    return render_template('adn.html', active_page='adn')

@app.route('/bot')
def bot(): 
    return render_template('bot_dashboard.html', active_page='bot')

@app.route('/usuarios')
def usuarios(): 
    return render_template('usuarios.html', active_page='usuarios')

@app.route('/mantenimiento')
def mantenimiento(): 
    return render_template('mantenimiento.html', active_page='mantenimiento')

@app.route('/configuracion')
def configuracion(): 
    return render_template('configuracion.html', active_page='configuracion')

# --- API DE DATOS (ESTRUCTURA DE CONTROL) ---
@app.route('/api/get_usuarios')
def api_get_usuarios():
    return jsonify(user_db.listar_usuarios())

@app.route('/api/crear_usuario', methods=['POST'])
def api_crear_usuario():
    try:
        data = request.json
        user_db.agregar_usuario(data['username'], data['rol'])
        logger.registrar("SEGURIDAD", f"Nuevo usuario creado: {data['username']}", "SUCCESS")
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

@app.route('/api/get_adn')
def api_get_adn():
    return jsonify(adn_db.cargar_todo())

@app.route('/api/get_logs')
def api_get_logs():
    return jsonify({'logs': logger.leer_ultimos()})

# Rutas de la Bóveda de Configuración
@app.route('/api/get_config')
def api_get_config():
    return jsonify(config_db.leer_configuracion())

@app.route('/api/save_config', methods=['POST'])
def api_save_config():
    try:
        data = request.json
        config_db.guardar_configuracion(data)
        logger.registrar("BÓVEDA", "Actualización manual de Matriz de API Keys", "SUCCESS")
        return jsonify({"status": "success"})
    except Exception as e:
        logger.registrar("BÓVEDA", f"Fallo al guardar matriz: {e}", "ERROR")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
