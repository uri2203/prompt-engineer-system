import os
import uuid # 🔧 NUEVO: Para crearle un ID único a cada orden
import time # 🔧 NUEVO: Para que la web espere al Xeon

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from modulos.usuarios import UsuarioManager
from modulos.boveda import BovedaManager
from modulos.ai_engine import AIEngine
from modulos.cctv_engine import CCTVEngine  
from modulos.voice_engine import VoiceEngine
from modulos.video_engine import VideoEngine # Importación del Ensamblador MP4

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin1978_master_key")

user_db = UsuarioManager()
boveda_db = BovedaManager()
ai_engine = AIEngine()
cctv_engine = CCTVEngine() 
voice_engine = VoiceEngine()
video_engine = VideoEngine() # Instanciación del motor de video

# ==========================================
# 🔧 MEMORIA RAM DEL SERVIDOR PARA EL XEON
# ==========================================
tareas_pendientes = []
resultados_completados = {}
# ==========================================

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
def api_get_usuarios(): return jsonify(user_db.listar_usuarios())

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
        data.get('gemini_keys', []),
        data.get('voice_api', ''),
        data.get('youtube_api', ''),
        data.get('tiktok_api', '')
    )
    return jsonify({"status": "success", "message": "Bóveda actualizada"})

@app.route('/api/generate_script', methods=['POST'])
@login_required
def api_generate_script():
    data = request.json
    marca = data.get('marca', 'La Viuda')
    contexto = data.get('contexto', '')
    peticion = data.get('peticion', '')
    longitud = data.get('longitud', '4900 palabras') 
    resultado = ai_engine.generar_guion(marca, contexto, peticion, longitud)
    return jsonify({"status": "success", "data": resultado})


# 🔧 MODIFICADO: Ahora manda la orden al Xeon en vez de intentar hacerla en la nube
@app.route('/api/generate_image', methods=['POST'])
@login_required
def api_generate_image():
    data = request.json
    prompt_visual = data.get('prompt', '')
    
    if not prompt_visual:
        return jsonify({"status": "error", "message": "Prompt visual vacío."})
        
    tarea_id = str(uuid.uuid4())
    
    # Metemos la orden a la sala de espera
    tareas_pendientes.append({
        "id": tarea_id,
        "prompt": prompt_visual
    })
    
    print(f"📦 [NUBE] Orden {tarea_id} en cola. Esperando al Obrero Xeon...")

    # La web se queda esperando hasta 10 minutos a que el Xeon entregue
    tiempo_espera = 0
    while tiempo_espera < 600:
        if tarea_id in resultados_completados:
            img_b64 = resultados_completados.pop(tarea_id)
            return jsonify({"status": "success", "image_url": img_b64})
        time.sleep(2)
        tiempo_espera += 2
        
    return jsonify({"status": "error", "message": "El motor local (Xeon) no entregó a tiempo."})


@app.route('/api/generate_audio', methods=['POST'])
@login_required
def api_generate_audio():
    data = request.json
    texto_locucion = data.get('texto', '')
    marca = data.get('marca', 'La Viuda') 
    
    if not texto_locucion:
        return jsonify({"status": "error", "message": "Texto de locución vacío."})
        
    resultado = voice_engine.generar_audio(texto_locucion, marca) 
    
    if "ERROR" in resultado:
        return jsonify({"status": "error", "message": resultado})
        
    return jsonify({"status": "success", "audio_url": resultado})

@app.route('/api/assemble_video', methods=['POST'])
@login_required
def api_assemble_video():
    data = request.json
    marca = data.get('marca', 'La Viuda')
    img_b64 = data.get('image_b64', '')
    audio_b64 = data.get('audio_b64', '')
    
    if not img_b64 or not audio_b64:
        return jsonify({"status": "error", "message": "Faltan assets para el ensamblaje."})
        
    resultado = video_engine.ensamblar_pipeline(marca, img_b64, audio_b64)
    return jsonify(resultado)

# ==========================================
# 🔧 PUERTAS DE ENLACE FÍSICO (Para el Xeon)
# ==========================================

@app.route('/api/nodo/polling', methods=['POST'])
def nodo_polling():
    datos_nodo = request.get_json()
    nodo_id = datos_nodo.get("nodo_id", "DESCONOCIDO")
    
    # Si hay trabajo pendiente, se lo damos al obrero que pregunte
    if len(tareas_pendientes) > 0:
        tarea = tareas_pendientes.pop(0)
        return jsonify({
            "status": "success",
            "hay_trabajo": True,
            "tarea": tarea
        }), 200
        
    return jsonify({
        "status": "success",
        "hay_trabajo": False,
        "mensaje": f"Cerebro Pinpinela reconoce al nodo {nodo_id}. Manténgase en Standby."
    }), 200

@app.route('/api/nodo/upload_result', methods=['POST'])
def nodo_upload_result():
    data = request.json
    tarea_id = data.get('tarea_id')
    img_b64 = data.get('image_b64')
    
    if tarea_id and img_b64:
        # Guardamos el resultado para que /api/generate_image lo recoja y se lo dé a la web
        resultados_completados[tarea_id] = img_b64
        return jsonify({"status": "success"}), 200
        
    return jsonify({"status": "error", "message": "Faltan datos en la entrega"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
