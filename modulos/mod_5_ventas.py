class MotorVentasUGC:
    def construir_prompt(self, d):
        gatillo = d.get('gatillo', '')
        instruccion_gatillo = ""
        
        if "FOMO" in gatillo:
            instruccion_gatillo = "Aplica el sesgo de aversión a la pérdida. El guion debe generar ansiedad de oportunidad: el producto se agota rápido, pertenece a un lote exclusivo y no tenerlo significa quedarse fuera de la tendencia. Usa lenguaje de urgencia extrema."
        elif "Autoridad" in gatillo:
            instruccion_gatillo = "Ataca el dolor de la ineficiencia. Demuestra cómo este producto digital o de software elimina fricciones al instante. Lenguaje directo, corporativo y basado en ROI (Retorno de Inversión)."
        else:
            instruccion_gatillo = "Aplica el sesgo seleccionado atacando el dolor del cliente y forzando la acción."

        return (f"[ESTRATEGIA DE CAMPAÑA Y VENTAS]: Eres un Media Buyer Senior y experto en Neuro-Marketing. Desarrolla esta secuencia publicitaria 9:16.\n"
                f"[GATILLO PSICOLÓGICO]: Tu único objetivo es la conversión inmediata. Aplica la estrategia de: {gatillo}. {instruccion_gatillo}\n"
                f"Prohibido vender características. Vende la transformación. El hook debe señalar un problema doloroso o un deseo reprimido, la retención debe agitar ese dolor, y el Call to Action (CTA) debe exigir una acción inmediata.\n"
                f"[SECUENCIA]: Bloque {d.get('bloque')}. Duración: {d.get('duracion')}.\n"
                f"[FASE 1: DISEÑO VISUAL]: Modalidad: {d.get('modalidad')}. Integra el producto de referencia manteniendo el 100% de su fidelidad y logotipos.\n"
                f"[FASE 2: ACCIÓN Y FÍSICA]: Render en 4K fotorrealista. Física inquebrantable. Sin deformaciones corporales ni del producto.\n"
                f"[FORMATO DE SALIDA ESTRICTO]:\n"
                f"[PROMPT VISUAL - VIDEO]: (Instrucción técnica de cámara y acción para IA).\n"
                f"[GUION DE VENTA]: (Texto exacto de locución respetando el límite estricto de palabras según la duración).")
