import gradio as gr
import os
import sqlite3
import hashlib
from datetime import datetime
import google.generativeai as genai
from PIL import Image as PILImage

conn = sqlite3.connect("prompt_history.db", check_same_thread=False)

# Tablas
conn.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, full_name TEXT, username TEXT UNIQUE, 
    password TEXT, blocked INTEGER DEFAULT 0, created_at TEXT)""")

conn.execute("""CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY, timestamp TEXT, tipo TEXT, canal TEXT, 
    objetivo TEXT, mejor_prompt TEXT, user_id INTEGER)""")

# Admin por defecto
admin_pass = hashlib.sha256("1978".encode()).hexdigest()
conn.execute("INSERT OR IGNORE INTO users (full_name, username, password, created_at) VALUES (?,?,?,?)",
             ("Edgar Admin", "1978", admin_pass, datetime.now().isoformat()))
conn.commit()

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def login_usuario(u, p):
    h = hash_password(p)
    row = conn.execute("SELECT id, full_name, blocked FROM users WHERE username=? AND password=?", (u, h)).fetchone()
    if row and row[2] == 0:
        return row[0], row[1], True
    return None, None, False

# ===================== MODELOS =====================
def llamar_modelo(prompt):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        return genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt).text
    except:
        return "Error con Gemini. Revisa tu API key."

# ===================== FUNCIONES =====================
def generar_hooks_video(canal, tema, cantidad, nivel):
    meta = f"""Eres Director Creativo de agencia de 7 cifras especializado en hooks de vídeo de 8 segundos para marcas premium mexicanas 2026.
Canal: {canal}
Tema: {tema}
Nivel de exigencia: {nivel}/10 (solo entrega hooks que realmente tengan CTR >15% y retención >70% en 3s).

Genera {cantidad} hooks de exactamente 8 segundos con:
- Timing segundo a segundo
- Visuales + cámara + iluminación
- Sound design
- Prompt completo para Kling/Runway/Luma
- Métricas estimadas

Sé extremadamente exigente."""
    return llamar_modelo(meta)

# ===================== INTERFAZ =====================
with gr.Blocks(title="Prompt Engineer Pro 2026 - Edgar", theme=gr.themes.Soft()) as demo:
    current_user_id = gr.State(None)
    current_full_name = gr.State("")

    with gr.Group(visible=True) as login_screen:
        gr.Markdown("# 🚀 Prompt Engineer Pro 2026\n**Acceso restringido**")
        with gr.Tabs():
            with gr.Tab("🔑 Iniciar Sesión"):
                u = gr.Textbox(label="Usuario", value="1978")
                p = gr.Textbox(label="Contraseña", type="password", value="1978")
                btn = gr.Button("Entrar", variant="primary")
                msg = gr.Markdown()
                btn.click(lambda uu,pp: (gr.update(visible=False), gr.update(visible=True), *login_usuario(uu,pp), f"✅ Bienvenido") if login_usuario(uu,pp)[2] else (gr.update(visible=True), gr.update(visible=False), None, "", "❌ Credenciales incorrectas"), [u,p], [login_screen, main_app, current_user_id, current_full_name, msg])

    with gr.Group(visible=False) as main_app:
        gr.Markdown("# 🚀 Prompt Engineer Pro 2026\n**Tu traductor personal profesional**")
        gr.Markdown(f"**Usuario conectado:** {current_full_name.value}")
        btn_logout = gr.Button("Cerrar Sesión", variant="secondary")

        with gr.Tabs():
            with gr.Tab("🔧 Prompt Engineer General"):
                gr.Markdown("Aquí va el general... (versión completa)")
            
            with gr.Tab("📹 Vídeos desde Foto del Producto"):
                gr.Markdown("Sube foto del producto aquí...")

            with gr.Tab("📦 Paquete Completo de Publicación"):
                gr.Markdown("Paquete completo aquí...")

            with gr.Tab("🔥 Hooks Virales de 8 Segundos para Vídeo"):
                canal = gr.Dropdown(["Café Orgánico Chiapas"], label="Canal", value="Café Orgánico Chiapas")
                tema = gr.Textbox(label="Tema del vídeo", lines=2)
                cant = gr.Slider(8, 20, 12, label="Cantidad de hooks")
                nivel = gr.Slider(9, 10, 9.8, label="Nivel de exigencia")
                btn_h = gr.Button("🚀 Generar Hooks de 8 Segundos (CTR >15% | Retención >70%)", variant="primary", size="large")
                output = gr.Markdown()
                btn_h.click(lambda c,t,ca,n: generar_hooks_video(c,t,ca,n), [canal,tema,cant,nivel], output)

            with gr.Tab("👑 Panel de Administrador"):
                gr.Markdown("### Solo visible para el admin (1978)")

        btn_logout.click(lambda: (gr.update(visible=True), gr.update(visible=False), None, ""), None, [login_screen, main_app, current_user_id, current_full_name])

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
