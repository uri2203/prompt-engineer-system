class GeneradorHooks:
    def construir_prompt(self, d, adn_completo):
        adn = adn_completo.get(d.get('marca'), {})
        memoria = d.get('memoria', '')
        bloque = d.get('bloque', 'Bloque 1 (Inicio)')
        duracion = d.get('duracion', '4 segundos')

        # [cite: 98] Contexto de memoria para continuidad visual
        contexto_memoria = f"El bloque anterior terminó con esta imagen y este audio: '{memoria}'. Mantén continuidad absoluta de personajes y voz." if bloque != 'Bloque 1 (Inicio)' else "Este es el segundo 0 del video."
        
        # [cite: 91, 92] Algoritmo matemático de locución
        limite_palabras = "10 palabras máximo." if duracion == "4 segundos" else ("entre 18 y 22 palabras." if duracion == "8 segundos" else "límite estricto asignado.")

        # [cite: 101, 102] Formato de salida estricto en 2 bloques
        return (f"[IDENTIDAD]: Eres un director de cinematografía generativa y experto en retención. Tono: {adn.get('identidad')}.\n"
                f"[SECUENCIA]: Este es el {bloque} de la secuencia. Su duración estricta es de {duracion}.\n"
                f"[CONTEXTO DE MEMORIA]: {contexto_memoria}\n"
                f"[TAREA]: Desarrolla este fragmento basado en: {d.get('premisa')}.\n"
                f"[RESTRICCIONES]: {adn.get('reglas_duras')}. El texto de locución debe tener matemáticamente el límite de palabras asignado: {limite_palabras}. Aplica disonancia cognitiva.\n"
                f"[FORMATO DE SALIDA ESTRICTO]: Entrega el resultado en dos bloques exactos:\n"
                f"[AUDIO-VOZ]: (Texto exacto para el generador de voz, respetando el límite de palabras).\n"
                f"[PROMPT-VIDEO]: (Instrucción técnica en inglés, optimizada para IA de video, describiendo sujeto, cámara y continuidad visual. Sin cortes de cámara dentro de este bloque).")
