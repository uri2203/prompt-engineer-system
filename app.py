import os
import time
from flask import Flask, render_template, request, jsonify
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine

# Silos Herméticos Intactos
from modulos.mod_1_traductor import TraductorUniversal
from modulos.mod_2_guiones import IngenieriaGuiones
from modulos.mod_3_hooks import GeneradorHooks
from modulos.mod_4_empaquetado import EmpaquetadoContenido
from modulos.mod_5_ventas import MotorVentasUGC

# Sistema Nervioso del Bot
from modulos.bot_orquestador import PinpinelaOrchestrator

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978_secure")

server_start_time = time.time()

# Instanciación del Clúster de Producción
adn_db = ADNManager()
ia_motor = AIEngine()
mod_1 = TraductorUniversal()
mod_2 = IngenieriaGuiones()
mod_3 = GeneradorHooks()
mod_4 = EmpaquetadoContenido()
mod_5 = MotorVentasUGC()

# Instanciación del Orquestador Autónomo
bot_pinpinela = PinpinelaOrchestrator()

# --- RUTAS DE NAVEGACIÓN MODULAR ---

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

@app.route('/configuracion')
def configuracion():
    return render_template('configuracion.html', active_page='configuracion')

@app.route('/mantenimiento')
def mantenimiento():
    return render_template('mantenimiento.html', active_page='mantenimiento')

# --- RUTAS DE DATOS Y API ---

@app.route('/api/get_adn')
def get_adn():
    return jsonify(adn_db.cargar_todo())

@app.route('/api/save_adn', methods=['POST'])
def save_adn():
    data = request.json
    return jsonify(adn_db.guardar(data['marca'], data['adn']))

@app.route('/api/telemetria')
def telemetria():
    uptime_segundos = int(time.time() - server_start_time)
    minutos, segundos = divmod(uptime_segundos, 60)
    horas, minutos = divmod(minutos, 60)
    uptime_str = f"{horas}h {minutos}m {segundos}s" if horas > 0 else f"{minutos}m {segundos}s"
    
    datos_motor = ia_motor.obtener_telemetria()
    
    return jsonify({
        'uptime': uptime_str,
        'system_status': 'ACTIVE',
        'api_status': datos_motor['estado_api'],
        'latencia': f"{datos_motor['latencia_actual']}s",
        'tokens_totales': datos_motor['tokens_totales'],
        'historial_latencia': datos_motor['historial_latencia'],
        'historial_tokens': datos_motor['historial_tokens']
    })

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar():
    data = request.json
    mod_id = data.get('modulo_id')
    d = data.get('datos', {})
    
    prompt = ""
    if mod_id == 'mod_1':
        prompt = mod_1.construir_prompt(d)
    elif mod_id == 'mod_2':
        prompt = mod_2.construir_prompt(d, adn_db.cargar_todo())
    elif mod_id == 'mod_3':
        prompt = mod_3.construir_prompt(d, adn_db.cargar_todo())
    elif mod_id == 'mod_4':
        prompt = mod_4.construir_prompt(d, adn_db.cargar_todo())
    elif mod_id == 'mod_5':
        prompt = mod_5.construir_prompt(d)
    else:
        return jsonify({'error': 'Módulo no detectado.'}), 400

    resultado = ia_motor.ejecutar_failover(prompt)
    return jsonify(resultado)

# --- RUTAS DEL ORQUESTADOR PINPINELA ---

@app.route('/api/bot/lanzar_orden', methods=['POST'])
def bot_lanzar_orden():
    data = request.json
    tarea_id = f"ORD-{int(time.time())}"
    marca = data.get('marca', 'La Viuda')
    premisa = data.get('premisa', 'Prueba de estrés de sistema autónomo. Operativa de inmersión confirmada.')
    
    # El Orquestador toma el control total del servidor
    resultado = bot_pinpinela.procesar_orden(tarea_id, marca, premisa)
    
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
