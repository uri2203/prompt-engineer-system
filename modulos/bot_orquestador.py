import os
import time
import logging
from modulos.adn_manager import ADNManager
from modulos.ai_engine import AIEngine

# Importamos los silos de generación de texto que ya construiste
from modulos.mod_2_guiones import IngenieriaGuiones
from modulos.mod_4_empaquetado import EmpaquetadoContenido

# Configuración de telemetría y log industrial para el orquestador
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PINPINELA] - %(levelname)s - %(message)s')

class PinpinelaOrchestrator:
    def __init__(self):
        logging.info("Iniciando Sistema Nervioso Central: Pinpinela Orchestrator v1.0")
        self.adn_db = ADNManager()
        self.motor_ia = AIEngine()
        
        # Conectamos las herramientas manuales para que el bot las use en automático
        self.mod_guiones = IngenieriaGuiones()
        self.mod_empaquetado = EmpaquetadoContenido()
        
        # NOTA ARQUITECTÓNICA: 
        # Aquí se conectarán bot_audio.py y bot_video.py en la próxima actualización.

    def procesar_orden(self, tarea_id, marca, premisa, tipo_contenido="Extenso"):
        """
        Ejecuta el pipeline de producción asíncrono End-to-End.
        Actualmente procesa Fase 1 (Extracción ADN) y Fase 2 (Scripting & Empaquetado).
        """
        logging.info(f"=== INICIANDO ORDEN DE PRODUCCIÓN: {tarea_id} | MARCA: {marca} ===")
        
        # FASE 1: Extracción de ADN de la Base de Datos JSON (Silo Hermético)
        adn_completo = self.adn_db.cargar_todo()
        if marca not in adn_completo:
            logging.error(f"ADN no encontrado para la marca: {marca}. Abortando orden.")
            return {"status": "ERROR", "mensaje": "ADN de marca no registrado en la base de datos."}
        
        logging.info(f"Fase 1 completada: ADN de '{marca}' cargado exitosamente. Reglas estrictas aplicadas.")

        # FASE 2: Motor de Guiones (Scripting Engine)
        logging.info(f"Fase 2 en proceso: Generando estructura narrativa de alta retención...")
        datos_guion = {
            "marca": marca,
            "premisa": premisa,
            "longitud": "Extenso (4,500+ palabras)" if tipo_contenido == "Extenso" else "Medio (1,500 palabras)",
            "framework": "Análisis Lógico Deductivo" # Framework de densidad alta por defecto
        }
        
        # Construimos el prompt exacto usando tu ingeniería existente y disparamos al motor
        prompt_guion = self.mod_guiones.construir_prompt(datos_guion, adn_completo)
        resultado_guion = self.motor_ia.ejecutar_failover(prompt_guion)
        
        if "error" in resultado_guion:
            logging.error("Falla crítica en Motor de Texto (Gemini API / Tanques Vacíos).")
            return {"status": "FAILED", "fase": "Scripting", "detalle": resultado_guion["error"]}
        
        texto_generado = resultado_guion["resultado_ia"]
        logging.info("Fase 2 completada: Guion principal generado con éxito. Densidad verificada.")

        # FASE 2.1: Empaquetado (Títulos Virales y Prompt de Miniatura CTR)
        logging.info("Fase 2.1 en proceso: Generando empaquetado y Vacío de Información...")
        datos_empaquetado = {
            "marca": marca,
            "guion": texto_generado[:1500], # Usamos el primer bloque para generar ganchos
            "enfoque": "Curiosidad/Secreto",
            "estilo": "Fotorrealismo", # Alineado al estilo Documental de Guerra
            "plataforma": "YouTube"
        }
        
        prompt_empaquetado = self.mod_empaquetado.construir_prompt(datos_empaquetado, adn_completo)
        resultado_empaquetado = self.motor_ia.ejecutar_failover(prompt_empaquetado)
        empaquetado_generado = resultado_empaquetado.get("resultado_ia", "Error en empaquetado")
        
        logging.info("Fase 2.1 completada: Títulos, metadatos y conceptos visuales generados.")

        # FASE 3: Audio Synth 
        logging.info("Fase 3: Synth de Audio -> [MODULO PENDIENTE DE ENSAMBLAJE: bot_audio.py]")
        
        # FASE 4: Render Engine 
        logging.info("Fase 4: Video Compiler -> [MODULO PENDIENTE DE ENSAMBLAJE: bot_video.py]")
        
        # FASE 5: Human in the Loop (Cola de Revisión)
        logging.info(f"=== ORDEN {tarea_id} DETENIDA: REQUIERE APROBACIÓN HUMANA PARA FASE 3 ===")

        # Retornamos el paquete de datos al Frontend (Dashboard)
        return {
            "status": "PENDING_REVIEW",
            "tarea_id": tarea_id,
            "marca": marca,
            "guion_final": texto_generado,
            "empaquetado": empaquetado_generado
        }
