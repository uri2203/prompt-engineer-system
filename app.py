import gradio as gr
import os
import google.generativeai as genai

# ===================== MÓDULO 1: HOOKS VIRALES DE 8 SEGUNDOS =====================
def generar_hooks_8s(canal, tema, cantidad, nivel):
    prompt = f"""Eres Director Creativo de agencia premium especializada en short-form video (TikTok/Reels/Shorts México 2026).

Canal: {canal}
Tema del vídeo: {tema}
Nivel de exigencia: {nivel}/10 (solo entregas hooks que realmente tengan CTR >15% y retención >70% en los primeros 3 segundos. Rechazas todo lo mediocre).

Genera exactamente {cantidad} hooks de vídeo de 8 segundos con:

Para cada hook incluye:
- Título del hook
- Script con timing exacto (0-3s | 3-6s | 6-8s)
- Visuales + ángulos de cámara + iluminación + B-roll
- Sound design y recomendaciones de voz
- Prompt completo y ultra-detallado para generar el clip de 8s en Kling AI / Runway Gen-3 / Luma
- Métricas estimadas (CTR, retención 3s, probabilidad full watch)

Sé extremadamente exigente y profesional. Solo entrega material de calidad agencia internacional."""

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return response.text
    except:
        return "❌ Error: Agrega tu GEMINI_API_KEY en Render → Environment Variables"

# ===================== INTERFAZ (solo este módulo por ahora) =====================
with gr.Blocks(title="Prompt Engineer Pro 2026 - Edgar", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 Prompt Engineer Pro 2026")
    gr.Markdown("**MÓDULO 1: Hooks Virales de 8 Segundos para Vídeo**")

    with gr.Row():
        canal = gr.Dropdown(["Café Orgánico Chiapas"], label="Canal", value="Café Orgánico Chiapas")
        tema = gr.Textbox(label="Tema del vídeo", lines=2, placeholder="Ej: Beneficios del café orgánico de Chiapas vs industrial")
    
    with gr.Row():
        cantidad = gr.Slider(5, 20, value=12, label="Cantidad de hooks")
        nivel = gr.Slider(9.0, 10.0, value=9.8, label="Nivel de exigencia (CTR + Retención)")

    btn = gr.Button("🚀 Generar Hooks Profesionales de 8 Segundos", variant="primary", size="large")
    output = gr.Markdown()

    btn.click(generar_hooks_8s, [canal, tema, cantidad, nivel], output)

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
