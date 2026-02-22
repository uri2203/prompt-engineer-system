import os
import json
import hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978_secure")
api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

DB_PROYECTOS = 'proyectos_db.json'
DB_USUARIOS = 'usuarios_db.json'

def inicializar_dbs():
    if not os.path.exists(DB_USUARIOS):
        with open(DB_USUARIOS, 'w') as f:
            json.dump({"1978": hashlib.sha256("1978".encode()).hexdigest()}, f)
    
    if not os.path.exists(DB_PROYECTOS):
        adn_inicial = {
            "La Viuda": {"estilo": "Suspenso Inmersivo", "tono": "Realismo Clínico", "reglas": "Voz baja, confidencial, 4 fases, sin gore."},
            "Monkygraff": {"estilo": "Geopolítica", "tono": "Documental de Guerra", "reglas": "Alta densidad, ritmo rápido, cero saludos."},
            "TuIALista": {"estilo": "SaaS/IA", "tono": "Corporate Tech", "reglas": "Autoridad técnica, lenguaje de eficiencia."},
            "Ezzenshop": {"estilo": "Ecommerce", "tono": "Hype/Urbano", "reglas": "Alta energía, estética neón, Mobile First."},
            "Yayika Digital": {"estilo": "Infoproductos", "tono": "Marketing Emocional", "reglas": "Empatía, suavidad, elegancia."},
            "Yayika Apparel": {"estilo": "TikTok/Retail", "tono": "Sátira Viral", "reglas": "Humor ácido, parodias, alto impacto visual."}
        }
        with open(DB_PROYECTOS, 'w') as f:
            json.dump(adn_inicial, f)

def verificar_credenciales(u, p):
    inicializar_dbs()
    with open(DB_USUARIOS, 'r') as f:
        db = json.load(f)
    return db.get(u) == hashlib.sha256(p.encode()).hexdigest()

# --- INTERFAZ CORPORATE TECH ACTUALIZADA (MÓDULO 0 VISIBLE) ---

