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

# ── MONITOREO DE NODOS (patrón heartbeat) ────────────────────────────────────
# Render no puede hacer ping a IPs locales (192.168.x.x son privadas).
# Por eso el Xeon reporta el estado aquí, y el dashboard lo lee.
_estado_nodos = {"sd": "off", "voz": "off", "parallax": "off", "nube": "on", "ts": 0}

@app.route('/api/nodos')
@login_required
def api_nodos():
    # Si el último reporte del Xeon es viejo (>60s), marcar locales como desconocidos
    antiguedad = time.time() - _estado_nodos.get("ts", 0)
    if antiguedad > 60:
        return jsonify({"sd": "off", "voz": "off", "parallax": "off", "nube": "on"})
    return jsonify({
        "sd": _estado_nodos.get("sd", "off"),
        "voz": _estado_nodos.get("voz", "off"),
        "parallax": _estado_nodos.get("parallax", "off"),
        "nube": "on",  # si responde este endpoint, la nube está viva
    })

@app.route('/api/nodos/reportar', methods=['POST'])
def api_nodos_reportar():
    # El Xeon reporta aquí el estado de los nodos locales (hace ping y envía).
    data = request.json or {}
    _estado_nodos["sd"]       = data.get("sd", "off")
    _estado_nodos["voz"]      = data.get("voz", "off")
    _estado_nodos["parallax"] = data.get("parallax", "off")
    _estado_nodos["ts"]       = time.time()
    return jsonify({"status": "ok"})

# ── BOT PINPINELA — Orquestador de órdenes ───────────────────────────────────
# ── BOT PINPINELA — Orquestador de órdenes ───────────────────────────────────
# ── BOT PINPINELA — Orquestador de órdenes ───────────────────────────────────
# Config del cronjob (persiste en disco para sobrevivir reinicios)
import json as _json_cron
CRON_FILE = "/tmp/cron_pinpinela.json"

def _leer_cron():
    try:
        with open(CRON_FILE) as f:
            return _json_cron.load(f)
    except Exception:
        return {"activo": False, "hora": "08:00", "canales": [], "formato": "9:16", "ultima_ejecucion": ""}

def _guardar_cron(cfg):
    try:
        with open(CRON_FILE, "w") as f:
            _json_cron.dump(cfg, f)
    except Exception:
        pass

@app.route('/api/bot/cron/config', methods=['GET', 'POST'])
@login_required
def api_bot_cron_config():
    if request.method == 'POST':
        data = request.json or {}
        cfg = _leer_cron()
        cfg["activo"]  = data.get("activo", cfg.get("activo", False))
        cfg["hora"]    = data.get("hora", cfg.get("hora", "08:00"))
        cfg["canales"] = data.get("canales", cfg.get("canales", []))
        cfg["formato"] = data.get("formato", cfg.get("formato", "9:16"))
        _guardar_cron(cfg)
        return jsonify({"status": "ok", "config": cfg})
    return jsonify(_leer_cron())

@app.route('/api/bot/cron/tick', methods=['POST'])
def api_bot_cron_tick():
    """El Xeon llama aquí cada minuto. Si es la hora del cronjob y no se ha
    ejecutado hoy, dispara las órdenes de los canales configurados."""
    from datetime import datetime
    cfg = _leer_cron()
    if not cfg.get("activo"):
        return jsonify({"status": "inactivo"})

    ahora = datetime.now()
    hora_actual = ahora.strftime("%H:%M")
    hoy = ahora.strftime("%Y-%m-%d")

    # ¿Ya es la hora y no se ejecutó hoy?
    if hora_actual == cfg.get("hora") and cfg.get("ultima_ejecucion") != hoy:
        cfg["ultima_ejecucion"] = hoy
        _guardar_cron(cfg)
        canales = cfg.get("canales", [])
        disparadas = []
        for marca in canales:
            try:
                tid = _disparar_orden_interna(marca, cfg.get("formato", "9:16"), "")
                disparadas.append({"marca": marca, "tarea_id": tid})
            except Exception as e:
                disparadas.append({"marca": marca, "error": str(e)})
        return jsonify({"status": "disparado", "ordenes": disparadas})
    return jsonify({"status": "esperando", "hora_actual": hora_actual, "hora_cron": cfg.get("hora")})

