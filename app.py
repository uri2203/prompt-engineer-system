import os
from flask import Flask, render_template, request, jsonify
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine
# Importación estricta de cada silo independiente
from modulos.mod_1_traductor import TraductorUniversal
from modulos.mod_2_guiones import IngenieriaGuiones

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978_secure")

# Instancias
adn_db = ADNManager()
ia_motor = AIEngine()
mod_1 = TraductorUniversal()
mod_2 = IngenieriaGuiones()

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
    # Enrutamiento hacia los silos físicos
    if mod_id == 'mod_1':
        prompt = mod_1.construir_prompt(d)
    elif mod_id == 'mod_2':
        prompt = mod_2.construir_prompt(d, adn_db.cargar_todo())
    else:
        return jsonify({'error': 'Este módulo aún no ha sido migrado a su propio silo.'}), 400

    # Ejecución aislada a través del motor
    resultado = ia_motor.ejecutar_failover(prompt)
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
