import os
import json
import hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "secret_key_1978_secure")

# Configuración de IA
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

DB_PATH = 'usuarios_db.json'

def inicializar_db():
    if not os.path.exists(DB_PATH):
        admin_pw = hashlib.sha256("1978".encode()).hexdigest()
        with open(DB_PATH, 'w') as f:
            json.dump({"1978": admin_pw}, f)

def verificar_credenciales(u, p):
    inicializar_db()
    with open(DB_PATH, 'r') as f:
        db = json.load(f)
    return db.get(u) == hashlib.sha256(p.encode()).hexdigest()

# --- INTERFACES VISUALES RECONSTRUIDAS (DISEÑO CORPORATE TECH) ---

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Acceso | AI System</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-[#0f172a] h-screen flex items-center justify-center font-sans">
    <div class="bg-[#1e293b] p-10 rounded-2xl shadow-2xl border border-slate-700 w-96 text-center">
        <h2 class="text-blue-400 font-bold text-xl mb-2 tracking-widest">ADMIN LOGIN</h2>
        <p class="text-slate-500 text-[10px] mb-8 uppercase">Acceso Restringido - Nivel 1</p>
        <form action="/login" method="POST" class="space-y-4">
            <input type="text" name="username" placeholder="Usuario" required class="w-full p-4 rounded-xl bg-[#0f172a] border border-slate-800 text-white outline-none focus:border-blue-500 transition-all text-sm">
            <input type="password" name="password" placeholder="Contraseña" required class="w-full p-4 rounded-xl bg-[#0f172a] border border-slate-800 text-white outline-none focus:border-blue-500 transition-all text-sm">
            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-500/20 uppercase text-xs tracking-widest">Entrar al Sistema</button>
        </form>
    </div>
</body></html>
"""

HTML_INDEX = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Prompt System | Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0B1120; color: #f8fafc; font-family: 'Inter', sans-serif; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; backdrop-filter: blur(10px); }
        .active-tab { background-color: #2563eb; color: white; box-shadow: 0 4px 15px rgba(37,99,235,0.3); }
        .inactive-tab { color: #94a3b8; border: 1px solid transparent; }
        .inactive-tab:hover { background: #1e293b; color: white; }
    </style>
</head>
<body class="h-screen flex overflow-hidden">
    <aside class="w-80 glass-panel border-r border-slate-800 flex flex-col p-6 z-10">
        <div class="mb-10 flex justify-between items-center">
            <div>
                <h1 class="text-xl font-bold text-blue-400 tracking-tighter">AI PROMPT SYSTEM</h1>
                <p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Arquitectura Modular</p>
            </div>
            <a href="/logout" class="text-[9px] bg-red-900/20 text-red-500 border border-red-900/50 px-2 py-1 rounded hover:bg-red-900/40">SALIR</a>
        </div>
        
        <nav class="flex-1 space-y-2">
            <button onclick="switchTab('mod_1')" id="btn_mod_1" class="w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all active-tab">MOD 1: UNIVERSAL</button>
            <button onclick="switchTab('mod_2')" id="btn_mod_2" class="w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all inactive-tab uppercase">MOD 2: Guiones (Retención)</button>
            <button onclick="switchTab('mod_3')" id="btn_mod_3" class="w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all inactive-tab uppercase">MOD 3: Micro-Hooks</button>
            <button onclick="switchTab('mod_4')" id="btn_mod_4" class="w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all inactive-tab uppercase">MOD 4: Metadatos</button>
            <button onclick="switchTab('mod_5')" id="btn_mod_5" class="w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all inactive-tab uppercase">MOD 5: UGC & Ventas</button>
        </nav>

        {% if is_admin %}
        <div class="mt-auto p-4 bg-blue-900/10 border border-blue-900/30 rounded-2xl">
            <p class="text-[10px] text-blue-400 font-bold uppercase mb-3">Registrar Colaborador</p>
            <input type="text" id="new_u" placeholder="Usuario" class="w-full p-2 mb-2 rounded-lg bg-slate-950 text-[11px] border border-slate-800 outline-none focus:border-blue-500">
            <input type="password" id="new_p" placeholder="Password" class="w-full p-2 mb-3 rounded-lg bg-slate-950 text-[11px] border border-slate-800 outline-none focus:border-blue-500">
            <button onclick="registrar()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold py-2 rounded-lg transition-all">CREAR ACCESO</button>
        </div>
        {% endif %}
    </aside>

    <main class="flex-1 flex p-8 gap-8 overflow-hidden">
        <div class="w-1/2 flex flex-col gap-6 overflow-y-auto pr-4">
            <div id="form_container" class="space-y-6">
                <div id="ui_mod_1">
                    <h2 class="text-2xl font-bold mb-6">Traductor Universal</h2>
                    <div class="space-y-4">
                        <input type="text" id="m1_rol" placeholder="Rol del Experto (Ej: Editor Técnico)" class="w-full p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm">
                        <textarea id="m1_peticion" placeholder="¿Qué necesitas ejecutar?" class="w-full h-40 p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm resize-none"></textarea>
                    </div>
                </div>
            </div>
            <button onclick="ejecutar()" id="btn_main" class="w-full bg-blue-600 hover:bg-blue-500 py-5 rounded-2xl font-bold text-sm tracking-widest shadow-xl shadow-blue-900/20 transition-all">COMPILAR Y EJECUTAR</button>
        </div>

        <div class="w-1/2 flex flex-col glass-panel rounded-3xl p-8 shadow-2xl">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-[10px] font-black text-emerald-400 uppercase tracking-[0.2em]">Output Blindado (Lenguaje IA)</h3>
                <span id="status_tag" class="text-[9px] text-slate-500 font-mono">IDLE</span>
            </div>
            <textarea id="output" class="flex-1 w-full bg-[#0a0f18]/50 border border-slate-800/50 rounded-2xl p-6 text-emerald-300 font-mono text-xs leading-relaxed resize-none focus:outline-none" readonly placeholder="Esperando inyección lógica..."></textarea>
        </div>
    </main>

    <script>
        let moduloActivo = 'mod_1';
        function switchTab(id) {
            moduloActivo = id;
            document.querySelectorAll('nav button').forEach(b => b.classList.replace('active-tab', 'inactive-tab'));
            document.getElementById('btn_' + id).classList.replace('inactive-tab', 'active-tab');
        }

        async function ejecutar() {
            const btn = document.getElementById('btn_main');
            const out = document.getElementById('output');
            btn.innerHTML = "PROCESANDO..."; btn.disabled = true;
            
            const res = await fetch('/api/ejecutar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({modulo_id: moduloActivo, datos: {peticion: document.getElementById('m1_peticion')?.value}})
            });
            const data = await res.json();
            out.value = data.resultado_ia || data.error;
            btn.innerHTML = "COMPILAR Y EJECUTAR"; btn.disabled = false;
        }

        async function registrar() {
            const u = document.getElementById('new_u').value;
            const p = document.getElementById('new_p').value;
            const res = await fetch('/api/registrar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: u, password: p})
            });
            const data = await res.json();
            alert(data.message);
        }
    </script>
</body></html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if verificar_credenciales(u, p):
            session['user'] = u
            session['isAdmin'] = (u == '1978')
            return redirect(url_for('dashboard'))
        return "Error de acceso", 401
    return render_template_string(HTML_LOGIN)

@app.route('/')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(HTML_INDEX, is_admin=session.get('isAdmin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar_prompt():
    if 'user' not in session: return jsonify({'error': 'No auth'}), 401
    try:
        data = request.json
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"MODULO: {data.get('modulo_id')}. DATOS: {data.get('datos')}")
        return jsonify({'status': 'success', 'resultado_ia': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
