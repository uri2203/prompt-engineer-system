import os
import json
import re
import logging

class ComplianceEngine:
    def __init__(self):
        # La Bóveda de Leyes: Almacenamiento Local
        self.leyes_path = os.path.join(os.path.dirname(__file__), 'leyes_plataformas.json')
        self.leyes = self._cargar_o_crear_leyes()

    def _cargar_o_crear_leyes(self):
        """
        Carga la 'Constitución' del sistema. Si no existe, la crea con las directrices estrictas
        de monetización y las reglas específicas de las marcas.
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
        """Genera el archivo JSON inquebrantable inicial."""
        leyes_base = {
            "plataformas": {
                "youtube": {
                    "palabras_prohibidas_estrictas": ["suicidio", "violación", "terrorismo", "gore", "asesinato explícito", "masacre"],
                    "regla_general": "Cero tolerancia a violencia gráfica no contextualizada o lenguaje de odio explícito."
                },
                "meta": {
                    "palabras_prohibidas_estrictas": ["muerte real", "trata", "abuso"],
                    "regla_general": "Restricción severa en temas sensibles sin valor documental o educativo."
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
        
        # Guardar en disco para que sea auditable y modificable externamente
        try:
            with open(self.leyes_path, 'w', encoding='utf-8') as f:
                json.dump(leyes_base, f, indent=4)
        except Exception as e:
            logging.error(f"[COMPLIANCE] No se pudo crear el archivo de leyes: {e}")
            
        return leyes_base

    def _auditar_texto_crudo(self, guion, marca):
        """
        Paso C: Interceptor. Escanea el guion crudo contra las leyes.
        Retorna (True, "Aprobado") o (False, "Motivo de rechazo").
        """
        texto_limpio = guion.lower()
        
        # 1. Filtro General (Todas las plataformas)
        prohibidas_yt = self.leyes["plataformas"]["youtube"]["palabras_prohibidas_estrictas"]
        prohibidas_meta = self.leyes["plataformas"]["meta"]["palabras_prohibidas_estrictas"]
        todas_prohibidas = prohibidas_yt + prohibidas_meta

        for palabra in todas_prohibidas:
            if re.search(r'\b' + re.escape(palabra) + r'\b', texto_limpio):
                return False, f"Se detectó un término crítico para desmonetización: '{palabra}'."

        # 2. Filtro de Silo Específico (Por Marca)
        if marca in self.leyes["marcas"]:
            restricciones = self.leyes["marcas"][marca]["restricciones"]
            # Búsqueda heurística básica para el filtro local
            for restriccion in restricciones:
                palabras_clave = [p for p in restriccion.split() if len(p) > 3]
                coincidencias = sum(1 for p in palabras_clave if p in texto_limpio)
                # Si coinciden más de 1 palabra clave de la restricción, levantamos bandera
                if coincidencias >= 2:
                    estrategia = self.leyes["marcas"][marca]["estrategia_evasion"]
                    return False, f"Se violó la directriz de la marca ({marca}) por posible: '{restriccion}'. DEBE APLICAR: {estrategia}."

        return True, "100% Limpio y Monetizable"

    def blindar_guion(self, ai_engine_instancia, marca, contexto, peticion, longitud):
        """
        El ciclo de guerra: Fuerza a la IA a reescribir si el guion es peligroso.
        """
        intentos_maximos = 3
        intento_actual = 1
        prompt_corrector = ""

        while intento_actual <= intentos_maximos:
            peticion_enviada = peticion + prompt_corrector
            
            # Paso A: Se solicita el guion al motor de IA
            guion_crudo = ai_engine_instancia.generar_guion(marca, contexto, peticion_enviada, longitud)
            
            # Paso B: Pasa por el Motor de Cumplimiento
            es_seguro, reporte = self._auditar_texto_crudo(guion_crudo, marca)
            
            if es_seguro:
                # Paso D: Sale limpio
                if intento_actual > 1:
                    logging.info(f"[COMPLIANCE] Guion rescatado en el intento {intento_actual}.")
                return guion_crudo
            
            # Si no es seguro, preparamos la orden de reescritura
            logging.warning(f"[COMPLIANCE] Guion bloqueado. Motivo: {reporte}. Forzando reescritura (Intento {intento_actual}/{intentos_maximos}).")
            estrategia_evasion = self.leyes["marcas"].get(marca, {}).get("estrategia_evasion", "Usa sinónimos neutros y elimina cualquier violencia gráfica.")
            
            prompt_corrector = f"\n\n[DIRECTRIZ DE EMERGENCIA DEL MOTOR DE CUMPLIMIENTO]: Tu intento anterior fue RECHAZADO por el siguiente motivo: {reporte}. DEBES REESCRIBIR TODO EL TEXTO aplicando estrictamente esta regla: {estrategia_evasion}."
            
            intento_actual += 1

        # Si falla las 3 veces, el sistema prefiere abortar antes que arriesgar el canal.
        return "[ERROR DE COMPLIANCE] Operación abortada. La IA no logró generar un guion seguro para la monetización después de 3 intentos. Revise la petición inicial."
