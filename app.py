import os, json, hashlib
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import google.generativeai as genai
from modulos.config import obtener_prompt_ingenieria # Recuperamos la modularidad

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_1978")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if u == "1978" and p == "1978": # Acceso Maestro
            session['user'] = u
            return redirect(url_for('dashboard'))
        return "Acceso Denegado", 401
    return render_template('login.html')

@app.route('/')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar():
    if 'user' not in session: return jsonify({'error': 'No auth'}), 401
    data = request.json
    # La inteligencia vive en el módulo, no aquí
    prompt_final = obtener_prompt_ingenieria(data.get('modulo_id'), data.get('datos'))
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt_final)
    return jsonify({'resultado_ia': response.text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
