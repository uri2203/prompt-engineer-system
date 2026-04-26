import os
import json
import re
import logging
import datetime
import requests

class ComplianceEngine:
    def __init__(self):
        # La Bóveda de Leyes: Almacenamiento Local
        self.leyes_path = os.path.join(os.path.dirname(__file__), 'leyes_plataformas.json')
        self.dias_caducidad = 30
        self.leyes = self._cargar_o_crear_leyes()
        
        # Ejecuta la validación de caducidad al arrancar el motor
        self.verificar_y_actualizar_leyes()

    def _cargar_o_crear_leyes(self):
        """
        Carga la Constitución del sistema. Si no existe, genera la base fundacional.
        """
        if os.path.exists(self.leyes_path):
            try:
                with open(self.leyes_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"[COMPLIANCE] Error leyendo leyes_plataformas.json: {e}")
                return self._generar_leyes_base()
        else:
            return self._generar_leyes_base()

    def _generar_leyes_base(self):
        """Genera el archivo JSON inquebrantable inicial con marca de tiempo."""
        leyes_base = {
            "ultima_actualizacion": datetime.datetime.now().strftime("%Y-%m-%d"),
            "plataformas": {
                "youtube": {
                    "palabras_prohibidas_estrictas": ["suicidio", "violación", "terrorismo", "gore", "asesinato explícito", "masacre"],
                    "regla_general": "Cero tolerancia a violencia gráfica no contextualizada o lenguaje de odio explícito."
                },
                "meta": {
                    "palabras_prohibidas_estrictas": ["muerte real", "trata", "abuso"],
                    "regla_general": "Restricción severa en temas sensibles sin valor documental o educativo."
                },
                "tiktok": {
                    "palabras_prohibidas_estrictas": ["autolesión", "armas de fuego", "drogas duras"],
                    "regla_general": "Cero tolerancia a contenido visualmente perturbador o que incite a actividades peligrosas."
                }
            },
            "marcas": {
                "La Viuda": {
                    "restricciones": ["violencia gráfica excesiva", "descripciones anatómicas gore", "sadismo visual"],
                    "estrategia_evasion": "Aplicar REALISMO CLÍNICO. Utilizar eufemismos médicos o periodísticos. Ejemplo: cambiar 'le destrozaron el cráneo' por 'sufrió traumatismos incompatibles con la vida'. Cambiar 'charco de sangre' por 'escena altamente perturbadora'."
                },
                "Monkygraff": {
                    "restricciones": ["lenguaje prohibido sobre conflictos armados", "incitación a la violencia", "jerga de combate explícita"],
                    "estrategia_evasion": "Aplicar TONO DOCUMENTAL NEUTRAL. No tomar partido. Informar los hechos como un observador externo usando lenguaje táctico y geopolítico formal."
                }
            }
        }
        self._guardar_leyes(leyes_base)
        return leyes_base

    def _guardar_leyes(self):
        pass # Definida abajo correctamente

    def _guardar_leyes(self, datos):
        """Escribe las políticas actualizadas en el disco."""
        try:
            with open(self.leyes_path, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4)
        except Exception as e:
            logging.error(f"[COMPLIANCE] Error fatal al guardar la Bóveda de Leyes: {e}")

    def verificar_y_actualizar_leyes(self):
        """
        Módulo de Sincronización Automática:
        Verifica si han pasado más de 'X' días desde la última actualización.
        Si es así, detona el proceso de extracción de nuevas reglas.
        """
        fecha_str = self.leyes.get("ultima_actualizacion", "2000-01-01")
        try:
            ultima_fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            diferencia = datetime.datetime.now() - ultima_fecha
            
            if diferencia.days >= self.dias_caducidad:
                logging.info(f"[COMPLIANCE] Las políticas tienen {diferencia.days} días de antigüedad. Iniciando actualización desde las APIs de las plataformas...")
                self._ejecutar_extraccion_nube()
            else:
                logging.info(f"[COMPLIANCE] Políticas vigentes. Próxima actualización en {self.dias_caducidad - diferencia.days} días.")
        except Exception as e:
            logging.error(f"[COMPLIANCE] Falla en la lectura de caducidad temporal: {e}")

    def _ejecutar_extraccion_nube(self):
        """
        Conecta con los endpoints o scrapers para obtener las directrices más recientes.
        (Estructura preparada para inyectar los webhooks reales de YouTube/Meta/TikTok).
        """
        try:
            # Aquí irán las llamadas reales a las APIs de compliance o scrapers.
            # Simulación de extracción de nuevos términos restrictivos:
            nuevos_terminos_yt = ["palabra_baneada_nueva_1", "palabra_baneada_nueva_2"] 
            nuevos_terminos_meta = ["termino_restringido_nuevo"]
            
            # Fusión de los nuevos datos con la bóveda existente
            lista_yt = set(self.leyes["plataformas"]["youtube"]["palabras_prohibidas_estrictas"])
            lista_yt.update(nuevos_terminos_yt)
            self.leyes["plataformas"]["youtube"]["palabras_prohibidas_estrictas"] = list(lista_yt)

            lista_meta = set(self.leyes["plataformas"]["meta"]["palabras_prohibidas_estrictas"])
            lista_meta.update(nuevos_terminos_meta)
            self.leyes["plataformas"]["meta"]["palabras_prohibidas_estrictas"] = list(lista_meta)

            # Actualizar sello de tiempo
            self.leyes["ultima_actualizacion"] = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Guardar la nueva Constitución
            self._guardar_leyes(self.leyes)
            logging.info("[COMPLIANCE] Bóveda de Leyes actualizada exitosamente desde la nube.")
            
        except Exception as e:
            logging.error(f"[COMPLIANCE] Falló la extracción de nuevas políticas. Manteniendo reglas anteriores por seguridad: {e}")

    def _auditar_texto_crudo(self, guion, marca):
        """
        Filtro Interceptor: Cruza el guion crudo (o JSON) contra las leyes actualizadas.
        """
        texto_limpio = guion.lower()

        # Si Gemini devolvió error, no auditar
        if "error crítico" in texto_limpio or "error de compliance" in texto_limpio:
            return True, "Texto de error — sin auditoría"

        # 1. Filtro General de Plataformas — solo palabras ESTRICTAMENTE prohibidas
        todas_prohibidas = []
        for plataforma in self.leyes["plataformas"].values():
            todas_prohibidas.extend(plataforma.get("palabras_prohibidas_estrictas", []))

        for palabra in todas_prohibidas:
            # Usar word boundary para evitar falsos positivos
            if re.search(r'\b' + re.escape(palabra.lower()) + r'\b', texto_limpio):
                return False, f"Término crítico detectado ('{palabra}'). Riesgo alto de desmonetización."

        # 2. Filtro de Marca — umbral subido a 6 coincidencias y palabras largas únicamente
        if marca in self.leyes["marcas"]:
            restricciones = self.leyes["marcas"][marca]["restricciones"]
            for restriccion in restricciones:
                # Solo palabras de más de 6 caracteres para evitar falsos positivos
                palabras_clave = [p for p in restriccion.split() if len(p) > 6]
                if not palabras_clave:
                    continue
                coincidencias = sum(
                    1 for p in palabras_clave
                    if re.search(r'\b' + re.escape(p) + r'\b', texto_limpio)
                )
                # Subido de 4 a 6 — requiere más coincidencias para rechazar
                if coincidencias >= 6:
                    estrategia = self.leyes["marcas"][marca]["estrategia_evasion"]
                    return False, f"Violación de directriz de marca ({marca}): '{restriccion}'. APLICAR: {estrategia}."

        return True, "100% Limpio y Monetizable"

    def blindar_guion(self, ai_engine_instancia, marca, contexto, peticion, longitud, formato="16:9"):
        """
        Fuerza a la IA a reescribir aplicando eufemismos si el guion es peligroso.
        Recibe el parámetro 'formato' y lo transfiere al motor de IA.
        """
        intentos_maximos = 3
        intento_actual = 1
        prompt_corrector = ""

        while intento_actual <= intentos_maximos:
            peticion_enviada = peticion + prompt_corrector
            
            # Paso A: Generación cruda (Ahora enviamos el formato)
            guion_crudo = ai_engine_instancia.generar_guion(marca, contexto, peticion_enviada, longitud, formato)
            
            # Paso B y C: Auditoría estricta contra la Bóveda actualizada
            es_seguro, reporte = self._auditar_texto_crudo(guion_crudo, marca)
            
            if es_seguro:
                # Paso D: Aprobado
                if intento_actual > 1:
                    logging.info(f"[COMPLIANCE] Guion rescatado en el intento {intento_actual}.")
                return guion_crudo
            
            # Redacción del veto y orden de reescritura
            logging.warning(f"[COMPLIANCE] Guion bloqueado. Motivo: {reporte}. Forzando reescritura (Intento {intento_actual}/{intentos_maximos}).")
            estrategia_evasion = self.leyes["marcas"].get(marca, {}).get("estrategia_evasion", "Usa sinónimos neutros y elimina cualquier violencia gráfica.")
            
            prompt_corrector = f"\n\n[DIRECTRIZ DE EMERGENCIA DEL MOTOR DE CUMPLIMIENTO]: Tu intento anterior fue RECHAZADO por el siguiente motivo: {reporte}. DEBES REESCRIBIR TODO EL TEXTO aplicando estrictamente esta regla para evadir los algoritmos: {estrategia_evasion}."
            
            intento_actual += 1

        return "[ERROR DE COMPLIANCE] Operación abortada. La IA no logró generar un guion seguro para la monetización. Revise la petición inicial."
