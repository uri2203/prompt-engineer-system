import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
# Importación estricta de los silos independientes
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine

app = Flask(__name__)
# Llave de seguridad para la sesión
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978_secure")

# Inicialización de los motores del sistema
adn_db = ADNManager()
ia_motor = AIEngine()

@app.route('/')
def index():
    # El sistema ahora busca automáticamente en la carpeta /templates/
    return render_template('index.html')

@app.route('/api/get_adn')
def get_adn():
    # Módulo 0: Carga de ADN desde JSON
    return jsonify(adn_db.cargar_todo())

@app.route('/api/save_adn', methods=['POST'])
def save_adn():
    # Módulo 0: Persistencia de ADN
    data = request.json
    return jsonify(adn_db.guardar(data['marca'], data['adn']))

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar():
    # Este es el puente central que conecta la interfaz con la IA
    data = request.json
    try:
        # Delegamos la ejecución al motor de IA blindado
        resultado = ia_motor.procesar(data, adn_db)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': f"Fallo en el puente de IA: {str(e)}"}), 500

# Gestión de salida segura
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # El servidor arranca en el puerto configurado por Render
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
