import os
import time
import logging
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine

# Importamos los silos de generación de texto
from modulos.mod_2_guiones import IngenieriaGuiones
from modulos.mod_4_empaquetado import EmpaquetadoContenido

# NUEVO: Importamos el motor de síntesis de voz (Cuerdas Vocales)
from modulos.bot_audio import AudioSynthEngine

# Configuración de telemetría y log industrial para el orquestador
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PINPINELA] - %(levelname)s - %(message)s')

class PinpinelaOrchestrator:
    def __init__(self):
        logging.info("Iniciando Sistema Nervioso Central: Pinpinela Orchestrator v1.1 (Audio Synth Integrado)")
        self.adn_db = ADNManager()
        self.motor_ia = AIEngine()
        
        # Conectamos los silos
        self.mod_guiones = IngenieriaGuiones()
        self.mod_empaquetado = EmpaquetadoContenido()
        self.mod_audio = AudioSynthEngine() # Inyección del silo de voz
        
        # NOTA ARQUITECTÓNICA: 
        # Aquí se conectará bot_video.py en la próxima actualización.

    def procesar_orden(self, tarea_id, marca, premisa, tipo_contenido="Medio"):
        """
        Ejecuta el pipeline de producción asíncrono End-to-End.
        Ahora procesa Fase 1 (ADN), Fase 2 (Scripting/Empaquetado) y Fase 3 (Audio Synth).
        """
        logging.info(f"=== INICIANDO ORDEN DE PRODUCCIÓN: {tarea_id} | MARCA: {marca} ===")
        
        # FASE 1: Extracción de ADN
        adn_completo = self.adn_db.cargar_todo()
        if marca not in adn_completo:
            logging.error(f"ADN no encontrado para la marca: {marca}. Abortando orden.")
            return {"status": "ERROR", "mensaje": "ADN de marca no registrado en la base de datos."}
        logging.info(f"Fase 1 completada: ADN de '{marca}' cargado exitosamente.")

        # FASE 2: Motor de Guiones
        logging.info(f"Fase 2 en proceso: Generando estructura narrativa de alta retención...")
        datos_guion = {
            "marca": marca,
            "premisa": premisa,
            "longitud": "Extenso (4,500+ palabras)" if tipo_contenido == "Extenso" else "Medio (1,500 palabras)",
            "framework": "Análisis Lógico Deductivo"
        }
        
        prompt_guion = self.mod_guiones.construir_prompt(datos_guion, adn_completo)
        resultado_guion = self.motor_ia.ejecutar_failover(prompt_guion)
        
        if "error" in resultado_guion:
            logging.error("Falla crítica en Motor de Texto (Gemini API).")
            return {"status": "FAILED", "fase": "Scripting", "detalle": resultado_guion["error"]}
        
        texto_generado = resultado_guion["resultado_ia"]
        logging.info("Fase 2 completada: Guion principal generado con éxito.")

        # FASE 2.1: Empaquetado
        logging.info("Fase 2.1 en proceso: Generando empaquetado y Vacío de Información...")
        datos_empaquetado = {
            "marca": marca,
            "guion": texto_generado[:1500],
            "enfoque": "Curiosidad/Secreto",
            "estilo": "Fotorrealismo",
            "plataforma": "YouTube"
        }
        
        prompt_empaquetado = self.mod_empaquetado.construir_prompt(datos_empaquetado, adn_completo)
        resultado_empaquetado = self.motor_ia.ejecutar_failover(prompt_empaquetado)
        empaquetado_generado = resultado_empaquetado.get("resultado_ia", "Error en empaquetado")
        logging.info("Fase 2.1 completada: Títulos y conceptos visuales generados.")

        # FASE 3: Audio Synth (LAS CUERDAS VOCALES)
        logging.info("Fase 3 en proceso: Iniciando Síntesis de Voz Neuronal...")
        resultado_audio = self.mod_audio.generar_audio_base(texto_generado, marca, tarea_id)
        
        if resultado_audio["status"] == "ERROR":
            logging.error(f"Falla crítica en Fase 3 (Audio): {resultado_audio['mensaje']}")
            return {"status": "FAILED", "fase": "Audio", "detalle": resultado_audio['mensaje']}
            
        ruta_mp3 = resultado_audio["ruta_audio"]
        voz_utilizada = resultado_audio["voz_usada"]
        logging.info(f"Fase 3 completada: Archivo MP3 ({voz_utilizada}) creado físicamente en -> {ruta_mp3}")

        # FASE 4: Render Engine 
        logging.info("Fase 4: Video Compiler -> [MODULO PENDIENTE DE ENSAMBLAJE: bot_video.py]")
        
        # FASE 5: Human in the Loop
        logging.info(f"=== ORDEN {tarea_id} DETENIDA: REQUIERE APROBACIÓN HUMANA PARA FASE 4 ===")

        # Retornamos el paquete finalizado al Dashboard
        return {
            "status": "PENDING_REVIEW",
            "tarea_id": tarea_id,
            "marca": marca,
            "guion_final": texto_generado,
            "empaquetado": empaquetado_generado,
            "ruta_audio": ruta_mp3
        }
