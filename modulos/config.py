def obtener_prompt_base(modulo, datos):
    """Encapsula la lógica de los prompts en un archivo independiente."""
    prompts = {
        "mod_1_universal": f"[IDENTIDAD]: Actúa como un {datos.get('rol')}. [TAREA]: {datos.get('peticion')}.",
        "mod_2_guiones": f"[IDENTIDAD]: Guionista de {datos.get('arquetipo_marca')}. [TAREA]: Guion de {datos.get('longitud')}.",
        "mod_3_hooks": f"[SECUENCIA]: Bloque {datos.get('num_bloque')}. Duración: {datos.get('duracion')}.",
        "mod_4_empaquetado": f"[ESTRATEGIA]: CTR para {datos.get('plataforma')}. Arte: {datos.get('estilo_visual')}.",
        "mod_5_ugc_ventas": f"[VENTAS]: Gatillo {datos.get('gatillo_ventas')}. Avatar: {datos.get('perfil_avatar')}."
    }
    return prompts.get(modulo, "Error: Módulo no configurado.")
