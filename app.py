import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978_secure")

# Inicialización de Silos
adn_db = ADNManager()
ia_motor = AIEngine()

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
    try:
        # El sistema delega la responsabilidad al motor de IA profesional
        resultado = ia_motor.procesar(data, adn_db)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': f"Error en el Silo: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
