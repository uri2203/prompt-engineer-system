import os
import time
import logging
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine
from modulos.mod_2_guiones import IngenieriaGuiones
from modulos.mod_4_empaquetado import EmpaquetadoContenido
from modulos.bot_audio import AudioSynthEngine

# NUEVO: Importación del motor de video (El Músculo)
from modulos.bot_video import VideoRenderEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PINPINELA] - %(levelname)s - %(message)s')

class PinpinelaOrchestrator:
    def __init__(self):
        logging.info("Iniciando Sistema Nervioso Central: Pinpinela Orchestrator v1.2 (Full Pipeline)")
        self.adn_db = ADNManager()
        self.motor_ia = AIEngine()
        self.mod_guiones = IngenieriaGuiones()
        self.mod_empaquetado = EmpaquetadoContenido()
        self.mod_audio = AudioSynthEngine()
        self.mod_video = VideoRenderEngine() # Inyección del silo de video

    def procesar_orden(self, tarea_id, marca, premisa, formato="16:9"):
        """
        Ejecuta el pipeline de producción asíncrono End-to-End.
        Fase 1 (ADN) -> Fase 2 (Texto) -> Fase 3 (Audio) -> Fase 4 (Video).
        """
        logging.info(f"=== INICIANDO ORDEN DE PRODUCCIÓN: {tarea_id} | MARCA: {marca} | FORMATO: {formato} ===")
        
        # FASE 1: ADN
        adn_completo = self.adn_db.cargar_todo()
        if marca not in adn_completo:
            return {"status": "ERROR", "mensaje": "ADN de marca no registrado."}

        # FASE 2: Guion
        datos_guion = {"marca": marca, "premisa": premisa, "longitud": "Medio", "framework": "Análisis Lógico Deductivo"}
        prompt_guion = self.mod_guiones.construir_prompt(datos_guion, adn_completo)
        resultado_guion = self.motor_ia.ejecutar_failover(prompt_guion)
        if "error" in resultado_guion: return {"status": "FAILED", "fase": "Scripting", "detalle": resultado_guion["error"]}
        texto_generado = resultado_guion["resultado_ia"]

        # FASE 2.1: Empaquetado
        datos_empaquetado = {"marca": marca, "guion": texto_generado[:1000], "enfoque": "Secreto", "plataforma": "YouTube"}
        prompt_empaquetado = self.mod_empaquetado.construir_prompt(datos_empaquetado, adn_completo)
        resultado_emp = self.motor_ia.ejecutar_failover(prompt_empaquetado)
        empaquetado_gen = resultado_emp.get("resultado_ia", "Error")

        # FASE 3: Audio Synth
        resultado_audio = self.mod_audio.generar_audio_base(texto_generado, marca, tarea_id)
        if resultado_audio["status"] == "ERROR": return {"status": "FAILED", "fase": "Audio", "detalle": resultado_audio['mensaje']}
        ruta_mp3 = resultado_audio["ruta_audio"]

        # FASE 4: Video Render (Músculo Dual)
        # El orquestador le ordena al motor de video usar el formato elegido en el dashboard
        logging.info(f"Fase 4: Compilando video en formato {formato}...")
        resultado_video = self.mod_video.compilar_video_base(ruta_mp3, marca, tarea_id)
        
        if resultado_video["status"] == "ERROR":
            return {"status": "FAILED", "fase": "Video", "detalle": resultado_video['mensaje']}

        # FASE 5: Human in the Loop (Finalizado)
        return {
            "status": "PENDING_REVIEW",
            "tarea_id": tarea_id,
            "marca": marca,
            "formato": formato,
            "guion_final": texto_generado,
            "empaquetado": empaquetado_gen,
            "ruta_audio": ruta_mp3,
            "ruta_video": resultado_video["ruta_video"]
        }
