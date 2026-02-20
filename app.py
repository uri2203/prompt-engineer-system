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

def hash_pass(p): return hashlib.sha256(p.encode()).hexdigest()

def login(u, p):
    row = conn.execute("SELECT id, full_name FROM users WHERE username=? AND password=? AND blocked=0", 
                       (u, hash_pass(p))).fetchone()
    return row if row else None

def generar_hooks(canal, tema, cantidad, nivel):
    prompt = f"""Eres Director Creativo de agencia premium especializado en hooks de vídeo de 8 segundos para marcas mexicanas 2026.

Canal: {canal}
Tema: {tema}
Nivel de exigencia: {nivel}/10 (solo entrega si CTR >15% y retención 3s >70%).

Genera {cantidad} hooks profesionales de exactamente 8 segundos con:
- Timing segundo a segundo
- Visuales, cámara, iluminación
- Sound design
- Prompt completo para Kling/Runway/Luma
- Métricas estimadas

Sé extremadamente exigente."""

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        return genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt).text
    except:
        return "Error: Agrega tu GEMINI_API_KEY en Render → Environment Variables"

with gr.Blocks(title="Prompt Engineer Pro 2026 - Edgar", theme=gr.themes.Soft()) as demo:
    logged = gr.State(False)
    name = gr.State("")

    with gr.Group(visible=True) as login_screen:
        gr.Markdown("# 🚀 Prompt Engineer Pro 2026")
        u = gr.Textbox(label="Usuario", value="1978")
        p = gr.Textbox(label="Contraseña", type="password", value="1978")
        btn = gr.Button("Entrar", variant="primary")
        msg = gr.Markdown()

    with gr.Group(visible=False) as main_screen:
        gr.Markdown(f"# Bienvenido **{name.value}**")
        logout = gr.Button("Cerrar Sesión")

        with gr.Tabs():
            with gr.Tab("🔥 Hooks Virales de 8 Segundos para Vídeo"):
                canal = gr.Dropdown(["Café Orgánico Chiapas"], label="Canal", value="Café Orgánico Chiapas")
                tema = gr.Textbox(label="Tema del vídeo", lines=2)
                cant = gr.Slider(8, 20, 12, label="Cantidad")
                nivel = gr.Slider(9.0, 10.0, 9.8, label="Nivel de exigencia")
                btn_h = gr.Button("🚀 Generar Hooks Profesionales", variant="primary", size="large")
                out = gr.Markdown()
                btn_h.click(generar_hooks, [canal, tema, cant, nivel], out)

            with gr.Tab("📹 Vídeos desde Foto"):
                gr.Markdown("Sube foto del producto aquí (versión completa)")

            with gr.Tab("📦 Paquete Completo de Publicación"):
                gr.Markdown("Paquete completo aquí")

            with gr.Tab("👑 Panel Admin"):
                gr.Markdown("Solo visible para admin")

    def do_login(usuario, contra):
        datos = login(usuario, contra)
        if datos:
            return gr.update(visible=False), gr.update(visible=True), datos[1]
        return gr.update(visible=True), gr.update(visible=False), ""

    btn.click(do_login, [u, p], [login_screen, main_screen, name])
    logout.click(lambda: (gr.update(visible=True), gr.update(visible=False)), None, [login_screen, main_screen])

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
