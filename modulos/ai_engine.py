# Dentro de la clase AIEngine en modulos/ai_engine.py
def _generar_prompt_especifico(self, mod_id, d, adn):
    if mod_id == 'mod_1':
        # INYECCIÓN OBLIGATORIA [cite: 11]
        filtro = ("Actúa con profesionalismo ejecutivo. Prohibido lenguaje genérico o relleno. "
                  "Sé directo y estratégico. Código completo y final[cite: 11, 18].")
        
        # ESTRUCTURA INMUTABLE [cite: 13, 14, 15, 16, 19]
        return (f"[IDENTIDAD]: Actúa como un {d.get('rol')}[cite: 14].\n"
                f"[CONTEXTO]: Base inamovible: {d.get('contexto')}[cite: 15].\n"
                f"[TAREA]: {d.get('texto')}[cite: 16].\n"
                f"[RESTRICCIONES]: {filtro}[cite: 17].\n"
                f"[FORMATO DE SALIDA]: {d.get('formato')}[cite: 19].")
    # ... resto de lógica de módulos
