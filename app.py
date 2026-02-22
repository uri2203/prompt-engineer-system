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
            "La Viuda": {"estilo": "Suspenso Inmersivo", "tono": "Realismo Clínico", "reglas": "Voz baja, confidencial, 4 fases, sin gore. Romper cuarta pared."},
            "Monkygraff": {"estilo": "Geopolítica", "tono": "Documental de Guerra", "reglas": "Alta densidad, ritmo rápido, cero saludos ni relleno."},
            "TuIALista": {"estilo": "SaaS/IA", "tono": "Corporate Tech", "reglas": "Autoridad técnica, lenguaje de eficiencia y software."},
            "Ezzenshop": {"estilo": "Ecommerce", "tono": "Hype/Urbano", "reglas": "Alta energía, estética neón, Mobile First."},
            "Yayika Digital": {"estilo": "Infoproductos", "tono": "Marketing Emocional", "reglas": "Empatía, suavidad, elegancia persuasiva."},
            "Yayika Apparel": {"estilo": "TikTok/Retail", "tono": "Sátira Viral", "reglas": "Humor ácido, parodias, alto impacto visual."}
        }
        with open(DB_PROYECTOS, 'w') as f:
            json.dump(adn_inicial, f)

def verificar_credenciales(u, p):
    inicializar_dbs()
    with open(DB_USUARIOS, 'r') as f:
        db = json.load(f)
    return db.get(u) == hashlib.sha256(p.encode()).hexdigest()

# --- INTERFAZ CORPORATE TECH COMPLETA (TODOS LOS MÓDULOS RESTAURADOS) ---

