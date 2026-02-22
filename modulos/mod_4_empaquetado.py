class EmpaquetadoContenido:
    def construir_prompt(self, d, adn_completo):
        adn = adn_completo.get(d.get('marca'), {})
        # [cite: 120] Vacío de información
        # [cite: 122] Resolución estricta 16:9
        return (f"[IDENTIDAD]: Eres un estratega de contenido viral y experto en SEO audiovisual.\n"
                f"Trabajas bajo los parámetros de: {adn.get('identidad')}.\n"
                f"[CONTEXTO]: Analiza el siguiente contenido: {d.get('guion')}.\n"
                f"[TAREA]: Desarrolla el paquete de publicación para {d.get('plataforma')} maximizando el CTR.\n"
                f"[RESTRICCIONES]: Títulos: Prohibido resumir la noticia. Utiliza estrictamente la estrategia de 'Vacío de Información'. Frases cortas de intriga pura que no revelen la conclusión. Enfoque: {d.get('enfoque')}.\n"
                f"Imágenes: El prompt de imagen debe solicitar estrictamente una resolución de 1920x1080 píxeles (relación de aspecto 16:9). El estilo visual debe ser rigurosamente: {d.get('estilo')}. Prohibido generar formatos cuadrados. {adn.get('reglas_duras')}.\n"
                f"Cumplir normativas de monetización.\n"
                f"[FORMATO DE SALIDA ESTRICTO]: Entrega la respuesta estructurada así:\n"
                f"TÍTULOS: (5 opciones viables).\n"
                f"PROMPT DE MINIATURA (En inglés): (1 instrucción altamente detallada para un modelo de generación de imágenes, priorizando composición e iluminación, asegurando el parámetro 1920x1080 y 16:9).\n"
                f"DESCRIPCIÓN Y TAGS: (Párrafo SEO optimizado y lista de etiquetas separadas por comas).")
