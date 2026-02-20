import gradio as gr
import os
import sqlite3
import hashlib
import google.generativeai as genai

conn = sqlite3.connect("prompt_history.db", check_same_thread=False)

conn.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, full_name TEXT, username TEXT UNIQUE, 
    password TEXT, blocked INTEGER DEFAULT 0)""")

admin_pass = hashlib.sha256("1978".encode()).hexdigest()
conn.execute("INSERT OR IGNORE INTO users (full_name, username, password) VALUES ('Edgar Admin','1978',?)", (admin_pass,))
conn.commit()

def hash_pass(p): 
    return hashlib.sha256(p.encode()).hexdigest()

def login(u, p):
    row = conn.execute("SELECT id, full_name FROM users WHERE username=? AND password=? AND blocked=0", 
                       (u, hash_pass(p))).fetchone()
    return row if row else None

def generar_hooks_profesionales(canal, tema, cantidad, nivel):
    prompt = f"""Eres un Director Creativo de agencia de marketing de alto nivel (campañas de 7 cifras) especializado en hooks de vídeo corto para marcas premium mexicanas en 2026.

Canal: {canal}
Tema del vídeo: {tema}
Nivel de exigencia: {nivel}/10

Genera {cantidad} hooks de exactamente 8 segundos que realmente funcionen (CTR >15% y retención >70% en los primeros 3 segundos).

Para cada hook incluye:
- Título del hook
- Script con timing exacto (0-3s | 3-6s | 6-8s)
- Visuales y cámara
- Sound design
- Prompt completo y ultra-detallado para generar el clip en Kling AI / Runway / Luma
- Métricas estimadas

Sé extremadamente exigente. Solo entrega material de calidad profesional."""

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error con Gemini: {str(e)}\n\nPon tu GEMINI_API_KEY en Render → Environment Variables"

with gr.Blocks(title="Prompt Engineer Pro 2026 - Edgar", theme=gr.themes.Soft()) as demo:
    logged_in = gr.State(False)
    full_name = gr.State("")

    with gr.Group(visible=True) as login_screen:
        gr.Markdown("# 🚀 Prompt Engineer Pro 2026")
        gr.Markdown("**Acceso restringido**")
        username = gr.Textbox(label="Usuario", value="1978")
        password = gr.Textbox(label="Contraseña", type="password", value="1978")
        login_btn = gr.Button("Iniciar Sesión", variant="primary", size="large")
        status = gr.Markdown()

    with gr.Group(visible=False) as main_screen:
        gr.Markdown("# 🚀 Prompt Engineer Pro 2026")
        gr.Markdown(f"**Bienvenido, {full_name.value}**")
        logout_btn = gr.Button("Cerrar Sesión", variant="secondary")

        with gr.Tabs():
            with gr.Tab("🔥 Hooks Virales de 8 Segundos para Vídeo"):
                canal = gr.Dropdown(["Café Orgánico Chiapas"], label="Canal", value="Café Orgánico Chiapas")
                tema = gr.Textbox(label="Tema del vídeo", placeholder="Ej: Beneficios del café orgánico vs industrial", lines=2)
                cantidad = gr.Slider(5, 20, value=12, label="Cantidad de hooks")
                nivel = gr.Slider(9.0, 10.0, 9.8, label="Nivel de exigencia")
                btn_generar = gr.Button("🚀 Generar Hooks Profesionales (CTR >15% | Retención >70%)", variant="primary", size="large")
                resultado = gr.Markdown()

                btn_generar.click(generar_hooks_profesionales, [canal, tema, cantidad, nivel], resultado)

    def intentar_login(u, p):
        datos = login(u, p)
        if datos:
            return gr.update(visible=False), gr.update(visible=True), datos[1]
        return gr.update(visible=True), gr.update(visible=False), ""

    login_btn.click(intentar_login, [username, password], [login_screen, main_screen, full_name])
    logout_btn.click(lambda: (gr.update(visible=True), gr.update(visible=False)), None, [login_screen, main_screen])

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