HTML_INDEX = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Prompt System | Control Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0B1120; color: #f8fafc; font-family: 'Inter', sans-serif; }
        .sidebar { background-color: #0F1523; border-right: 1px solid #1e293b; }
        .glass-panel { background-color: #0F1523; border: 1px solid #1e293b; border-radius: 12px; }
        .active-tab { border: 2px solid #3b82f6; color: #f8fafc; border-radius: 8px; }
        .inactive-tab { color: #94a3b8; border: 2px solid transparent; }
        input, select, textarea { background-color: #0B1120; border: 1px solid #334155; border-radius: 6px; color: #e2e8f0; outline: none; }
        .label-red { color: #f43f5e; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; }
        .label-blue { color: #60a5fa; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; }
    </style>
</head>
<body class="h-screen flex overflow-hidden">
    
    <aside class="w-[280px] sidebar flex flex-col p-5">
        <div class="mb-8">
            <h1 class="text-xl font-bold text-[#3b82f6]">AI Prompt System</h1>
            <p class="text-[9px] text-slate-500 font-bold uppercase mt-1">Gestión de ADN JSON</p>
        </div>
        
        <nav class="flex-1 space-y-2">
            <button onclick="switchTab('mod_0')" id="btn_mod_0" class="w-full text-left px-4 py-3 text-sm active-tab font-bold">Módulo 0: Centro de ADN</button>
            <button onclick="switchTab('mod_2')" id="btn_mod_2" class="w-full text-left px-4 py-3 text-sm inactive-tab">Módulo 2: Guiones</button>
            <button onclick="switchTab('mod_5')" id="btn_mod_5" class="w-full text-left px-4 py-3 text-sm inactive-tab">Módulo 5: Ventas UGC</button>
        </nav>
        <div class="mt-auto text-[11px] text-slate-400">DB Estado: <span class="text-[#10b981] font-bold">CONECTADO</span></div>
    </aside>

    <main class="flex-1 flex p-8 gap-6 bg-[#0B1120] overflow-hidden">
        <div class="w-[55%] flex flex-col gap-6 overflow-y-auto pr-2">
            
            <div id="ui_mod_0" class="module-content block">
                <h2 class="text-2xl font-bold mb-2 text-white">Centro de Control de ADN</h2>
                <p class="text-xs text-slate-400 mb-6">Modifica las reglas inquebrantables de tus marcas en la base de datos.</p>
                
                <div class="space-y-4">
                    <div>
                        <label class="label-red block mb-1.5">SELECCIONAR PROYECTO PARA EDITAR</label>
                        <select id="m0_selector" onchange="cargarADN()" class="w-full p-2.5 text-sm">
                            <option value="La Viuda">La Viuda</option>
                            <option value="Monkygraff">Monkygraff</option>
                            <option value="TuIALista">TuIALista</option>
                            <option value="Ezzenshop">Ezzenshop</option>
                            <option value="Yayika Digital">Yayika Digital</option>
                            <option value="Yayika Apparel">Yayika Apparel</option>
                        </select>
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">ESTILO VISUAL</label>
                        <input type="text" id="m0_estilo" class="w-full p-2.5 text-sm">
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">TONO DE VOZ</label>
                        <input type="text" id="m0_tono" class="w-full p-2.5 text-sm">
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">REGLAS INQUEBRANTABLES (EL "SÉ Y NO SÉ")</label>
                        <textarea id="m0_reglas" class="w-full h-32 p-2.5 text-sm resize-none"></textarea>
                    </div>
                    <button onclick="guardarADN()" class="w-full bg-[#10b981] hover:bg-emerald-500 py-3 rounded-lg font-bold text-xs transition-all">ACTUALIZAR ADN EN BASE DE DATOS</button>
                </div>
            </div>

            <div id="ui_mod_2" class="module-content hidden">
                <h2 class="text-2xl font-bold mb-6 text-white">Motor de Guiones</h2>
                <div class="space-y-4">
                    <label class="label-blue block mb-1.5">TEMA A DESARROLLAR</label>
                    <textarea id="m2_tema" class="w-full h-32 p-2.5 text-sm"></textarea>
                    <button onclick="ejecutar()" class="w-full bg-[#2563eb] py-3 rounded-lg font-bold text-xs">GENERAR GUION CON ADN ACTUAL</button>
                </div>
            </div>
        </div>

        <div class="w-[45%] flex flex-col glass-panel p-6 shadow-2xl">
            <h3 class="text-[#10b981] font-bold text-[11px] uppercase mb-4 tracking-widest">Consola de Salida</h3>
            <textarea id="output" class="flex-1 w-full bg-transparent text-slate-300 font-mono text-sm leading-relaxed resize-none outline-none" readonly></textarea>
        </div>
    </main>

    <script>
        let adnGlobal = {};

        async function cargarADN() {
            const res = await fetch('/api/get_adn');
            adnGlobal = await res.json();
            const marca = document.getElementById('m0_selector').value;
            const data = adnGlobal[marca];
            document.getElementById('m0_estilo').value = data.estilo;
            document.getElementById('m0_tono').value = data.tono;
            document.getElementById('m0_reglas').value = data.reglas;
        }

        async function guardarADN() {
            const marca = document.getElementById('m0_selector').value;
            const nuevoADN = {
                estilo: document.getElementById('m0_estilo').value,
                tono: document.getElementById('m0_tono').value,
                reglas: document.getElementById('m0_reglas').value
            };
            const res = await fetch('/api/save_adn', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({marca: marca, adn: nuevoADN})
            });
            const resp = await res.json();
            alert(resp.status === 'success' ? 'ADN Actualizado Correctamente' : 'Error al guardar');
        }

        function switchTab(id) {
            document.querySelectorAll('.module-content').forEach(el => el.classList.add('hidden'));
            document.getElementById('ui_' + id).classList.remove('hidden');
            document.querySelectorAll('nav button').forEach(b => b.classList.replace('active-tab', 'inactive-tab'));
            document.getElementById('btn_' + id).classList.replace('inactive-tab', 'active-tab');
        }

        window.onload = cargarADN;
    </script>
</body></html>
"""

@app.route('/')
def index():
    if 'user' not in session: return render_template_string(HTML_INDEX) # Para pruebas directas
    return render_template_string(HTML_INDEX)

@app.route('/api/get_adn')
def get_adn():
    with open(DB_PROYECTOS, 'r') as f: return jsonify(json.load(f))

@app.route('/api/save_adn', methods=['POST'])
def save_adn():
    data = request.json
    marca, adn = data.get('marca'), data.get('adn')
    with open(DB_PROYECTOS, 'r') as f: db = json.load(f)
    db[marca] = adn
    with open(DB_PROYECTOS, 'w') as f: json.dump(db, f)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    inicializar_dbs()
    app.run(host='0.0.0.0', port=5000)
