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
PROYECTOS_DB = 'proyectos_db.json'

def inicializar_db():
    if not os.path.exists(DB_PATH):
        admin_pw = hashlib.sha256("1978".encode()).hexdigest()
        with open(DB_PATH, 'w') as f:
            json.dump({"1978": admin_pw}, f)
    if not os.path.exists(PROYECTOS_DB):
        with open(PROYECTOS_DB, 'w') as f:
            json.dump({}, f)

def verificar_credenciales(u, p):
    inicializar_db()
    with open(DB_PATH, 'r') as f:
        db = json.load(f)
    return db.get(u) == hashlib.sha256(p.encode()).hexdigest()

def cargar_proyectos():
    inicializar_db()
    with open(PROYECTOS_DB, 'r') as f:
        return json.load(f)

def guardar_proyecto(nombre, datos):
    db = cargar_proyectos()
    db[nombre] = datos
    with open(PROYECTOS_DB, 'w') as f:
        json.dump(db, f)

# --- DISEÑO CORPORATE TECH INTACTO Y EXPANDIDO ---

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
        
        <nav class="flex-1 space-y-2 overflow-y-auto scrollbar-hide">
            <button onclick="switchTab('mod_0')" id="btn_mod_0" class="w-full text-left px-4 py-3 text-sm font-medium transition-all inactive-tab border-l-4 border-transparent">Mod 0: Núcleo (DB)</button>
            <button onclick="switchTab('mod_1')" id="btn_mod_1" class="w-full text-left px-4 py-3 text-sm font-medium transition-all inactive-tab border-l-4 border-transparent">Mod 1: Traductor Universal</button>
            <button onclick="switchTab('mod_2')" id="btn_mod_2" class="w-full text-left px-4 py-3 text-sm font-medium transition-all inactive-tab border-l-4 border-transparent">Mod 2: Guiones (Retención)</button>
            <button onclick="switchTab('mod_3')" id="btn_mod_3" class="w-full text-left px-4 py-3 text-sm font-medium transition-all inactive-tab border-l-4 border-transparent">Mod 3: Micro-Hooks</button>
            <button onclick="switchTab('mod_4')" id="btn_mod_4" class="w-full text-left px-4 py-3 text-sm font-medium transition-all inactive-tab border-l-4 border-transparent">Mod 4: Metadatos Visuales</button>
            <button onclick="switchTab('mod_5')" id="btn_mod_5" class="w-full text-left px-4 py-3 text-sm font-medium transition-all active-tab border-l-4 border-transparent">Mod 5: UGC 9:16 y Ventas</button>
        </nav>

        <div class="mt-auto pt-4 border-t border-slate-800/50 flex justify-between items-center">
            <p class="text-[11px] text-slate-400">Estado: <span class="text-[#10b981] font-bold">EN LÍNEA</span></p>
            {% if is_admin %}
                <a href="/logout" class="text-[10px] text-slate-500 hover:text-red-400 transition-colors">Salir</a>
            {% endif %}
        </div>
    </aside>

    <main class="flex-1 flex p-8 gap-6 bg-[#0B1120] overflow-hidden">
        
        <div class="w-[55%] flex flex-col gap-6 overflow-y-auto pr-2 scrollbar-hide">
            
            <div id="ui_mod_0" class="module-content hidden">
                <h2 class="text-2xl font-bold mb-6 text-white tracking-tight">Núcleo de Identidad (Base de Datos)</h2>
                <div class="space-y-5">
                    <div>
                        <label class="label-green block mb-1.5">NOMBRE DEL PROYECTO / MARCA</label>
                        <input type="text" id="m0_nombre" placeholder="Ej. La Viuda, TuIALista, Monkygraff..." class="w-full p-2.5 text-sm">
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="label-blue block mb-1.5">ARQUETIPO DE VOZ</label>
                            <select id="m0_voz" class="w-full p-2.5 text-sm">
                                <option>Realismo Clínico y Seco</option>
                                <option>Eficiencia Corporate Tech</option>
                                <option>Alta Energía Hype-Urbano</option>
                                <option>Marketing Emocional Suave</option>
                                <option>Sátira Viral y Humor Ácido</option>
                            </select>
                        </div>
                        <div>
                            <label class="label-blue block mb-1.5">ESTRATEGIA DE TÍTULOS</label>
                            <select id="m0_titulos" class="w-full p-2.5 text-sm">
                                <option>Vacío de Información</option>
                                <option>Beneficio Directo</option>
                                <option>Gancho de Tendencia</option>
                                <option>Curiosidad Emocional</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">ESTÉTICA VISUAL BASE</label>
                        <select id="m0_estetica" class="w-full p-2.5 text-sm">
                            <option>Documental/Fotoperiodismo B&N</option>
                            <option>Azules Profundos Corporativos</option>
                            <option>Saturación Neón-Gamer</option>
                            <option>Elegancia Minimalista</option>
                            <option>Parodia Alto Impacto TikTok</option>
                        </select>
                    </div>
                    <div>
                        <label class="label-red block mb-1.5">LÍMITES ESTRICTOS (REGLAS INQUEBRANTABLES)</label>
                        <textarea id="m0_limites" placeholder="Ej: Prohibido usar rostros humanos, Nunca resumir la noticia..." class="w-full h-24 p-2.5 text-sm resize-none"></textarea>
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

            <div id="ui_mod_2" class="module-content hidden">
                <h2 class="text-2xl font-bold mb-6 text-white tracking-tight">Ingeniería de Guiones (Super Retención)</h2>
                <div class="space-y-5">
                    <div>
                        <label class="label-green block mb-1.5">PROYECTO / MARCA (CARGA ADN)</label>
                        <select id="m2_proyecto" class="w-full p-2.5 text-sm">
                            {% for p in proyectos %}
                            <option value="{{ p }}">{{ p }}</option>
                            {% endfor %}
                            {% if not proyectos %}<option value="">(Registra un proyecto en Mod 0)</option>{% endif %}
                        </select>
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">PREMISA O NOTICIA BASE</label>
                        <textarea id="m2_premisa" placeholder="Pega aquí la noticia o idea central..." class="w-full h-32 p-2.5 text-sm resize-none"></textarea>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="label-blue block mb-1.5">LONGITUD ESTIMADA</label>
                            <select id="m2_longitud" class="w-full p-2.5 text-sm">
                                <option>Short/TikTok (150 palabras)</option>
                                <option>Medio (1,500 palabras)</option>
                                <option>Extenso/Documental (4,500+ palabras)</option>
                            </select>
                        </div>
                        <div>
                            <label class="label-blue block mb-1.5">FRAMEWORK NARRATIVO</label>
                            <select id="m2_framework" class="w-full p-2.5 text-sm">
                                <option>Bucle Abierto (Intriga constante)</option>
                                <option>Problema-Agitación-Solución (Ventas)</option>
                                <option>Análisis Lógico Deductivo (Info)</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">PETICIÓN ESPECÍFICA (OPCIONAL)</label>
                        <input type="text" id="m2_peticion" placeholder="¿Algún ángulo a destacar?" class="w-full p-2.5 text-sm">
                    </div>
                </div>
            </div>

            <div id="ui_mod_3" class="module-content hidden">
                <h2 class="text-2xl font-bold mb-6 text-white tracking-tight">Micro-Hooks (Fragmentación Secuencial)</h2>
                <div class="space-y-5">
                    <div>
                        <label class="label-green block mb-1.5">PROYECTO / MARCA</label>
                        <select id="m3_proyecto" class="w-full p-2.5 text-sm">
                            {% for p in proyectos %}
                            <option value="{{ p }}">{{ p }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">PREMISA O DATO DE CHOQUE</label>
                        <textarea id="m3_premisa" placeholder="La idea central del gancho..." class="w-full h-24 p-2.5 text-sm resize-none"></textarea>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="label-red block mb-1.5">DURACIÓN DEL BLOQUE (LÍMITE IA)</label>
                            <select id="m3_duracion" class="w-full p-2.5 text-sm">
                                <option value="4">4 segundos (10 palabras max)</option>
                                <option value="5">5 segundos (12-15 palabras)</option>
                                <option value="8">8 segundos (18-22 palabras)</option>
                                <option value="15">15 segundos (35-40 palabras)</option>
                            </select>
                        </div>
                        <div>
                            <label class="label-blue block mb-1.5">NÚMERO DE BLOQUE</label>
                            <select id="m3_bloque" class="w-full p-2.5 text-sm">
                                <option>Bloque 1 (Inicio Absoluto)</option>
                                <option>Bloque 2 (Continuación)</option>
                                <option>Bloque 3 (Continuación)</option>
                                <option>Bloque 4 (Continuación)</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label class="label-green block mb-1.5">MEMORIA DE CONTINUIDAD (SOLO BLOQUE 2+)</label>
                        <textarea id="m3_memoria" placeholder="Pega el audio/prompt del bloque anterior para enlazar..." class="w-full h-20 p-2.5 text-sm resize-none"></textarea>
                    </div>
                </div>
            </div>

            <div id="ui_mod_4" class="module-content hidden">
                <h2 class="text-2xl font-bold mb-6 text-white tracking-tight">Metadatos y Visuales (CTR Extremo)</h2>
                <div class="space-y-5">
                    <div>
                        <label class="label-green block mb-1.5">PROYECTO / MARCA</label>
                        <select id="m4_proyecto" class="w-full p-2.5 text-sm">
                            {% for p in proyectos %}
                            <option value="{{ p }}">{{ p }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">GUION O PREMISA FINAL</label>
                        <textarea id="m4_guion" placeholder="Pega el guion completo aquí..." class="w-full h-32 p-2.5 text-sm resize-none"></textarea>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="label-red block mb-1.5">ENFOQUE DEL TÍTULO</label>
                            <select id="m4_enfoque" class="w-full p-2.5 text-sm">
                                <option>Amenaza/Urgencia</option>
                                <option>Curiosidad/Secreto</option>
                                <option>Contraste/Anomalía</option>
                                <option>Beneficio Extremo</option>
                            </select>
                        </div>
                        <div>
                            <label class="label-blue block mb-1.5">PLATAFORMA OBJETIVO</label>
                            <select id="m4_plataforma" class="w-full p-2.5 text-sm">
                                <option>YouTube (Largo formato)</option>
                                <option>TikTok / Shorts</option>
                                <option>Instagram Reels</option>
                            </select>
                        </div>
                    </div>
                    <div>
                        <label class="label-blue block mb-1.5">ESTILO ARTÍSTICO DE IMAGEN (MINIATURA 16:9)</label>
                        <select id="m4_estilo" class="w-full p-2.5 text-sm">
                            <option>Fotorrealismo Cinematográfico</option>
                            <option>Terror Psicológico / Realismo Sucio</option>
                            <option>Fotoperiodismo Crudo en B/N</option>
                            <option>Cyberpunk / Neón Saturado</option>
                            <option>Minimalismo Conceptual</option>
                            <option>Corporate Tech Limpio</option>
                        </select>
                    </div>
                </div>
            </div>

            <div id="ui_mod_5" class="module-content">
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
            
            // 1. Limpiar todos los botones
            document.querySelectorAll('nav button').forEach(b => {
                b.classList.remove('active-tab');
                b.classList.add('inactive-tab');
                b.classList.remove('border-emerald-500');
                b.classList.add('border-transparent');
            });
            
            // 2. Activar el botón presionado
            const activeBtn = document.getElementById('btn_' + id);
            activeBtn.classList.remove('inactive-tab');
            activeBtn.classList.add('active-tab');
            if(id === 'mod_0') {
                activeBtn.classList.remove('border-transparent');
                activeBtn.classList.add('border-emerald-500');
            }
            
            // 3. Ocultar todos los módulos
            document.querySelectorAll('.module-content').forEach(el => {
                el.classList.add('hidden');
            });
            
            // 4. Mostrar solo el módulo objetivo
            const targetUI = document.getElementById('ui_' + id);
            if(targetUI) { 
                targetUI.classList.remove('hidden'); 
            }
            
            // 5. Ajustar el estilo del botón principal
            const btn = document.getElementById('btn_main');
            if (id === 'mod_0') {
                btn.innerHTML = "GUARDAR IDENTIDAD EN BASE DE DATOS";
                btn.classList.remove('bg-[#2563eb]', 'hover:bg-blue-500');
                btn.classList.add('bg-[#10b981]', 'hover:bg-emerald-500');
            } else {
                btn.innerHTML = "COMPILAR Y EJECUTAR";
                btn.classList.remove('bg-[#10b981]', 'hover:bg-emerald-500');
                btn.classList.add('bg-[#2563eb]', 'hover:bg-blue-500');
            }
        }

        async function ejecutar() {
            const btn = document.getElementById('btn_main');
            const out = document.getElementById('output');
            btn.innerHTML = "PROCESANDO LÓGICA..."; 
            btn.disabled = true;
            
            let datos = {};
            if(moduloActivo === 'mod_0') {
                datos = {
                    nombre: document.getElementById('m0_nombre').value,
                    voz: document.getElementById('m0_voz').value,
                    estetica: document.getElementById('m0_estetica').value,
                    titulos: document.getElementById('m0_titulos').value,
                    limites: document.getElementById('m0_limites').value
                };
            } else if (moduloActivo === 'mod_1') {
                datos = { 
                    rol: document.getElementById('m1_rol').value, 
                    contexto: document.getElementById('m1_contexto').value,
                    texto: document.getElementById('m1_texto').value,
                    formato: document.getElementById('m1_formato').value
                };
            } else if (moduloActivo === 'mod_2') {
                datos = {
                    proyecto: document.getElementById('m2_proyecto').value,
                    premisa: document.getElementById('m2_premisa').value,
                    longitud: document.getElementById('m2_longitud').value,
                    framework: document.getElementById('m2_framework').value,
                    peticion: document.getElementById('m2_peticion').value
                };
            } else if (moduloActivo === 'mod_3') {
                datos = {
                    proyecto: document.getElementById('m3_proyecto').value,
                    premisa: document.getElementById('m3_premisa').value,
                    duracion: document.getElementById('m3_duracion').value,
                    bloque: document.getElementById('m3_bloque').value,
                    memoria: document.getElementById('m3_memoria').value
                };
            } else if (moduloActivo === 'mod_4') {
                datos = {
                    proyecto: document.getElementById('m4_proyecto').value,
                    guion: document.getElementById('m4_guion').value,
                    enfoque: document.getElementById('m4_enfoque').value,
                    plataforma: document.getElementById('m4_plataforma').value,
                    estilo: document.getElementById('m4_estilo').value
                };
            } else if (moduloActivo === 'mod_5') {
                datos = {
                    gatillo: document.getElementById('m5_gatillo').value,
                    modalidad: document.getElementById('m5_modalidad').value,
                    avatar: document.getElementById('m5_avatar').value,
                    duracion: document.getElementById('m5_duracion').value,
                    bloque: document.getElementById('m5_bloque').value,
                    raccord: document.getElementById('m5_raccord').value
                };
            }

            try {
                const res = await fetch('/api/ejecutar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({modulo_id: moduloActivo, datos: datos})
                });
                const data = await res.json();
                
                if(moduloActivo === 'mod_0' && data.status === 'success') {
                    out.value = "PROYECTO GUARDADO CON ÉXITO EN LA BASE DE DATOS.\n\nRecarga la página (F5) para que el proyecto aparezca en los menús desplegables del resto de módulos.";
                } else {
                    out.value = data.resultado_ia || data.error;
                }
            } catch (e) {
                out.value = "Error de conexión con el motor IA o Base de Datos.";
            } finally {
                if (moduloActivo === 'mod_0') {
                    btn.innerHTML = "GUARDAR IDENTIDAD EN BASE DE DATOS";
                } else {
                    btn.innerHTML = "COMPILAR Y EJECUTAR";
                }
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
    proyectos = cargar_proyectos()
    return render_template_string(HTML_INDEX, is_admin=session.get('isAdmin'), proyectos=proyectos.keys())

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
        modulo_id = data.get('modulo_id')
        datos = data.get('datos', {})
        
        # --- MODULO 0: GUARDADO EN BASE DE DATOS LOCAL ---
        if modulo_id == 'mod_0':
            nombre = datos.get('nombre')
            if not nombre:
                return jsonify({'error': 'El nombre del proyecto es obligatorio.'}), 400
            guardar_proyecto(nombre, datos)
            return jsonify({'status': 'success', 'resultado_ia': 'Guardado'})

        # --- RUTINA DE AUTO-DESCUBRIMIENTO DE MODELO ---
        modelo_valido = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelo_valido = m.name
                if 'flash' in m.name.lower() or 'pro' in m.name.lower():
                    break
                    
        if not modelo_valido:
            return jsonify({'error': 'Error Crítico: Tu API Key no tiene modelos habilitados.'}), 500

        model = genai.GenerativeModel(modelo_valido)
        
        # --- INYECCIÓN DE LÓGICA DE BACKEND MAESTRA ---
        prompt = ""
        silenciador = "\n[REGLA MAESTRA INQUEBRANTABLE]: Entrega ÚNICAMENTE el output final estructurado. Tienes estrictamente prohibido incluir saludos, explicaciones, confirmaciones o texto conversacional previo/posterior como 'Aquí tienes...' o 'Claro que sí'."
        proyectos_db = cargar_proyectos()
        
        if modulo_id == 'mod_1':
            prompt = f"""[IDENTIDAD]: Actúa como un {datos.get('rol', 'Experto')}.
[CONTEXTO]: Considera los siguientes datos como base inamovible: {datos.get('contexto', '')}.
[TAREA]: Ejecuta la siguiente orden: {datos.get('texto', '')}.
[RESTRICCIONES]: Actúa con profesionalismo ejecutivo. Prohibido el lenguaje genérico. Sé directo y estratégico. Si es código, entrégalo final sin fragmentos.
[FORMATO DE SALIDA]: Entrega el resultado estrictamente como {datos.get('formato', 'Texto')}. {silenciador}"""

        elif modulo_id == 'mod_2':
            p_data = proyectos_db.get(datos.get('proyecto', ''), {})
            prompt = f"""[IDENTIDAD Y TONO]: Eres un guionista experto en retención. Escribe estrictamente bajo este arquetipo: {p_data.get('voz', 'Profesional')}.
[CONTEXTO DE MARCA]: Respeta los siguientes límites inquebrantables: {p_data.get('limites', 'Ninguno')} y cumple normas de monetización.
[TAREA]: Desarrolla un guion de longitud {datos.get('longitud')} basado en: {datos.get('premisa', '')}. Petición extra: {datos.get('peticion', 'N/A')}.
[ESTRUCTURA]: Aplica framework: {datos.get('framework')}. Prohibido iniciar con saludos o introducciones lentas. La primera línea ataca la curiosidad. Densidad alta, ritmo rápido, frases cortas.
[FORMATO DE SALIDA]: Guion limpio, dividido por bloques lógicos. {silenciador}"""

        elif modulo_id == 'mod_3':
            p_data = proyectos_db.get(datos.get('proyecto', ''), {})
            dur = int(datos.get('duracion', 5))
            limite_palabras = "10 palabras máximo" if dur == 4 else "12 a 15 palabras exactas" if dur == 5 else "18 a 22 palabras exactas" if dur == 8 else "35 a 40 palabras exactas"
            
            ctx_memoria = ""
            if "Inicio" in datos.get('bloque', ''):
                ctx_memoria = "Este es el segundo 0 del video. Aplica regla de 1 segundo (cero saludos, detonar intriga pura)."
            else:
                ctx_memoria = f"El bloque anterior terminó así: '{datos.get('memoria', '')}'. Mantén continuidad visual de personajes/entorno y continúa el guion exactamente donde se quedó."

            prompt = f"""[IDENTIDAD]: Director de cinematografía y retención. Tono: {p_data.get('voz', 'Seco')}.
[SECUENCIA]: {datos.get('bloque')}. Duración estricta: {dur} segundos.
[CONTEXTO DE MEMORIA]: {ctx_memoria}.
[TAREA]: Desarrolla gancho basado en: {datos.get('premisa')}.
[RESTRICCIONES DURAS]: Límites de marca: {p_data.get('limites', 'N/A')}. El texto de locución DEBE tener matemáticamente: {limite_palabras}.
[FORMATO DE SALIDA ESTRICTO]: Dos bloques exactos:
[AUDIO-VOZ]: (Texto exacto para voz).
[PROMPT-VIDEO]: (Instrucción técnica en inglés para IA de video). {silenciador}"""

        elif modulo_id == 'mod_4':
            p_data = proyectos_db.get(datos.get('proyecto', ''), {})
            prompt = f"""[IDENTIDAD]: Estratega viral y SEO. Arquetipo: {p_data.get('voz', 'Experto')}.
[CONTEXTO]: Analiza: {datos.get('guion', '')}.
[TAREA]: Empaquetado para {datos.get('plataforma')}.
[RESTRICCIONES]: Títulos: Usa Vacío de Información, no resumas. Enfoque: {datos.get('enfoque')}. Imágenes: Resolución 1920x1080 (16:9) estricto. Estilo de arte: {datos.get('estilo')}. Límites extra: {p_data.get('limites', 'Ninguno')}.
[FORMATO DE SALIDA ESTRICTO]: 
TÍTULOS: (5 opciones).
PROMPT DE MINIATURA (Inglés): (1 instrucción técnica, garantizando 1920x1080 y estilo visual).
DESCRIPCIÓN Y TAGS: (Párrafo SEO y etiquetas). {silenciador}"""

        elif modulo_id == 'mod_5':
            gatillo_logic = "Aplica el sesgo de aversión a la pérdida. Urgencia extrema." if datos.get('gatillo') == "FOMO" else "Ataca el dolor de la ineficiencia. Lenguaje ROI." if datos.get('gatillo') == "Autoridad" else "Aplica marketing emocional y estatus social." if datos.get('gatillo') == "Identidad" else "Aplica humor ácido y sátira viral anti-marketing."
            prompt = f"""[ESTRATEGIA]: Media Buyer Senior y Neuro-Marketing. Secuencia 9:16.
[GATILLO]: Conversión inmediata. {gatillo_logic}
[SECUENCIA]: {datos.get('bloque', 'Bloque 1')}. Duración: {datos.get('duracion', '4 segundos')}. Continuación: {datos.get('raccord', 'N/A')}.
[FASE 1]: Modalidad: {datos.get('modalidad', 'UGC')}. Perfil: {datos.get('avatar', 'Gen-Z')}.
[FASE 2]: Render 4K fotorrealista. Física inquebrantable.
[FORMATO DE SALIDA ESTRICTO]:
[PROMPT VISUAL - VIDEO]: (Cámara y acción).
[GUION DE VENTA]: (Locución directa al dolor/urgencia). Prohibido vender características. {silenciador}"""

        response = model.generate_content(prompt)
        return jsonify({'status': 'success', 'resultado_ia': response.text})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    inicializar_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
