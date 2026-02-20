import gradio as gr
import os
import sqlite3
import hashlib
from datetime import datetime
import google.generativeai as genai

# ===================== DB =====================
conn = sqlite3.connect("prompt_history.db", check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, full_name TEXT, username TEXT UNIQUE, 
    password TEXT, blocked INTEGER DEFAULT 0)""")

admin_pass = hashlib.sha256("1978".encode()).hexdigest()
conn.execute("INSERT OR IGNORE INTO users (full_name, username, password) VALUES ('Edgar Admin','1978',?)", (admin_pass,))
conn.commit()

def hash_pass(p): return hashlib.sha256(p.encode()).hexdigest()

# ===================== LOGIN =====================
def login(u, p):
    h = hash_pass(p)
    row = conn.execute("SELECT id, full_name FROM users WHERE username=? AND password=? AND blocked=0", (u, h)).fetchone()
    return row if row else None

# ===================== HOOKS PROFESIONALES =====================
def generar_hooks(canal, tema, cantidad, nivel):
    prompt = f"""Eres Director Creativo de agencia top (campañas de 7 cifras) especializado en hooks de vídeo de exactamente 8 segundos para marcas mexicanas premium 2026.

Canal: {canal}
Tema: {tema}
Nivel de exigencia: {nivel}/10 (solo aceptas hooks que realmente tengan CTR >15% y retención >70% en los primeros 3 segundos).

Genera {cantidad} hooks de vídeo de 8 segundos con:
- Timing exacto segundo a segundo
- Visuales + ángulos de cámara + iluminación
- Sound design
- Texto en pantalla
- Prompt completo y ultra detallado para Kling AI / Runway Gen-3 / Luma
- Métricas estimadas

Sé extremadamente exigente y profesional. Solo entrega oro."""

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        return genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt).text
    except:
        return "Error: Pon tu GEMINI_API_KEY en Render → Environment Variables"

# ===================== INTERFAZ =====================
with gr.Blocks(title="Prompt Engineer Pro 2026", theme=gr.themes.Soft()) as demo:
    user_id = gr.State(None)
    full_name = gr.State("")

    with gr.Group(visible=True) as login_group:
        gr.Markdown("# 🚀 Prompt Engineer Pro 2026")
        with gr.Row():
            u = gr.Textbox(label="Usuario", value="1978")
            p = gr.Textbox(label="Contraseña", type="password", value="1978")
        btn_login = gr.Button("Entrar", variant="primary", size="large")
        msg = gr.Markdown()

    with gr.Group(visible=False) as main_group:
        gr.Markdown(f"# Bienvenido **{full_name.value}**")
        btn_logout = gr.Button("Cerrar Sesión", variant="secondary")

        with gr.Tabs():
            with gr.Tab("🔥 Hooks Virales de 8 Segundos para Vídeo"):
                canal = gr.Dropdown(["Café Orgánico Chiapas"], label="Canal", value="Café Orgánico Chiapas")
                tema = gr.Textbox(label="Tema del vídeo", lines=3)
                cantidad = gr.Slider(5, 20, value=12, label="Cantidad de hooks")
                nivel = gr.Slider(9.0, 10.0, 9.8, label="Nivel de exigencia (CTR + Retención)")
                btn = gr.Button("🚀 Generar Hooks Profesionales", variant="primary", size="large")
                output = gr.Markdown()
                btn.click(generar_hooks, [canal, tema, cantidad, nivel], output)

            with gr.Tab("👑 Panel Admin (solo 1978)"):
                gr.Markdown("Panel de administración completo aquí (usuarios, bloquear, eliminar)")

    def do_login(usuario, contra):
        datos = login(usuario, contra)
        if datos:
            return gr.update(visible=False), gr.update(visible=True), datos[0], datos[1]
        return gr.update(visible=True), gr.update(visible=False), None, ""

    btn_login.click(do_login, [u, p], [login_group, main_group, user_id, full_name])

    btn_logout.click(lambda: (gr.update(visible=True), gr.update(visible=False)), None, [login_group, main_group])

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
