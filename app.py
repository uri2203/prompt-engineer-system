import os
import time
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "admin_secret_1978_secure"

# INICIALIZACIÓN CON CAPA DE PROTECCIÓN
try:
    from modulos.adn_manager import ADNManager
    from modulos.auditoria import AuditoriaSystem
    from modulos.usuarios import UsuarioManager
    from modulos.bot_orquestador import PinpinelaOrchestrator
    
    logger = AuditoriaSystem()
    user_db = UsuarioManager()
    adn_db = ADNManager()
    bot_pinpinela = PinpinelaOrchestrator()
except Exception as e:
    print(f"CRITICAL STARTUP ERROR: {e}")
    # Creamos objetos vacíos para que no rompa las rutas
    logger = None
    user_db = None

# --- RUTAS DE NAVEGACIÓN ---
@app.route('/')
def index(): return render_template('workspace.html', active_page='workspace')

@app.route('/usuarios')
def usuarios(): return render_template('usuarios.html', active_page='usuarios')

@app.route('/mantenimiento')
def mantenimiento(): return render_template('mantenimiento.html', active_page='mantenimiento')

# --- API DE DATOS (EL MOTOR DE TUS TABLAS) ---
@app.route('/api/get_usuarios')
def api_get_usuarios():
    try:
        if user_db:
            return jsonify(user_db.listar_usuarios())
        return jsonify({"admin": {"rol": "Master", "status": "Error de Carga"}})
    except:
        return jsonify({})

@app.route('/api/get_logs')
def api_get_logs():
    if logger:
        return jsonify({'logs': logger.leer_ultimos()})
    return jsonify({'logs': ["Error: Sistema de logs no disponible"]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
