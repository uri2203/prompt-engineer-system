def obtener_prompt_ingenieria(modulo_id, datos):
    """Silos de Ingeniería de Prompts. Sin mezclar contextos."""
    p1 = datos.get('p1', '')
    p2 = datos.get('p2', '')

    config = {
        "mod_1": f"[MODULO UNIVERSAL]: Actúa como {p1}. Procesa: {p2}.",
        "mod_2": f"[INGENIERÍA DE GUIONES]: Aplicar estructura de retención para {p1}. Datos: {p2}.",
        "mod_5": f"[MOTOR DE VENTAS]: Gatillo {p1}. Escala de conversión: {p2}."
    }
    
    return config.get(modulo_id, "Módulo no configurado.")
