import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from modules.adn_manager import ADNManager
from modules.ai_engine import AIEngine

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978")

# Instanciamos los silos como objetos independientes
adn_db = ADNManager()
ia = AIEngine()

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
    # El app.py delega la responsabilidad al motor de IA
    return jsonify(ia.procesar(data, adn_db))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
