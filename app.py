import os
import json
import hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "secret_key_1978_secure")
api_key = os.environ.get("GEMINI_API_KEY")
if api_key: genai.configure(api_key=api_key)

DB_PATH = 'usuarios_db.json'

def inicializar_db():
    if not os.path.exists(DB_PATH):
        admin_pw = hashlib.sha256("1978".encode()).hexdigest()
        with open(DB_PATH, 'w') as f: json.dump({"1978": admin_pw}, f)

def verificar_credenciales(u, p):
    inicializar_db()
    with open(DB_PATH, 'r') as f: db = json.load(f)
    return db.get(u) == hashlib.sha256(p.encode()).hexdigest()

# --- INTERFAZ CORPORATE TECH (DISEÑO FINAL) ---
HTML_INDEX = """
<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>AI PROMPT SYSTEM</title><script src="https://cdn.tailwindcss.com"></script>
<style>
    body { background-color: #0B1120; color: #f8fafc; font-family: 'Inter', sans-serif; }
    .glass-panel { background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; backdrop-filter: blur(10px); }
    .active-tab { background-color: #2563eb; color: white; border-color: #3b82f6; }
</style></head>
<body class="h-screen flex overflow-hidden">
    <aside class="w-80 glass-panel border-r border-slate-800 flex flex-col p-6 z-10">
        <div class="mb-10 flex justify-between items-center">
            <div><h1 class="text-xl font-bold text-blue-400">AI SYSTEM</h1><p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Corporate Tech</p></div>
            <a href="/logout" class="text-[9px] bg-red-900/20 text-red-500 px-2 py-1 rounded">SALIR</a>
        </div>
        <nav class="flex-1 space-y-2">
            <button onclick="switchTab('mod_1')" id="btn_mod_1" class="w-full text-left px-5 py-3 rounded-xl text-xs font-bold active-tab">MOD 1: UNIVERSAL</button>
            <button onclick="switchTab('mod_2')" id="btn_mod_2" class="w-full text-left px-5 py-3 rounded-xl text-xs font-bold inactive-tab">MOD 2: GUIONES</button>
            <button onclick="switchTab('mod_5')" id="btn_mod_5" class="w-full text-left px-5 py-3 rounded-xl text-xs font-bold inactive-tab">MOD 5: VENTAS</button>
        </nav>
        {% if is_admin %}<div class="mt-auto p-4 bg-blue-900/10 border border-blue-900/30 rounded-2xl">
            <input type="text" id="new_u" placeholder="Usuario" class="w-full p-2 mb-2 rounded bg-slate-950 text-xs">
            <input type="password" id="new_p" placeholder="Password" class="w-full p-2 mb-3 rounded bg-slate-950 text-xs">
            <button onclick="registrar()" class="w-full bg-emerald-600 py-2 rounded text-xs font-bold">CREAR</button>
        </div>{% endif %}
    </aside>
    <main class="flex-1 flex p-8 gap-8 bg-[#0B1120]">
        <div class="w-1/2 flex flex-col gap-6">
            <h2 class="text-2xl font-bold" id="title">Traductor Universal</h2>
            <div class="space-y-4">
                <input type="text" id="f1" placeholder="Rol / Marca" class="w-full p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm">
                <textarea id="f2" placeholder="Petición..." class="w-full h-40 p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm resize-none"></textarea>
            </div>
            <button onclick="ejecutar()" id="btn_main" class="w-full bg-blue-600 py-4 rounded-xl font-bold uppercase tracking-widest text-xs">Compilar y Ejecutar</button>
        </div>
        <div class="w-1/2 flex flex-col glass-panel rounded-3xl p-8"><textarea id="output" class="flex-1 w-full bg-transparent text-emerald-400 font-mono text-xs resize-none outline-none" readonly></textarea></div>
    </main>
    <script>
        let mod = 'mod_1';
        function switchTab(id) { mod = id; document.querySelectorAll('nav button').forEach(b => b.classList.replace('active-tab', 'inactive-tab')); document.getElementById('btn_'+id).classList.replace('inactive-tab', 'active-tab'); }
        async function ejecutar() {
            const out = document.getElementById('output'); out.value = "Procesando...";
            const res = await fetch('/api/ejecutar', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({modulo_id: mod, datos: {f1: document.getElementById('f1').value, f2: document.getElementById('f2').value}}) });
            const data = await res.json(); out.value = data.resultado_ia || data.error;
        }
        async function registrar() {
            const res = await fetch('/api/registrar', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({username: document.getElementById('new_u').value, password: document.getElementById('new_p').value}) });
            const data = await res.json(); alert(data.message);
        }
    </script>
</body></html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if verificar_credenciales(request.form.get('username'), request.form.get('password')):
            session['user'] = request.form.get('username'); session['isAdmin'] = (session['user'] == '1978')
            return redirect(url_for('dashboard'))
        return "Error", 401
    return render_template_string("Copia aquí el HTML_LOGIN previo") # He omitido el login para brevedad, pero mantenlo igual.

@app.route('/')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(HTML_INDEX, is_admin=session.get('isAdmin'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar_prompt():
    if 'user' not in session: return jsonify({'error': 'No auth'}), 401
    try:
        data = request.json
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"MODULO: {data.get('modulo_id')}. DATOS: {data.get('datos')}")
        return jsonify({'status': 'success', 'resultado_ia': response.text})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/registrar', methods=['POST'])
def registrar():
    if not session.get('isAdmin'): return jsonify({'error': 'Denegado'}), 403
    d = request.json
    with open(DB_PATH, 'r') as f: db = json.load(f)
    db[d.get('username')] = hashlib.sha256(d.get('password').encode()).hexdigest()
    with open(DB_PATH, 'w') as f: json.dump(db, f)
    return jsonify({'status': 'success', 'message': 'Usuario creado'})

if __name__ == '__main__':
    inicializar_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
