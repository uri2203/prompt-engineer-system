class IngenieriaGuiones:
    def construir_prompt(self, d, adn_completo):
        adn = adn_completo.get(d.get('marca'), {})
        return (f"[IDENTIDAD Y TONO]: Eres un guionista experto en retención. Escribe estrictamente bajo este arquetipo: {adn.get('identidad')}.\n"
                f"[CONTEXTO DE MARCA]: Respeta los siguientes límites inquebrantables: {adn.get('reglas_duras')}.\n"
                f"[TAREA]: Desarrolla un guion de {d.get('longitud')} basado en esta premisa: {d.get('premisa')}.\n"
                f"[ESTRUCTURA]: Aplica el framework de {d.get('framework')}. Prohibido iniciar con saludos, introducciones genéricas o resúmenes de lo que se va a tratar. La primera línea debe atacar directamente la curiosidad intelectual.\n"
                f"[FORMATO DE SALIDA]: Entrega el guion en un formato limpio, dividido por bloques visuales lógicos.")
