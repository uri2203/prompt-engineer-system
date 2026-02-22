import os
import time
from flask import Flask, render_template, request, jsonify
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine
from modulos.auditoria import AuditoriaSystem  # <--- Inyección de Auditoría

# Silos de Producción
from modulos.mod_1_traductor import TraductorUniversal
from modulos.mod_2_guiones import IngenieriaGuiones
from modulos.mod_3_hooks import GeneradorHooks
from modulos.mod_4_empaquetado import EmpaquetadoContenido
from modulos.mod_5_ventas import MotorVentasUGC
from modulos.bot_orquestador import PinpinelaOrchestrator

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "admin_secret_1978_secure")

# Instanciación del Sistema de Auditoría (La Caja Negra)
logger = AuditoriaSystem()

# Instanciación del Clúster
adn_db = ADNManager()
ia_motor = AIEngine()
bot_pinpinela = PinpinelaOrchestrator()

@app.route('/')
def index(): return render_template('workspace.html', active_page='workspace')

@app.route('/mantenimiento')
def mantenimiento(): return render_template('mantenimiento.html', active_page='mantenimiento')

@app.route('/configuracion')
def configuracion(): return render_template('configuracion.html', active_page='configuracion')

@app.route('/bot')
def bot(): return render_template('bot_dashboard.html', active_page='bot')

# --- API DE AUDITORÍA ---
@app.route('/api/get_logs')
def get_logs():
    return jsonify({'logs': logger.leer_ultimos()})

@app.route('/api/bot/lanzar_orden', methods=['POST'])
def bot_lanzar_orden():
    data = request.json
    tarea_id = f"ORD-{int(time.time())}"
    marca = data.get('marca', 'La Viuda')
    formato = data.get('formato', '16:9')
    
    logger.registrar("ORQUESTADOR", f"Nueva orden recibida: {tarea_id} para {marca} ({formato})", "INFO")
    
    resultado = bot_pinpinela.procesar_orden(tarea_id, marca, data.get('premisa', ''), formato)
    
    if resultado.get("status") == "PENDING_REVIEW":
        logger.registrar("ORQUESTADOR", f"Orden {tarea_id} completada exitosamente hasta Fase 4", "SUCCESS")
    else:
        logger.registrar("ORQUESTADOR", f"Fallo en orden {tarea_id}: {resultado.get('detalle')}", "ERROR")
        
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
