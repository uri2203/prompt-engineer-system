import os
import time
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps

from modulos.usuarios import UsuarioManager
from modulos.boveda import BovedaManager
from modulos.ai_engine import AIEngine
from modulos.cctv_engine import CCTVEngine  
from modulos.voice_engine import VoiceEngine
from modulos.video_engine import VideoEngine  
from modulos.trend_engine import TrendEngine
from modulos.compliance_engine import ComplianceEngine

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin1978_master_key")

user_db = UsuarioManager()
boveda_db = BovedaManager()
ai_engine = AIEngine()
cctv_engine = CCTVEngine()  
voice_engine = VoiceEngine()
video_engine = VideoEngine()
trend_engine = TrendEngine()
compliance_engine = ComplianceEngine()

# COLA DE TAREAS PARA LA DARK FACTORY
cola_de_renderizado = []
resultados_itinerantes = {}
audios_temporales = {}  # Almacén temporal de audios grandes

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "message": "No autorizado"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session: return redirect(url_for('index'))
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pw = request.form.get('password', '').strip()
        usuarios = user_db.listar_usuarios()
        if user in usuarios and usuarios[user]['pass'] == pw:
            session.permanent = True
            session['user'] = user
            return redirect(url_for('index'))
        else:
            flash('ACCESO DENEGADO', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index(): return render_template('workspace.html', active_page='workspace')

@app.route('/usuarios')
@login_required
def usuarios(): return render_template('usuarios.html', active_page='usuarios')

@app.route('/configuracion')
@login_required
def configuracion(): return render_template('configuracion.html', active_page='configuracion')

@app.route('/mantenimiento')
@login_required
def mantenimiento(): return render_template('mantenimiento.html', active_page='logs')

@app.route('/bot')
@login_required
def bot(): return render_template('bot_dashboard.html', active_page='bot')

@app.route('/api/get_logs')
@login_required
def api_get_logs():
    return jsonify({"logs": ["[SISTEMA] Motor Pinpinela en Standby.", "[INFO] Enlace con Workspace establecido."] })

@app.route('/api/get_usuarios')
@login_required
def api_get_usuarios(): 
    return jsonify(user_db.listar_usuarios())

@app.route('/api/telemetria')
@login_required
def api_telemetria():
    llaves_activas = len(boveda_db.obtener_llaves())
    return jsonify({
        "uptime": "Sincronizado", "latencia": "0.02s", "tokens_totales": 0,
        "api_status": f"TANQUES API: {llaves_activas}/5", 
        "historial_latencia": [0.02, 0.02, 0.02, 0.02, 0.02],
        "historial_tokens": [0, 0, 0, 0, 0]
    })

@app.route('/api/get_boveda')
@login_required
def api_get_boveda(): 
    return jsonify(boveda_db.obtener_datos())

@app.route('/api/save_boveda', methods=['POST'])
@login_required
def api_save_boveda():
    data = request.json
    boveda_db.guardar_boveda_completa(
        data.get('gemini_keys', []), data.get('voice_api', ''),
        data.get('youtube_api', ''), data.get('tiktok_api', '')
    )
    return jsonify({"status": "success", "message": "Bóveda actualizada"})

@app.route('/api/generate_script', methods=['POST'])
@login_required
def api_generate_script():
    data = request.json
    marca = data.get('marca', 'La Viuda')
    contexto_base = data.get('contexto', '')
    peticion = data.get('peticion', '')
    longitud = data.get('longitud', '130 palabras') 

    peticion_enriquecida = f"{peticion}\n\n[FRAGMENTACIÓN REQUERIDA]: Divide el guion en bloques de máximo 4-5 segundos. Genera una matriz de entre 12 y 15 escenas visuales independientes. Cada escena debe representar un cambio de plano o ángulo.\n\n[INSTRUCCIÓN VISUAL OBLIGATORIA]: Al generar la descripción de cada escena, asegúrate de incorporar al final de ella los siguientes parámetros para el renderizado: 'Cinematografía hiperrealista, 8k, Unreal Engine 5, iluminación volumétrica'."

    formato_crudo = str(data.get('formato', '')) + " " + str(longitud)
    formato_crudo = formato_crudo.lower()
    formato_calculado = "9:16" if "short" in formato_crudo or "9:16" in formato_crudo else "16:9"

    yt_api_key = boveda_db.obtener_datos().get('youtube_api', '')
    contexto_viral = trend_engine.inyectar_contexto_viral(marca, yt_api_key)
    contexto_absoluto = f"{contexto_base}\n\n{contexto_viral}"

    resultado = compliance_engine.blindar_guion(
        ai_engine_instancia=ai_engine,
        marca=marca, contexto=contexto_absoluto,
        peticion=peticion_enriquecida, longitud=longitud, formato=formato_calculado
    )
    return jsonify({"status": "success", "data": resultado})

@app.route('/api/generate_audio', methods=['POST'])
@login_required
def api_generate_audio():
    data = request.json
    resultado = voice_engine.generar_audio(data.get('texto', ''), data.get('marca', 'La Viuda')) 
    return jsonify({"status": "success", "audio_url": resultado})

@app.route('/api/assemble_video', methods=['POST'])
@login_required
def api_assemble_video():
    data = request.json
    tarea_id = str(uuid.uuid4())
    marca = data.get('marca', 'La Viuda')
    voice_id = "PHKlYg202ODwQRa3Fxuo" if marca == "Monkygraff" else "GTY55jD77hLBRrnQOhNk"

    # INYECCIÓN DEL FORMATO: Asegura que el Worker sepa exactamente si es LARGO (16:9)
    tarea = {
        "id": tarea_id,
        "tipo": "ENSAMBLAJE",
        "texto_locucion": data.get('texto_locucion', ''),
        "escenas_texto": data.get('escenas_texto', []),
        "voice_id": voice_id,
        "elevenlabs_key": boveda_db.obtener_datos().get('voice_api', ''),
        "marca": marca,
        "formato": data.get('formato', '16:9') # CORRECCIÓN APLICADA AQUÍ
    }

    import json as _json
    with open(f"/tmp/ensamblaje_{tarea_id}.json", "w") as f:
        _json.dump(tarea, f)

    cola_de_renderizado.append(tarea)
    return jsonify({"status": "success", "message": "ÓRDEN DE ENSAMBLAJE ENVIADA A LA DARK FACTORY"})

def _procesar_paquete(marca, titulo, texto_locucion, formato):
    print(f"[PAQUETE] Generando paquete de publicación para {marca}...")
    paquete = ai_engine.generar_paquete_publicacion(marca, titulo, texto_locucion, formato)
    if not paquete:
        return jsonify({"status": "error", "message": "Error generando paquete con Gemini"}), 500
    return jsonify({"status": "success", "paquete": paquete})

@app.route('/api/generar_paquete', methods=['POST'])
@login_required
def api_generar_paquete():
    data = request.json
    return _procesar_paquete(
        data.get('marca', 'La Viuda'),
        data.get('titulo', ''),
        data.get('texto_locucion', ''),
        data.get('formato', '9:16')
    )

@app.route('/api/interna/generar_paquete', methods=['POST'])
def api_generar_paquete_interna():
    data = request.json
    if data.get('clave_interna') != app.secret_key:
        return jsonify({"status": "error", "message": "No autorizado"}), 401
    return _procesar_paquete(
        data.get('marca', 'La Viuda'),
        data.get('titulo', ''),
        data.get('texto_locucion', ''),
        data.get('formato', '9:16')
    )

@app.route('/api/generate_image', methods=['POST'])
@login_required
def api_generate_image():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt: return jsonify({"status": "error", "message": "Prompt vacío"})
    
    tarea_id = str(uuid.uuid4())
    formato = data.get('formato', '16:9')
    cola_de_renderizado.append({"id": tarea_id, "tipo": "IMAGEN", "prompt": prompt, "formato": formato})
    return jsonify({"status": "EN_COLA", "tarea_id": tarea_id, "message": "Orden enviada a la Dark Factory."})

@app.route('/api/check_image/<tarea_id>')
@login_required
def check_image(tarea_id):
    if tarea_id in resultados_itinerantes:
        return jsonify({"status": "READY", "image_url": resultados_itinerantes.pop(tarea_id)})
    return jsonify({"status": "PENDING"})

@app.route('/api/nodo/encolar_tarea', methods=['POST'])
def nodo_encolar_tarea():
    tarea = request.json
    if tarea:
        cola_de_renderizado.append(tarea)
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400

@app.route('/api/nodo/polling', methods=['POST'])
def nodo_polling():
    import json as _json, glob
    if len(cola_de_renderizado) == 0:
        archivos = glob.glob("/tmp/ensamblaje_*.json")
        for archivo in archivos:
            try:
                with open(archivo, "r") as f:
                    tarea = _json.load(f)
                cola_de_renderizado.append(tarea)
                os.remove(archivo)
                break  
            except:
                pass
    if len(cola_de_renderizado) > 0:
        return jsonify({"status": "success", "hay_trabajo": True, "tarea": cola_de_renderizado.pop(0)}), 200
    return jsonify({"status": "success", "hay_trabajo": False}), 200

@app.route('/api/nodo/upload_result', methods=['POST'])
def upload_result():
    data = request.json
    tid, img = data.get('tarea_id'), data.get('image_b64')
    if tid and img:
        resultados_itinerantes[tid] = img
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
