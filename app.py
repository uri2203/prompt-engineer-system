import os, json, hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978")
api_key = os.environ.get("GEMINI_API_KEY")
if api_key: genai.configure(api_key=api_key)

DB_PATH = 'usuarios_db.json'

def inicializar_db():
    if not os.path.exists(DB_PATH):
        admin_pw = hashlib.sha256("1978".encode()).hexdigest()
        with open(DB_PATH, 'w') as f: json.dump({"1978": admin_pw}, f)

def verificar_credenciales(u, p):
    inicializar_db()
    with open(DB_PATH, 'r') as f:
        db = json.load(f)
    return db.get(u) == hashlib.sha256(p.encode()).hexdigest()

# --- DISEÑO "CORPORATE TECH" ORIGINAL ---
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Acceso | AI System</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-[#0f172a] h-screen flex items-center justify-center font-sans">
    <div class="bg-[#1e293b] p-10 rounded-2xl shadow-2xl border border-slate-700 w-96 text-center">
        <h2 class="text-blue-400 font-bold text-xl mb-6 tracking-widest uppercase">Admin Login</h2>
        <form action="/login" method="POST" class="space-y-4">
            <input type="text" name="username" placeholder="Usuario" required class="w-full p-4 rounded-xl bg-[#0f172a] border border-slate-800 text-white outline-none focus:border-blue-500 transition-all text-sm uppercase">
            <input type="password" name="password" placeholder="Contraseña" required class="w-full p-4 rounded-xl bg-[#0f172a] border border-slate-800 text-white outline-none focus:border-blue-500 transition-all text-sm uppercase">
            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-500/20 uppercase text-xs">Entrar</button>
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
        .active-tab { background-color: #2563eb; color: white; border-color: #3b82f6; box-shadow: 0 4px 15px rgba(37,99,235,0.3); }
        .inactive-tab { color: #94a3b8; border: 1px solid transparent; }
        .inactive-tab:hover { background: #1e293b; color: white; }
    </style>
</head>
<body class="h-screen flex overflow-hidden">
    <aside class="w-80 glass-panel border-r border-slate-800 flex flex-col p-6 z-10">
        <div class="mb-10 flex justify-between items-center">
            <div><h1 class="text-xl font-bold text-blue-400">AI SYSTEM</h1><p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Corporate Tech</p></div>
            <a href="/logout" class="text-[9px] bg-red-900/20 text-red-500 border border-red-900/50 px-2 py-1 rounded">SALIR</a>
        </div>
        <nav class="flex-1 space-y-2">
            <button onclick="switchTab('mod_1')" id="btn_mod_1" class="w-full text-left px-5 py-3.5 rounded-xl text-xs font-bold transition-all active-tab uppercase tracking-wider">Mod 1: Universal</button>
            <button onclick="switchTab('mod_2')" id="btn_mod_2" class="w-full text-left px-5 py-3.5 rounded-xl text-xs font-bold transition-all inactive-tab uppercase tracking-wider">Mod 2: Guiones</button>
            <button onclick="switchTab('mod_5')" id="btn_mod_5" class="w-full text-left px-5 py-3.5 rounded-xl text-xs font-bold transition-all inactive-tab uppercase tracking-wider">Mod 5: Ventas</button>
        </nav>
        {% if is_admin %}<div class="mt-auto p-5 bg-blue-900/10 border border-blue-900/30 rounded-2xl">
            <p class="text-[10px] text-blue-400 font-bold uppercase mb-3 tracking-widest text-center">Registrar Acceso</p>
            <input type="text" id="new_u" placeholder="USUARIO" class="w-full p-2 mb-2 rounded bg-slate-950 text-[11px] border border-slate-800 text-white">
            <input type="password" id="new_p" placeholder="PASSWORD" class="w-full p-2 mb-3 rounded bg-slate-950 text-[11px] border border-slate-800 text-white">
            <button onclick="registrar()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold py-3 rounded-lg transition-all shadow-lg shadow-emerald-900/20">CREAR</button>
        </div>{% endif %}
    </aside>

    <main class="flex-1 flex p-8 gap-8 bg-[#0B1120] overflow-hidden">
        <div class="w-1/2 flex flex-col gap-6 overflow-y-auto pr-4">
            <h2 class="text-2xl font-bold mb-6 tracking-tight" id="mod_title">Traductor Universal</h2>
            <div class="space-y-4">
                <input type="text" id="p1" placeholder="Rol / Instrucción Técnica" class="w-full p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm focus:border-blue-500 outline-none">
                <textarea id="p2" placeholder="Cuerpo de la petición..." class="w-full h-44 p-4 rounded-xl bg-slate-900 border border-slate-800 text-sm resize-none focus:border-blue-500 outline-none"></textarea>
            </div>
            <button onclick="ejecutar()" id="btn_main" class="w-full bg-blue-600 hover:bg-blue-500 py-5 rounded-2xl font-black text-xs tracking-[0.2em] shadow-xl shadow-blue-900/20 transition-all uppercase">Compilar y Ejecutar</button>
        </div>
        <div class="w-1/2 flex flex-col glass-panel rounded-3xl p-8 relative">
            <h3 class="text-[10px] font-black text-emerald-400 uppercase tracking-[0.3em] mb-4">Output IA</h3>
            <textarea id="output" class="flex-1 w-full bg-transparent text-emerald-300 font-mono text-xs leading-relaxed resize-none outline-none scrollbar-hide" readonly placeholder="Esperando inyección lógica..."></textarea>
        </div>
    </main>

    <script>
        let moduloActivo = 'mod_1';
        function switchTab(id) {
            moduloActivo = id;
            document.querySelectorAll('nav button').forEach(b => b.classList.replace('active-tab', 'inactive-tab'));
            document.getElementById('btn_'+id).classList.replace('inactive-tab', 'active-tab');
            const t = {mod_1: 'Traductor Universal', mod_2: 'Ingeniería de Guiones', mod_5: 'Motor de Ventas'};
            document.getElementById('mod_title').innerText = t[id];
        }
        async function ejecutar() {
            const btn = document.getElementById('btn_main');
            const out = document.getElementById('output');
            btn.innerHTML = "PROCESANDO..."; btn.disabled = true;
            try {
                const res = await fetch('/api/ejecutar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({modulo_id: moduloActivo, datos: {p1: document.getElementById('p1').value, p2: document.getElementById('p2').value}})
                });
                const data = await res.json();
                out.value = data.resultado_ia || data.error;
            } catch (e) { out.value = "Error de red."; }
            finally { btn.innerHTML = "COMPILAR Y EJECUTAR"; btn.disabled = false; }
        }
        async function registrar() {
            const u = document.getElementById('new_u').value;
            const p = document.getElementById('new_p').value;
            const res = await fetch('/api/registrar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: u, password: p})
            });
            const d = await res.json(); alert(d.message);
        }
    </script>
</body></html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if verificar_credenciales(u, p):
            session['user'] = u; session['isAdmin'] = (u == '1978')
            return redirect(url_for('dashboard'))
        return "Acceso denegado", 401
    return render_template_string(HTML_LOGIN)

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
        response = model.generate_content(f"MODULO: {data.get('modulo_id')}. INSTRUCCIÓN: {data.get('datos')}")
        return jsonify({'status': 'success', 'resultado_ia': response.text})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/registrar', methods=['POST'])
def registrar():
    if not session.get('isAdmin'): return jsonify({'error': 'Denegado'}), 403
    d = request.json
    with open(DB_PATH, 'r') as f: db = json.load(f)
    db[d.get('username')] = hashlib.sha256(d.get('password').encode()).hexdigest()
    with open(DB_PATH, 'w') as f: json.dump(db, f)
    return jsonify({'status': 'success', 'message': 'Usuario registrado'})

if __name__ == '__main__':
    inicializar_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