def _disparar_orden_interna(marca, formato, premisa):
    """Lógica compartida: genera guion + encola. Devuelve tarea_id."""
    import json as _json
    es_largo = formato == "16:9"
    longitud = "2800 palabras" if es_largo else "130 palabras"
    formato_calculado = "16:9" if formato == "16:9" else "9:16"

    yt_api_key = boveda_db.obtener_datos().get('youtube_api', '')
    contexto_viral = trend_engine.inyectar_contexto_viral(marca, yt_api_key)
    contexto_base = premisa if premisa else "Genera el tema desde la tendencia detectada."
    contexto_absoluto = f"{contexto_base}\n\n{contexto_viral}"

    resultado = compliance_engine.blindar_guion(
        ai_engine_instancia=ai_engine, marca=marca, contexto=contexto_absoluto,
        peticion=premisa or "Tema en tendencia del canal",
        longitud=longitud, formato=formato_calculado
    )
    if isinstance(resultado, str):
        if resultado.startswith("ERROR"):
            raise Exception(resultado[:120])
        guion = _json.loads(resultado)
    else:
        guion = resultado

    tarea_id = str(uuid.uuid4())
    escenas = guion.get("escenas", [])
    if not escenas:
        raise Exception("Guion sin escenas")
    titulo = guion.get("titulo", guion.get("titulo_sugerido", ""))
    texto_locucion = " ".join(e.get("texto_locucion", "") for e in escenas if e.get("texto_locucion"))

    tarea_worker = {
        "id": tarea_id, "tipo": "IMAGEN",
        "prompt": _json.dumps(escenas, ensure_ascii=False),
        "formato": formato_calculado, "marca": marca,
        "texto_locucion": texto_locucion, "titulo_sugerido": titulo,
        "origen": "bot_pinpinela_cron",
    }
    try:
        with open(f"/tmp/orden_bot_{tarea_id}.json", "w") as f:
            _json.dump(tarea_worker, f)
    except Exception:
        pass
    cola_de_renderizado.append(tarea_worker)
    return tarea_id

@app.route('/api/bot/estado')
@login_required
def api_bot_estado():
    """Estado en vivo de los 4 bloques del Bot Pinpinela para el dashboard."""
    cron = _leer_cron()
    # Estado de nodos (reportado por el Xeon)
    antiguedad = time.time() - _estado_nodos.get("ts", 0)
    nodos_vivos = antiguedad <= 60
    sd_on   = nodos_vivos and _estado_nodos.get("sd") == "on"
    voz_on  = nodos_vivos and _estado_nodos.get("voz") == "on"
    return jsonify({
        "scripting": {
            "estado": "activo" if cron.get("activo") else "en_espera",
            "cron_hora": cron.get("hora", "—"),
            "cron_activo": cron.get("activo", False),
            "canales": cron.get("canales", []),
        },
        "voz": {"estado": "online" if voz_on else "offline"},
        "video": {"estado": "online" if sd_on else "ocioso",
                  "en_cola": len(cola_de_renderizado)},
        "cola": {"pendientes": len(resultados_itinerantes)},
    })