HTML_INDEX = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Prompt System | Master Control</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0B1120; color: #f8fafc; font-family: 'Inter', sans-serif; }
        .sidebar { background-color: #0F1523; border-right: 1px solid #1e293b; }
        .glass-panel { background-color: #0F1523; border: 1px solid #1e293b; border-radius: 12px; }
        .active-tab { border: 2px solid #3b82f6; color: #f8fafc; border-radius: 8px; background: rgba(59,130,246,0.1); }
        .inactive-tab { color: #94a3b8; border: 2px solid transparent; }
        input, select, textarea { background-color: #0B1120; border: 1px solid #334155; border-radius: 6px; color: #e2e8f0; outline: none; transition: border 0.2s; }
        input:focus, select:focus, textarea:focus { border-color: #3b82f6; }
        .label-red { color: #f43f5e; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
        .label-blue { color: #60a5fa; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
        .label-green { color: #34d399; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
    </style>
</head>
<body class="h-screen flex overflow-hidden">
    
    <aside class="w-[280px] sidebar flex flex-col p-5 z-10">
        <div class="mb-8">
            <h1 class="text-xl font-bold text-[#3b82f6] tracking-tight">AI Prompt System</h1>
            <p class="text-[9px] text-slate-500 font-bold uppercase mt-1">Arquitectura de Marcas</p>
        </div>
        
        <nav class="flex-1 space-y-2">
            <button onclick="switchTab('mod_0')" id="btn_mod_0" class="w-full text-left px-4 py-3 text-sm active-tab font-medium">Módulo 0: Centro de ADN</button>
            <button onclick="switchTab('mod_2')" id="btn_mod_2" class="w-full text-left px-4 py-3 text-sm inactive-tab">Módulo 2: Guiones</button>
            <button onclick="switchTab('mod_3')" id="btn_mod_3" class="w-full text-left px-4 py-3 text-sm inactive-tab">Módulo 3: Micro-Hooks</button>
            <button onclick="switchTab('mod_5')" id="btn_mod_5" class="w-full text-left px-4 py-3 text-sm inactive-tab">Módulo 5: Ventas UGC</button>
        </nav>
        <div class="mt-auto pt-4 border-t border-slate-800/50 flex justify-between items-center">
            <p class="text-[10px] text-slate-400">DB: <span class="text-[#10b981] font-bold">JSON ACTIVE</span></p>
            <a href="/logout" class="text-[10px] text-slate-500 hover:text-red-400">Cerrar Sesión</a>
        </div>
    </aside>

    <main class="flex-1 flex p-8 gap-6 bg-[#0B1120] overflow-hidden">
        <div class="w-[55%] flex flex-col gap-6 overflow-y-auto pr-2 scrollbar-hide">
            
            <div id="ui_mod_0" class="module-content block">
                <h2 class="text-2xl font-bold mb-2 text-white tracking-tight">Centro de ADN de Marca</h2>
                <p class="text-xs text-slate-400 mb-6">Configura las reglas inquebrantables que la IA debe obedecer.</p>
                <div class="space-y-4">
                    <div>
                        <label class="label-red block mb-1.5">MARCA A CONFIGURAR</label>
                        <select id="m0_selector" onchange="cargarADN()" class="w-full p-2.5 text-sm">
                            <option value="La Viuda">La Viuda</option>
                            <option value="Monkygraff">Monkygraff</option>
                            <option value="TuIALista">TuIALista</option>
                            <option value="Ezzenshop">Ezzenshop</option>
                            <option value="Yayika Digital">Yayika Digital</option>
                            <option value="Yayika Apparel">Yayika Apparel</option>
                        </select>
                    </div>
                    <div><label class="label-blue block mb-1.5">ESTILO VISUAL</label><input type="text" id="m0_estilo" class="w-full p-2.5 text-sm"></div>
                    <div><label class="label-blue block mb-1.5">TONO DE VOZ</label><input type="text" id="m0_tono" class="w-full p-2.5 text-sm"></div>
                    <div><label class="label-blue block mb-1.5">REGLAS INQUEBRANTABLES</label><textarea id="m0_reglas" class="w-full h-32 p-2.5 text-sm resize-none"></textarea></div>
                    <button onclick="guardarADN()" class="w-full bg-[#10b981] hover:bg-emerald-500 py-3 rounded-lg font-bold text-xs transition-all">ACTUALIZAR MEMORIA JSON</button>
                </div>
            </div>

            <div id="ui_mod_2" class="module-content hidden">
                <h2 class="text-2xl font-bold mb-6 text-white tracking-tight">Motor de Guiones (Retención)</h2>
                <div class="space-y-5">
                    <div>
                        <label class="label-red block mb-1.5">PROYECTO ACTIVO</label>
                        <select id="m2_marca" class="w-full p-2.5 text-sm">
                            <option value="La Viuda">La Viuda</option>
                            <option value="Monkygraff">Monkygraff</option>
                            <option value="TuIALista">TuIALista</option>
                            <option value="Ezzenshop">Ezzenshop</option>
                            <option value="Yayika Digital">Yayika Digital</option>
                            <option value="Yayika Apparel">Yayika Apparel</option>
                        </select>
                    </div>
                    <div><label class="label-blue block mb-1.5">TEMA O NOTICIA</label><textarea id="m2_tema" class="w-full h-40 p-2.5 text-sm resize-none"></textarea></div>
                    <div>
                        <label class="label-green block mb-1.5">OBJETIVO DE FORMATO</label>
                        <select id="m2_retencion" class="w-full p-2.5 text-sm">
                            <option>Documental Extenso (30+ min)</option>
                            <option>Formato Medio (15 min)</option>
                            <option>Impacto Corto (5 min)</option>
                        </select>
                    </div>
                </div>
            </div>

            <div id="ui_mod_3" class="module-content hidden">
                <h2 class="text-2xl font-bold mb-6 text-white tracking-tight">Micro-Hooks (Continuidad)</h2>
                <div class="space-y-5">
                    <div><label class="label-green block mb-1.5">RACCORD (BLOQUE ANTERIOR)</label><textarea id="m3_raccord" class="w-full h-24 p-2.5 text-sm resize-none"></textarea></div>
                    <div>
                        <label class="label-blue block mb-1.5">TIPO DE MICRO-HOOK</label>
                        <select id="m3_tipo" class="w-full p-2.5 text-sm">
                            <option value="Vacio_Informacion">Vacío de Información</option>
                            <option value="Disonancia">Disonancia Cognitiva</option>
                            <option value="Cuarta_Pared">Romper la Cuarta Pared</option>
                        </select>
                    </div>
                    <div><label class="label-blue block mb-1.5">INSTRUCCIÓN DE CONTINUIDAD</label><input type="text" id="m3_instruccion" class="w-full p-2.5 text-sm"></div>
                </div>
            </div>

            <div id="ui_mod_5" class="module-content hidden">
                <h2 class="text-2xl font-bold mb-6 text-white tracking-tight">Motor UGC 9:16 y Ventas</h2>
                <div class="space-y-4">
                    <div>
                        <label class="label-red block mb-1.5">GATILLO PSICOLÓGICO</label>
                        <select id="m5_gatillo" class="w-full p-2.5 text-sm">
                            <option value="FOMO">FOMO y Escasez</option>
                            <option value="Autoridad">Autoridad y Eficiencia</option>
                            <option value="Satira">Sátira y Rebeldía</option>
                        </select>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div><label class="label-blue block mb-1.5">DURACIÓN</label><select id="m5_duracion" class="w-full p-2.5 text-sm"><option>4 segundos</option><option>8 segundos</option></select></div>
                        <div><label class="label-blue block mb-1.5">AVATAR</label><select id="m5_avatar" class="w-full p-2.5 text-sm"><option>Femenino Gen-Z</option><option>Masculino Tech</option></select></div>
                    </div>
                </div>
            </div>

            <button onclick="ejecutar()" id="btn_main" class="w-full bg-[#2563eb] hover:bg-blue-500 py-4 mt-4 rounded-lg font-bold text-xs tracking-widest transition-all shadow-lg shadow-blue-500/20">COMPILAR Y EJECUTAR PROMPT</button>
        </div>

        <div class="w-[45%] flex flex-col glass-panel p-6 shadow-2xl relative">
            <h3 class="text-[#10b981] font-bold text-[11px] uppercase tracking-widest mb-4">Output Blindado (ADN Activo)</h3>
            <textarea id="output" class="flex-1 w-full bg-transparent text-slate-300 font-mono text-sm leading-relaxed resize-none outline-none scrollbar-hide" readonly></textarea>
        </div>
    </main>

    <script>
        let moduloActivo = 'mod_0';
        async function cargarADN() {
            const res = await fetch('/api/get_adn');
            const adn = await res.json();
            const marca = document.getElementById('m0_selector').value;
            document.getElementById('m0_estilo').value = adn[marca].estilo;
            document.getElementById('m0_tono').value = adn[marca].tono;
            document.getElementById('m0_reglas').value = adn[marca].reglas;
        }

        async function guardarADN() {
            const marca = document.getElementById('m0_selector').value;
            const data = { estilo: document.getElementById('m0_estilo').value, tono: document.getElementById('m0_tono').value, reglas: document.getElementById('m0_reglas').value };
            await fetch('/api/save_adn', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({marca, adn: data}) });
            alert("ADN Guardado en JSON con éxito.");
        }

        function switchTab(id) {
            moduloActivo = id;
            document.querySelectorAll('.module-content').forEach(el => el.classList.add('hidden'));
            document.getElementById('ui_' + id).classList.remove('hidden');
            document.querySelectorAll('nav button').forEach(b => b.classList.replace('active-tab', 'inactive-tab'));
            document.getElementById('btn_' + id).classList.replace('inactive-tab', 'active-tab');
        }

        async function ejecutar() {
            const btn = document.getElementById('btn_main');
            const out = document.getElementById('output');
            btn.innerHTML = "PROCESANDO CON INTELIGENCIA..."; btn.disabled = true;
            
            let payload = { modulo_id: moduloActivo, datos: {} };
            if(moduloActivo === 'mod_2') {
                payload.datos = { marca: document.getElementById('m2_marca').value, tema: document.getElementById('m2_tema').value, retencion: document.getElementById('m2_retencion').value };
            } else if (moduloActivo === 'mod_5') {
                payload.datos = { gatillo: document.getElementById('m5_gatillo').value, duracion: document.getElementById('m5_duracion').value };
            }

            try {
                const res = await fetch('/api/ejecutar', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
                const data = await res.json();
                out.value = data.resultado_ia || data.error;
            } catch (e) { out.value = "Error de conexión."; }
            finally { btn.innerHTML = "COMPILAR Y EJECUTAR PROMPT"; btn.disabled = false; }
        }
        window.onload = cargarADN;
    </script>
</body></html>
"""

@app.route('/')
def index():
    if 'user' not in session: return render_template_string(HTML_INDEX)
    return render_template_string(HTML_INDEX)

@app.route('/api/get_adn')
def get_adn():
    with open(DB_PROYECTOS, 'r') as f: return jsonify(json.load(f))

@app.route('/api/save_adn', methods=['POST'])
def save_adn():
    data = request.json
    with open(DB_PROYECTOS, 'r') as f: db = json.load(f)
    db[data['marca']] = data['adn']
    with open(DB_PROYECTOS, 'w') as f: json.dump(db, f)
    return jsonify({'status': 'success'})

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar_prompt():
    data = request.json
    mod_id, d = data['modulo_id'], data['datos']
    with open(DB_PROYECTOS, 'r') as f: adn_db = json.load(f)
    
    prompt = ""
    if mod_id == 'mod_2':
        info = adn_db.get(d['marca'], {})
        prompt = f"Actúa para {d['marca']}. Estilo: {info.get('estilo')}. Reglas: {info.get('reglas')}. Tema: {d['tema']}. Formato: {d['retencion']}. NO SALUDES, VE DIRECTO AL GRANO."
    else: prompt = f"Genera secuencia UGC. Gatillo: {d.get('gatillo')}. Duración: {d.get('duracion')}"

    # Bucle Failover
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            if any(x in m.name for x in ['preview', 'experimental', 'gemini-3']): continue
            try:
                model = genai.GenerativeModel(m.name)
                response = model.generate_content(prompt)
                return jsonify({'resultado_ia': response.text})
            except: continue
    return jsonify({'error': 'Falla de cuota general.'}), 500

if __name__ == '__main__':
    inicializar_dbs()
    app.run(host='0.0.0.0', port=5000)
