class TraductorUniversal:
    def construir_prompt(self, d):
        # Reglas de Traducción Interna inyectadas directamente aquí
        return (f"[IDENTIDAD]: Actúa como un {d.get('rol')}.\n"
                f"[CONTEXTO]: {d.get('contexto')}.\n"
                f"[TAREA]: {d.get('texto')}.\n"
                f"[RESTRICCIONES]: Actúa con un nivel de profesionalismo ejecutivo y experto. Prohibido el lenguaje genérico, el relleno y las obviedades. Sé directo, estratégico y de alto nivel. Si se requiere código, entrégalo completo y final, sin fragmentos sueltos.\n"
                f"[FORMATO DE SALIDA]: Entrega el resultado estrictamente como {d.get('formato')}.")
