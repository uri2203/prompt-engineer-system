import os
import time
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps

# --- [SILO: MÓDULOS DE INGENIERÍA - RESTAURACIÓN COMPLETA] ---
from modulos.usuarios import UsuarioManager
from modulos.boveda import BovedaManager
from modulos.ai_engine import AIEngine
from modulos.cctv_engine import CCTVEngine  
from modulos.voice_engine import VoiceEngine
from modulos.video_engine import VideoEngine 

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin1978_master_key")

# --- [INSTANCIACIÓN DE MOTORES] ---
user_db = UsuarioManager()
boveda_db = BovedaManager()
ai_engine = AIEngine()
cctv_engine = CCTVEngine() 
voice_engine = VoiceEngine()
video_engine = VideoEngine()

# --- [ESTRUCTURA DE MEMORIA DINÁMICA: DARK FACTORY] ---
# Esta sección maneja al Xeon sin bloquear el servidor de Render.
cola_de_renderizado = []
resultados_itinerantes = {} 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "message": "No autorizado"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- [RUTAS DE INTERFAZ: DISEÑO CORPORATE TECH] ---
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

# --- [API: TELEMETRÍA Y GESTIÓN DE BÓVEDA (SILO RECUPERADO)] ---
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

# --- [API: MOTORES DE GENERACIÓN] ---
@app.route('/api/generate_script', methods=['POST'])
@login_required
def api_generate_script():
    data = request.json
    resultado = ai_engine.generar_guion(
        data.get('marca', 'La Viuda'), data.get('contexto', ''),
        data.get('peticion', ''), data.get('longitud', '4900 palabras')
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
    resultado = video_engine.ensamblar_pipeline(data.get('marca'), data.get('image_b64'), data.get('audio_b64'))
    return jsonify(resultado)

# --- [API: INTEGRACIÓN XEON ASÍNCRONA - CERO BLOQUEOS] ---
@app.route('/api/generate_image', methods=['POST'])
@login_required
def api_generate_image():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt: return jsonify({"status": "error", "message": "Prompt vacío"})
    
    tarea_id = str(uuid.uuid4())
    cola_de_renderizado.append({"id": tarea_id, "prompt": prompt})
    
    return jsonify({
        "status": "EN_COLA", 
        "tarea_id": tarea_id,
        "message": "Orden enviada a la Dark Factory (Xeon)."
    })

@app.route('/api/check_image/<tarea_id>')
@login_required
def check_image(tarea_id):
    if tarea_id in resultados_itinerantes:
        return jsonify({"status": "READY", "image_url": resultados_itinerantes.pop(tarea_id)})
    return jsonify({"status": "PENDING"})

# --- [NODO LOCAL: PROTOCOLO DE COMUNICACIÓN FÍSICA] ---
@app.route('/api/nodo/polling', methods=['POST'])
def nodo_polling():
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
