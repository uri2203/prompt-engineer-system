import os
import re
import logging
import asyncio
import edge_tts

# Telemetría de consola específica para el silo de audio
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [AUDIO_SYNTH] - %(levelname)s - %(message)s')

class AudioSynthEngine:
    def __init__(self):
        logging.info("Inicializando Motor de Síntesis de Voz Neuronal (Mockup Tier)")
        
        # Creamos el directorio temporal donde se guardarán los .mp3
        self.output_dir = os.path.join(os.getcwd(), "workspace_temp", "audio")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # MATRIZ DE ASIGNACIÓN NEURONAL POR MARCA
        # Estas voces gratuitas simulan la calidad de ElevenLabs para pruebas End-to-End
        self.voces_marcas = {
            "La Viuda": "es-MX-JorgeNeural",       # Voz grave, seria, documental de misterio
            "Monkygraff": "es-ES-AlvaroNeural",    # Voz de noticiero, fotoperiodismo
            "TuIALista": "es-MX-DaliaNeural",      # Voz corporativa y tecnológica
            "Ezzenshop": "es-MX-CecilioNeural",    # Voz dinámica, hype urbano
            "Yayika Digital": "es-MX-DaliaNeural", # Voz femenina, empática y suave
            "Yayika Apparel": "es-MX-CecilioNeural",# Voz rápida para retención en TikTok
            "default": "es-MX-JorgeNeural"
        }

    def limpiar_texto_guion(self, texto):
        """
        Filtro de purga de metadatos.
        Elimina notas de director, corchetes y asteriscos que la IA suele generar 
        (Ej: "[Música tensa]" o "*susurrando*") para que el motor TTS no las lea en voz alta.
        """
        texto_limpio = re.sub(r'\[.*?\]', '', texto) # Purga [corchetes]
        texto_limpio = re.sub(r'\*.*?\*', '', texto) # Purga *asteriscos*
        texto_limpio = re.sub(r'\(.*?\)', '', texto) # Purga (paréntesis)
        
        # Normalización de espaciado
        texto_limpio = re.sub(r'\n+', '\n', texto_limpio).strip()
        return texto_limpio

    async def _generar_async(self, texto, voz, ruta_salida):
        """Núcleo asíncrono de compilación de audio"""
        communicate = edge_tts.Communicate(texto, voz)
        await communicate.save(ruta_salida)

    def generar_audio_base(self, texto, marca, tarea_id):
        """
        Punto de entrada síncrono para el Orquestador Pinpinela.
        Recibe el texto crudo de la Fase 2, lo limpia, selecciona la voz del ADN y escupe el archivo .mp3.
        """
        logging.info(f"Iniciando renderizado de audio para Orden: {tarea_id} | Marca: {marca}")
        
        # 1. Purga de guion
        texto_procesado = self.limpiar_texto_guion(texto)
        if not texto_procesado:
            logging.error("Fallo de purga: El texto resultante está vacío.")
            return {"status": "ERROR", "mensaje": "Texto de audio vacío post-purga."}

        # 2. Selección de ADN Vocal
        voz_seleccionada = self.voces_marcas.get(marca, self.voces_marcas["default"])
        nombre_archivo = f"audio_{tarea_id}.mp3"
        ruta_absoluta = os.path.join(self.output_dir, nombre_archivo)
        
        # 3. Renderizado y guardado en disco
        try:
            # Envolvemos el motor asíncrono para que no rompa el hilo de Flask
            asyncio.run(self._generar_async(texto_procesado, voz_seleccionada, ruta_absoluta))
            
            logging.info(f"Audio renderizado con éxito en disco local: {ruta_absoluta}")
            return {
                "status": "SUCCESS", 
                "ruta_audio": ruta_absoluta,
                "voz_usada": voz_seleccionada
            }
            
        except Exception as e:
            logging.error(f"Fallo crítico en el motor TTS: {str(e)}")
            return {"status": "ERROR", "mensaje": str(e)}
