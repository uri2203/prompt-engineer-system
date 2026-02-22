import os
from flask import Flask, render_template, request, jsonify
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine

# Importación hermética de silos
from modulos.mod_1_traductor import TraductorUniversal
from modulos.mod_2_guiones import IngenieriaGuiones
from modulos.mod_3_hooks import GeneradorHooks
from modulos.mod_4_empaquetado import EmpaquetadoContenido
from modulos.mod_5_ventas import MotorVentasUGC

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978_secure")

adn_db = ADNManager()
ia_motor = AIEngine()
mod_1 = TraductorUniversal()
mod_2 = IngenieriaGuiones()
mod_3 = GeneradorHooks()
mod_4 = EmpaquetadoContenido()
mod_5 = MotorVentasUGC()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_adn')
def get_adn():
    return jsonify(adn_db.cargar_todo())

@app.route('/api/save_adn', methods=['POST'])
def save_adn():
    data = request.json
    return jsonify(adn_db.guardar(data['marca'], data['adn']))

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
