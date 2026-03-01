import os
import time
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from modulos.usuarios import UsuarioManager
from modulos.boveda import BovedaManager
from modulos.ai_engine import AIEngine
from modulos.cctv_engine import CCTVEngine  
from modulos.voice_engine import VoiceEngine
from modulos.video_engine import VideoEngine

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin1978_master_key")

user_db = UsuarioManager()
boveda_db = BovedaManager()
ai_engine = AIEngine()
cctv_engine = CCTVEngine() 
voice_engine = VoiceEngine()
video_engine = VideoEngine()

# --- SISTEMAS DE COLA Y ALMACÉN ---
cola_de_renderizado = []
resultados_itinerantes = {} # Aquí se guardarán las imágenes terminadas temporalmente

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "message": "No autorizado"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# [RUTAS DE INTERFAZ - SIN CAMBIOS]
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

@app.route('/api/generate_script', methods=['POST'])
@login_required
def api_generate_script():
    data = request.json
    resultado = ai_engine.generar_guion(data.get('marca'), data.get('contexto'), data.get('peticion'), data.get('longitud'))
    return jsonify({"status": "success", "data": resultado})

# --- FASE 2: GENERACIÓN ASÍNCRONA (NUEVA LÓGICA) ---
@app.route('/api/generate_image', methods=['POST'])
@login_required
def api_generate_image():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt: return jsonify({"status": "error", "message": "Prompt vacío"})
    
    # CCTV Engine ahora solo empaqueta la tarea
    tarea = cctv_engine.empaquetar_tarea(prompt)
    cola_de_renderizado.append(tarea)
    
    return jsonify({
        "status": "EN_COLA", 
        "tarea_id": tarea['id'],
        "message": "Orden enviada a la Dark Factory (Nodo Local)."
    })

# --- RUTA PARA QUE EL NAVEGADOR PREGUNTE SI YA ESTÁ LISTA ---
@app.route('/api/check_image/<tarea_id>')
@login_required
def check_image(tarea_id):
    if tarea_id in resultados_itinerantes:
        return jsonify({"status": "READY", "image_url": resultados_itinerantes[tarea_id]})
    return jsonify({"status": "PENDING"})

# --- RUTA PARA QUE SU PC ENTREGUE LA IMAGEN TERMINADA ---
@app.route('/api/nodo/upload_result', methods=['POST'])
def upload_result():
    data = request.json
    tarea_id = data.get('tarea_id')
    img_b64 = data.get('image_b64')
    if tarea_id and img_b64:
        resultados_itinerantes[tarea_id] = img_b64
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 400

# [OTRAS RUTAS DE API - SIN CAMBIOS]
@app.route('/api/generate_audio', methods=['POST'])
@login_required
def api_generate_audio():
    data = request.json
    resultado = voice_engine.generar_audio(data.get('texto'), data.get('marca')) 
    return jsonify({"status": "success", "audio_url": resultado})

@app.route('/api/assemble_video', methods=['POST'])
@login_required
def api_assemble_video():
    data = request.json
    tarea = {
        "id": f"video_{int(time.time())}",
        "tipo": "VIDEO_MP4",
        "marca": data.get('marca'),
        "image_b64": data.get('image_b64'),
        "audio_b64": data.get('audio_b64')
    }
    cola_de_renderizado.append(tarea)
    return jsonify({"status": "success", "message": "Video en cola de ensamblaje."})

@app.route('/api/nodo/polling', methods=['POST'])
def nodo_polling():
    if len(cola_de_renderizado) > 0:
        tarea_actual = cola_de_renderizado.pop(0)
        return jsonify({"status": "success", "hay_trabajo": True, "tarea": tarea_actual}), 200
    return jsonify({"status": "success", "hay_trabajo": False}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
