import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from modulos.config import obtener_prompt_base  # Importamos la lógica externa

app = Flask(__name__)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar_prompt():
    try:
        payload = request.json
        # Llamamos a la función del archivo externo
        prompt_blindado = obtener_prompt_base(payload.get('modulo_id'), payload.get('datos', {}))
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt_blindado)
        
        return jsonify({'status': 'success', 'resultado_ia': response.text})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