@app.route('/api/bot/sugerir_tema', methods=['POST'])
@login_required
def api_bot_sugerir_tema():
    """Devuelve el tema en tendencia del canal (TrendEngine) para rellenar la premisa.
    Con API key de YouTube = tendencia real. Sin key = simulación estructurada."""
    data = request.json or {}
    marca = data.get('marca', 'La Viuda')
    try:
        yt_api_key = boveda_db.obtener_datos().get('youtube_api', '')
        tendencia = trend_engine.escanear_traccion_competitiva(marca, yt_api_key)
        if not tendencia:
            return jsonify({"status": "error", "message": "Sin tendencias para este canal"}), 404
        en_vivo = bool(yt_api_key)
        return jsonify({
            "status": "ok",
            "tema": tendencia.get("tema_base", ""),
            "referencia": tendencia.get("titulo_competidor", ""),
            "vph": round(tendencia.get("vph", 0), 1),
            "en_vivo": en_vivo,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/lanzar_orden', methods=['POST'])
@login_required
def api_bot_lanzar_orden():
    """El Bot Pinpinela dispara una orden: genera el guion (con tendencias del
    TrendEngine) y lo deja listo para encolar. Es el cerebro de la automatización."""
    data = request.json or {}
    marca   = data.get('marca', 'La Viuda')
    formato = data.get('formato', '9:16')
    premisa = data.get('premisa', '').strip()

    # Formato → longitud (largo vs short)
    es_largo = formato in ("16:9",) and data.get('tipo', 'largo') != 'short'
    longitud = "2800 palabras" if es_largo else "130 palabras"
    formato_calculado = "16:9" if formato == "16:9" else "9:16"

    try:
        # 1. TrendEngine: inyecta contexto viral del canal
        yt_api_key = boveda_db.obtener_datos().get('youtube_api', '')
        contexto_viral = trend_engine.inyectar_contexto_viral(marca, yt_api_key)

        # Si no hay premisa manual, el tema lo guía la tendencia
        contexto_base = premisa if premisa else "Genera el tema desde la tendencia detectada."
        contexto_absoluto = f"{contexto_base}\n\n{contexto_viral}"

        # 2. Generar el guion blindado (compliance + NeuroEngine vía ai_engine)
        resultado = compliance_engine.blindar_guion(
            ai_engine_instancia=ai_engine,
            marca=marca, contexto=contexto_absoluto,
            peticion=premisa or "Tema en tendencia del canal",
            longitud=longitud, formato=formato_calculado
        )

        # 3. Parsear el guion (viene como JSON string) y armar la tarea del worker
        import json as _json
        if isinstance(resultado, str):
            if resultado.startswith("ERROR"):
                return jsonify({"status": "error", "message": resultado}), 500
            try:
                guion = _json.loads(resultado)
            except Exception:
                return jsonify({"status": "error", "message": "Guion no es JSON válido"}), 500
        else:
            guion = resultado

        tarea_id = str(uuid.uuid4())
        escenas = guion.get("escenas", [])
        titulo = guion.get("titulo", guion.get("titulo_sugerido", ""))
        # Reconstruir el texto de locución completo desde las escenas
        texto_locucion = " ".join(
            e.get("texto_locucion", "") for e in escenas if e.get("texto_locucion")
        )

        if not escenas:
            return jsonify({"status": "error", "message": "El guion no trae escenas"}), 500

        # 4. Encolar la ORDEN VISUAL (el worker genera imágenes → voz → video → MP4)
        tarea_worker = {
            "id": tarea_id,
            "tipo": "IMAGEN",
            "prompt": _json.dumps(escenas, ensure_ascii=False),
            "formato": formato_calculado,
            "marca": marca,
            "texto_locucion": texto_locucion,
            "titulo_sugerido": titulo,
            "origen": "bot_pinpinela",
        }
        # Guardar en disco (sobrevive reinicios de Render) y encolar
        try:
            with open(f"/tmp/orden_bot_{tarea_id}.json", "w") as f:
                _json.dump(tarea_worker, f)
        except Exception:
            pass
        cola_de_renderizado.append(tarea_worker)

        return jsonify({
            "status": "PENDING_REVIEW",
            "tarea_id": tarea_id,
            "marca": marca,
            "formato": formato_calculado,
            "titulo": titulo,
            "num_escenas": len(escenas),
            "encolado": True,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


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
    longitud = data.get('longitud', '130 palabras') # Estandarizado para Shorts de alta retención


    formato_crudo = str(data.get('formato', '')) + " " + str(longitud)
    formato_crudo = formato_crudo.lower()
    formato_calculado = "9:16" if "short" in formato_crudo or "9:16" in formato_crudo else "16:9"

    yt_api_key = boveda_db.obtener_datos().get('youtube_api', '')
    contexto_viral = trend_engine.inyectar_contexto_viral(marca, yt_api_key)
    contexto_absoluto = f"{contexto_base}\n\n{contexto_viral}"

    resultado = compliance_engine.blindar_guion(
        ai_engine_instancia=ai_engine,
        marca=marca, contexto=contexto_absoluto,
        peticion=peticion, longitud=longitud, formato=formato_calculado
    )
    return jsonify({"status": "success", "data": resultado})

@app.route('/api/generate_audio', methods=['POST'])
@login_required
def api_generate_audio():
    data = request.json
    resultado = voice_engine.generar_audio(data.get('texto', ''), data.get('marca', 'La Viuda')) 
    return jsonify({"status": "success", "audio_url": resultado})

# ========================================================
# RUTA ACTUALIZADA: ENSAMBLAJE CON SOPORTE PARA SUBTÍTULOS
# ========================================================
@app.route('/api/assemble_video', methods=['POST'])
@login_required
def api_assemble_video():
    data = request.json
    tarea_id = str(uuid.uuid4())
    marca = data.get('marca', 'La Viuda')
    voice_id = "PHKlYg202ODwQRa3Fxuo" if marca == "Monkygraff" else "GTY55jD77hLBRrnQOhNk"

    tarea = {
        "id": tarea_id,
        "tipo": "ENSAMBLAJE",
        "texto_locucion": data.get('texto_locucion', ''),
        "escenas_texto": data.get('escenas_texto', []),
        "escenas": data.get('escenas', []),
        "hooks": data.get('hooks', []),
        "titulo_sugerido": data.get('titulo_sugerido', ''),
        "voice_id": voice_id,
        "elevenlabs_key": boveda_db.obtener_datos().get('voice_api', ''),
        "marca": marca
    }

    # Guardar en disco — sobrevive reinicios de Render
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
    # Solo devuelve el JSON — el worker es quien guarda en disco local
    return jsonify({"status": "success", "paquete": paquete})

# Ruta para el frontend (requiere login)
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

# Ruta interna para el worker (sin login, usa clave compartida)
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
    cola_de_renderizado.append({"id": tarea_id, "tipo": "IMAGEN", "prompt": prompt, "formato": formato, "marca": data.get('marca', 'La Viuda')})
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
    # Si la cola está vacía, recuperar tareas guardadas en disco (ensamblajes y órdenes del bot)
    if len(cola_de_renderizado) == 0:
        for patron in ("/tmp/orden_bot_*.json", "/tmp/ensamblaje_*.json"):
            archivos = glob.glob(patron)
            for archivo in archivos:
                try:
                    with open(archivo, "r") as f:
                        tarea = _json.load(f)
                    cola_de_renderizado.append(tarea)
                    os.remove(archivo)
                    break  # procesar una a la vez
                except:
                    pass
            if len(cola_de_renderizado) > 0:
                break
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

