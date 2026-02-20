import gradio as gr
import sqlite3
from datetime import datetime

# ===================== CONFIGURACIÓN =====================
conn = sqlite3.connect("prompt_history.db", check_same_thread=False)

# ===================== MÓDULO 1: GESTOR DE CANALES =====================
conn.execute("""CREATE TABLE IF NOT EXISTS canales (
    id INTEGER PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    nicho TEXT,
    estilo_comunicacion TEXT,
    publico_objetivo TEXT,
    plataformas TEXT,
    tono_voz TEXT,
    palabras_clave TEXT,
    brand_guidelines TEXT,
    notas TEXT,
    creado_en TEXT
)""")

def agregar_canal(nombre, nicho, estilo, publico, plataformas, tono, palabras_clave, guidelines, notas):
    try:
        conn.execute("""INSERT INTO canales 
            (nombre, nicho, estilo_comunicacion, publico_objetivo, plataformas, tono_voz, palabras_clave, brand_guidelines, notas, creado_en) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (nombre, nicho, estilo, publico, plataformas, tono, palabras_clave, guidelines, notas, datetime.now().isoformat()))
        conn.commit()
        return "✅ Canal agregado correctamente"
    except:
        return "❌ Error: El nombre del canal ya existe"

def obtener_canales():
    rows = conn.execute("SELECT id, nombre, nicho, estilo_comunicacion, publico_objetivo, plataformas FROM canales").fetchall()
    return [[r[0], r[1], r[2][:80] if r[2] else "", r[3][:60] if r[3] else "", r[4]] for r in rows]

def eliminar_canal(canal_id):
    conn.execute("DELETE FROM canales WHERE id=?", (canal_id,))
    conn.commit()
    return "Canal eliminado"

# ===================== INTERFAZ PRINCIPAL =====================
with gr.Blocks(title="Prompt Engineer Pro 2026 - Edgar", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 Prompt Engineer Pro 2026")
    gr.Markdown("### MÓDULO 1: Gestor de Canales (Base del Sistema)")

    with gr.Tabs():
        with gr.Tab("📋 Lista de Canales"):
            tabla = gr.DataFrame(headers=["ID", "Nombre", "Nicho", "Estilo", "Plataformas"], value=obtener_canales())
            refresh_btn = gr.Button("🔄 Actualizar Lista")

        with gr.Tab("➕ Agregar Nuevo Canal"):
            nombre = gr.Textbox(label="Nombre del Canal", placeholder="Café Orgánico Chiapas")
            nicho = gr.Textarea(label="Nicho completo", lines=3)
            estilo = gr.Textarea(label="Estilo de comunicación", lines=2)
            publico = gr.Textarea(label="Público objetivo", lines=2)
            plataformas = gr.Textbox(label="Plataformas", value="TikTok, Instagram Reels, YouTube Shorts")
            tono = gr.Textbox(label="Tono de voz")
            palabras = gr.Textarea(label="Palabras clave principales")
            guidelines = gr.Textarea(label="Brand Guidelines / Reglas de marca")
            notas = gr.Textarea(label="Notas adicionales")
            btn_agregar = gr.Button("Guardar Canal", variant="primary")
            msg = gr.Markdown()

        with gr.Tab("🗑 Eliminar Canal"):
            id_eliminar = gr.Number(label="ID del canal a eliminar", precision=0)
            btn_eliminar = gr.Button("Eliminar Canal", variant="stop")

    # Funciones
    refresh_btn.click(lambda: obtener_canales(), None, tabla)
    btn_agregar.click(agregar_canal, [nombre, nicho, estilo, publico, plataformas, tono, palabras, guidelines, notas], msg)
    btn_eliminar.click(eliminar_canal, [id_eliminar], msg)

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
