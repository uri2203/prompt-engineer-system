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

# --- DISEÑO CORPORATE TECH INTACTO ---

HTML_LOGIN = """
<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>AI Prompt System | Login</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-[#0B1120] h-screen flex items-center justify-center font-sans text-white">
    <div class="bg-[#0F1523] p-10 rounded-xl shadow-2xl border border-slate-800 w-96 text-center">
        <h2 class="text-[#3b82f6] font-bold text-xl mb-1 tracking-tight">AI Prompt System</h2>
        <p class="text-[10px] text-slate-500 uppercase tracking-widest mb-8 font-bold">Arquitectura Modular</p>
        <form action="/login" method="POST" class="space-y-4">
            <input type="text" name="username" placeholder="Usuario (Ej. 1978)" required class="w-full p-3 rounded-lg bg-[#0B1120] border border-slate-700 text-white outline-none focus:border-[#3b82f6] text-sm">
            <input type="password" name="password" placeholder="Contraseña" required class="w-full p-3 rounded-lg bg-[#0B1120] border border-slate-700 text-white outline-none focus:border-[#3b82f6] text-sm">
            <button type="submit" class="w-full bg-[#2563eb] hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-all text-sm">Ingresar al Sistema</button>
        </form>
    </div>
</body></html>
"""

HTML_INDEX = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Prompt System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0B1120; color: #f8fafc; font-family: 'Inter', system-ui, sans-serif; }
        .sidebar { background-color: #0F1523; border-right: 1px solid #1e293b; }
        .glass-panel { background-color: #0F1523; border: 1px solid #1e293b; border-radius: 12px; }
        .active-tab { background-color: transparent; border: 2px solid #3b82f6; box-shadow: inset 0 0 10px rgba(59,130,246,0.2); border-radius: 8px; color: #f8fafc; }
        .inactive-tab { color: #94a3b8; border: 2px solid transparent; }
        .inactive-tab:hover { background-color: #1e293b; color: white; border-radius: 8px; }
        input, select, textarea { background-color: #0B1120; border: 1px solid #334155; border-radius: 6px; color: #e2e8f0; outline: none; }
        input:focus, select:focus, textarea:focus { border-color: #3b82f6; }
        .label-red { color: #f43f5e; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
        .label-blue { color: #60a5fa; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
        .label-green { color: #34d399; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    </style>
</head>
<body class="h-screen flex overflow-hidden selection:bg-blue-500/30">
    
    <aside class="w-[280px] sidebar flex flex-col p-5 z-10">
        <div class="mb-8">
            <h1 class="text-xl font-bold text-[#3b82f6] tracking-tight">AI Prompt System</h1>
            <p class="text-[9px] text-slate-500 font-bold uppercase tracking-[0.15em] mt-1">Arquitectura Modular</p>
        </div>
        
        <nav class="flex-1 space-y-2">
            <button onclick="switchTab('mod_1')" id="btn_mod_1" class="w-full text-left px-4 py-3 text-sm font-medium transition-all inactive-tab">Mod 1: Traductor Universal</button>
            <button onclick="switchTab('mod_2')" id="btn_mod_2" class="w-full text-left px-4 py-3 text-sm font-medium transition-all inactive-tab">Mod 2: Guiones (Retención)</button>
            <button onclick="switchTab('mod_3')" id="btn_mod_3" class="w-full text-left px-4 py-3 text-sm font-medium transition-all inactive-tab">Mod 3: Micro-Hooks (Secuencia)</button>
            <button onclick="switchTab('mod_4')" id="btn_mod_4" class="w-full text-left px-4 py-3 text-sm font-medium transition-all inactive-tab">Mod 4: Metadatos y Visuales</button>
            <button onclick="switchTab('mod_5')" id="btn_mod_5" class="w-full text-left px-4 py-3 text-sm font-medium transition-all active-tab">Mod 5: UGC 9:16 y Ventas</button>
        </nav>

        <div class="mt-auto pt-4 border-t border-slate-800/50 flex justify-between items-center">
            <p class="text-[11px] text-slate-400">Estado del Sistema: <span class="text-[#10b981] font-bold">EN LÍNEA</span></p>
            {% if is_admin %}
                <a href="/logout" class="text-[10px] text-slate-500 hover:text-red-400 transition-colors">Salir</a>
            {% endif %}
        </div>
    </aside>

    <main class="flex-1 flex p-8 gap-6 bg-[#0B1120] overflow-hidden">
        
        <div class="w-[55%] flex flex-col gap-6 overflow-y-auto pr-2 scrollbar-hide">
            
            <div id="ui_mod_5" class="module-content block">
                <h2 class="text-2xl font-bold mb-6 text-white tracking-tight">Motor de Ventas y UGC 9:16</h2>
                
                <div class="space-y-5">
                    <div>
                        <label class="label-red block mb-1.5">GATILLO PSICOLÓGICO (NEURO-MARKETING)</label>
                        <select id="m5_gatillo" class="w-full p-2.5 text-sm">
                            <option value="FOMO">FOMO y Escasez (Urgencia / Exclusividad)</option>
                            <option value="Autoridad">Autoridad y Eficiencia (Solución técnica, ahorro de tiempo/dinero)</option>
                            <option value="Identidad">Identidad y Pertenencia (Marketing emocional, estatus social)</option>
                            <option value="Satira">Sátira y Rebeldía (Humor ácido, anti-marketing viral)</option>
                        </select>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="label-blue block mb-1.5">MODALIDAD</label>
                            <select id="m5_modalidad" class="w-full p-2.5 text-sm">
                                <option>Influencer Sintético (UGC)</option>
                                <option>Voz en Off Dinámica</option>
                                <option>Texto en Pantalla (Mudo)</option>
                            </select>
                        </div>
                        <div>
                            <label class="label-blue block mb-1.5">PERFIL DE AVATAR</label>
                            <select id="m5_avatar" class="w-full p-2.5 text-sm">
                                <option>Femenino Gen-Z</option>
                                <option>Masculino Tech/Ejecutivo</option>
                                <option>Especialista Clínico</option>
                            </select>
                        </div>
                        <div>
                            <label class="label-blue block mb-1.5">DURACIÓN</label>
                            <select id="m5_duracion" class="w-full p-2.5 text-sm">
                                <option>4 segundos</option>
                                <option>5 segundos</option>
                                <option>8 segundos</option>
                            </select>
                        </div>
                        <div>
                            <label class="label-blue block mb-1.5">NÚMERO DE BLOQUE</label>
                            <select id="m5_bloque" class="w-full p-2.5 text-sm">
                                <option>Bloque 1 (Inicio)</option>
                                <option>Bloque 2</option>
                                <option>Bloque 3</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label class="label-green block mb-1.5">RACCORD (ANCLAJE FÍSICO BLOQUE ANTERIOR)</label>
                        <input type="text" id="m5_raccord" placeholder="Pega el prompt visual anterior..." class="w-full p-2.5 text-sm">
                    </div>
                </div>
            </div>

            <div id="ui_mod_1" class="module-content hidden">
                <h2 class="text-2xl font-bold mb-6 text-white tracking-tight">Traductor Universal</h2>
                <div class="space-y-5">
                    <div>
                        <label class="label-blue block mb-1.5">ROL / EXPERTO</label>
                        <input type="text" id="m1_rol" placeholder="Ej: Ingeniero de Software, Asesor Estratégico" class="w-full p-2.5 text-sm">
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">CONTEXTO (VARIABLES)</label>
                        <textarea id="m1_contexto" placeholder="Datos clave, antecedentes..." class="w-full h-24 p-2.5 text-sm resize-none"></textarea>
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">PETICIÓN HUMANA</label>
                        <textarea id="m1_texto" placeholder="¿Qué necesitas que haga exactamente?" class="w-full h-32 p-2.5 text-sm resize-none"></textarea>
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">FORMATO DE SALIDA</label>
                        <select id="m1_formato" class="w-full p-2.5 text-sm">
                            <option>Código listo para copiar</option>
                            <option>Tabla Comparativa</option>
                            <option>Documento Formal</option>
                            <option>Lista de Acción Estratégica</option>
                            <option>Markdown</option>
                        </select>
                    </div>
                </div>
            </div>

            <button onclick="ejecutar()" id="btn_main" class="w-full bg-[#2563eb] hover:bg-blue-500 py-3.5 mt-2 rounded-lg font-bold text-[13px] tracking-wide shadow-[0_4px_14px_rgba(37,99,235,0.3)] transition-all">COMPILAR Y EJECUTAR</button>
        </div>

        <div class="w-[45%] flex flex-col glass-panel p-6 shadow-2xl relative">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-[#10b981] font-bold text-[11px] uppercase tracking-widest">Output Blindado (Lenguaje IA)</h3>
                <button onclick="copiarOutput()" class="bg-[#1e293b] hover:bg-slate-700 text-slate-300 text-[10px] px-3 py-1.5 rounded transition-all border border-slate-700">Copiar Todo</button>
            </div>
            <textarea id="output" class="flex-1 w-full bg-transparent text-slate-300 font-mono text-sm leading-relaxed resize-none outline-none scrollbar-hide" readonly placeholder="El resultado de la inyección lógica aparecerá aquí..."></textarea>
        </div>
    </main>

    <script>
        let moduloActivo = 'mod_5';
        
        function switchTab(id) {
            moduloActivo = id;
            document.querySelectorAll('nav button').forEach(b => {
                b.classList.remove('active-tab');
                b.classList.add('inactive-tab');
            });
            document.getElementById('btn_' + id).classList.remove('inactive-tab');
            document.getElementById('btn_' + id).classList.add('active-tab');
            
            document.querySelectorAll('.module-content').forEach(el => el.classList.add('hidden'));
            const targetUI = document.getElementById('ui_' + id);
            if(targetUI) { 
                targetUI.classList.remove('hidden'); 
            }
        }

        async function ejecutar() {
            const btn = document.getElementById('btn_main');
            const out = document.getElementById('output');
            btn.innerHTML = "PROCESANDO LÓGICA..."; 
            btn.disabled = true;
            
            let datos = {};
            if(moduloActivo === 'mod_5') {
                datos = {
                    gatillo: document.getElementById('m5_gatillo').value,
                    modalidad: document.getElementById('m5_modalidad').value,
                    avatar: document.getElementById('m5_avatar').value,
                    duracion: document.getElementById('m5_duracion').value,
                    bloque: document.getElementById('m5_bloque').value,
                    raccord: document.getElementById('m5_raccord').value
                };
            } else if (moduloActivo === 'mod_1') {
                datos = { 
                    rol: document.getElementById('m1_rol').value, 
                    contexto: document.getElementById('m1_contexto').value,
                    texto: document.getElementById('m1_texto').value,
                    formato: document.getElementById('m1_formato').value
                };
            }

            try {
                const res = await fetch('/api/ejecutar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({modulo_id: moduloActivo, datos: datos})
                });
                const data = await res.json();
                out.value = data.resultado_ia || data.error;
            } catch (e) {
                out.value = "Error de conexión con el motor IA.";
            } finally {
                btn.innerHTML = "COMPILAR Y EJECUTAR"; 
                btn.disabled = false;
            }
        }

        function copiarOutput() {
            const out = document.getElementById('output');
            out.select();
            document.execCommand('copy');
            alert('Código copiado al portapapeles');
        }
    </script>
</body></html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if verificar_credenciales(u, p):
            session['user'] = u
            session['isAdmin'] = (u == '1978')
            return redirect(url_for('dashboard'))
        return "Acceso denegado. Intenta de nuevo.", 401
    return render_template_string(HTML_LOGIN)

@app.route('/')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template_string(HTML_INDEX, is_admin=session.get('isAdmin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/ejecutar', methods=['POST'])
def ejecutar_prompt():
    if 'user' not in session:
        return jsonify({'error': 'No auth'}), 401
    try:
        data = request.json
        # Actualización estricta de modelo para compatibilidad con v1beta de Google
        model = genai.GenerativeModel('gemini-1.5-pro')
        modulo_id = data.get('modulo_id')
        datos = data.get('datos', {})
        
        prompt = ""
        
        # --- INYECCIÓN DE LÓGICA DE BACKEND (DOCUMENTO MAESTRO) ---
        
        if modulo_id == 'mod_1':
            prompt = f"""[IDENTIDAD]: Actúa como un {datos.get('rol', 'Experto')}.
[CONTEXTO]: Considera los siguientes datos como base inamovible: {datos.get('contexto', '')}.
[TAREA]: Ejecuta la siguiente orden: {datos.get('texto', '')}.
[RESTRICCIONES]: Actúa con profesionalismo ejecutivo y experto. Prohibido el lenguaje genérico, el relleno y las obviedades. Sé directo y estratégico. Si se requiere código, entrégalo completo y final, sin fragmentos sueltos.
[FORMATO DE SALIDA]: Entrega el resultado estrictamente como {datos.get('formato', 'Texto')}.
"""
        elif modulo_id == 'mod_5':
            gatillo_logic = ""
            if datos.get('gatillo') == "FOMO":
                gatillo_logic = "Aplica el sesgo de aversión a la pérdida. El guion debe generar ansiedad de oportunidad: el producto se agota rápido, pertenece a un lote exclusivo. Usa lenguaje de urgencia extrema."
            elif datos.get('gatillo') == "Autoridad":
                gatillo_logic = "Ataca el dolor de la ineficiencia. Demuestra cómo este producto digital elimina fricciones al instante. Lenguaje directo, corporativo y basado en ROI."
            elif datos.get('gatillo') == "Identidad":
                gatillo_logic = "Aplica marketing emocional. El guion debe hacer sentir al usuario que adquirir esto le otorga estatus social y pertenencia a un grupo exclusivo."
            elif datos.get('gatillo') == "Satira":
                gatillo_logic = "Aplica humor ácido y sátira viral. Usa el anti-marketing como herramienta de conexión. Lenguaje de tendencia para TikTok."

            prompt = f"""[ESTRATEGIA DE CAMPAÑA Y VENTAS]: Eres un Media Buyer Senior y experto en Neuro-Marketing. Desarrolla esta secuencia publicitaria 9:16.
[GATILLO PSICOLÓGICO]: Tu único objetivo es la conversión inmediata. {gatillo_logic}
[SECUENCIA]: {datos.get('bloque', 'Bloque 1')}. Duración: {datos.get('duracion', '4 segundos')}. Continuación de (Si aplica): {datos.get('raccord', 'N/A')}.
[FASE 1: DISEÑO VISUAL]: Modalidad: {datos.get('modalidad', 'UGC')}. Perfil: {datos.get('avatar', 'Gen-Z')}. Integra el producto de referencia manteniendo el 100% de su fidelidad.
[FASE 2: ACCIÓN Y FÍSICA]: Render 4K fotorrealista. Física inquebrantable. Sin deformaciones corporales ni del producto.
[FORMATO DE SALIDA ESTRICTO]:
[PROMPT VISUAL - VIDEO]: (Instrucción técnica de cámara y acción para IA).
[GUION DE VENTA]: (Texto exacto de locución. Debe aplicar el sesgo psicológico, atacando el dolor del cliente y forzando la urgencia. Límite estricto de palabras según la duración). Prohibido vender características, vende la transformación.
"""
        else:
            prompt = f"Procesando Módulo: {modulo_id} con datos: {datos}"

        # Ejecución contra la API
        response = model.generate_content(prompt)
        return jsonify({'status': 'success', 'resultado_ia': response.text})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    inicializar_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
