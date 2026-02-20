import gradio as gr
import os
import sqlite3
import hashlib
from datetime import datetime

conn = sqlite3.connect("prompt_history.db", check_same_thread=False)

conn.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    full_name TEXT,
    username TEXT UNIQUE,
    password TEXT,
    blocked INTEGER DEFAULT 0,
    created_at TEXT
)""")

admin_pass = hashlib.sha256("1978".encode()).hexdigest()
conn.execute("INSERT OR IGNORE INTO users (full_name, username, password, created_at) VALUES (?, ?, ?, ?)",
             ("Edgar Admin", "1978", admin_pass, datetime.now().isoformat()))
conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def registrar_usuario(full_name, username, password):
    try:
        hashed = hash_password(password)
        conn.execute("INSERT INTO users (full_name, username, password, created_at) VALUES (?, ?, ?, ?)",
                     (full_name, username, hashed, datetime.now().isoformat()))
        conn.commit()
        return "✅ Usuario registrado correctamente."
    except:
        return "❌ El nombre de usuario ya existe."

def login_usuario(username, password):
    hashed = hash_password(password)
    row = conn.execute("SELECT id, full_name, blocked FROM users WHERE username=? AND password=?", 
                       (username, hashed)).fetchone()
    if row:
        if row[2] == 1: return None, None, False, "❌ Tu cuenta está bloqueada."
        return row[0], row[1], True, ""
    return None, None, False, "❌ Usuario o contraseña incorrectos"

def get_all_users():
    rows = conn.execute("SELECT id, full_name, username, blocked, created_at FROM users").fetchall()
    return [[r[0], r[1], r[2], "✅ Activo" if r[3]==0 else "🚫 Bloqueado", r[4]] for r in rows]

def toggle_block(user_id):
    conn.execute("UPDATE users SET blocked = 1 - blocked WHERE id=?", (user_id,))
    conn.commit()
    return "Estado actualizado."

def delete_user(user_id):
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    return "Usuario eliminado."

def update_user(user_id, new_full_name, new_username, new_password):
    try:
        if new_password.strip():
            hashed = hash_password(new_password)
            conn.execute("UPDATE users SET full_name=?, username=?, password=? WHERE id=?", 
                         (new_full_name, new_username, hashed, user_id))
        else:
            conn.execute("UPDATE users SET full_name=?, username=? WHERE id=?", 
                         (new_full_name, new_username, user_id))
        conn.commit()
        return "✅ Usuario actualizado."
    except:
        return "❌ El nuevo nombre de usuario ya existe."

with gr.Blocks(title="Prompt Engineer Pro 2026 - Edgar", theme=gr.themes.Soft()) as demo:
    current_user_id = gr.State(None)
    current_full_name = gr.State("")
    is_admin = gr.State(False)

    with gr.Group(visible=True) as login_screen:
        gr.Markdown("# 🚀 Prompt Engineer Pro 2026\n**Acceso restringido**")
        with gr.Tabs():
            with gr.Tab("🔑 Iniciar Sesión"):
                login_user = gr.Textbox(label="Usuario", value="1978")
                login_pass = gr.Textbox(label="Contraseña", type="password", value="1978")
                btn_login = gr.Button("Iniciar Sesión", variant="primary")
                login_msg = gr.Markdown()

            with gr.Tab("📝 Registrarse"):
                reg_name = gr.Textbox(label="Nombre Completo")
                reg_user = gr.Textbox(label="Usuario")
                reg_pass = gr.Textbox(label="Contraseña", type="password")
                btn_reg = gr.Button("Registrarse")
                reg_msg = gr.Markdown()

    with gr.Group(visible=False) as main_app:
        gr.Markdown("# 🚀 Prompt Engineer Pro 2026\n**Tu traductor personal profesional**")
        with gr.Row():
            gr.Markdown("**Usuario conectado:**")
            user_display = gr.Markdown()
            btn_logout = gr.Button("🚪 Cerrar Sesión", variant="secondary", size="sm")

        with gr.Tabs():
            with gr.Tab("🔥 Hooks Virales de 8 Segundos para Vídeo"):
                gr.Markdown("### Próximamente aquí estarán tus hooks (versión completa)")
                gr.Markdown("Por ahora solo mostramos el panel de login y admin.")

            with gr.Tab("👑 Panel de Administrador", visible=False) as admin_tab:
                gr.Markdown("### 👑 Gestión de Usuarios (solo admin)")
                users_table = gr.DataFrame(headers=["ID", "Nombre", "Usuario", "Estado", "Creado"], value=get_all_users())
                refresh_btn = gr.Button("🔄 Actualizar Lista")
                with gr.Row():
                    selected_id = gr.Number(label="ID del usuario", precision=0)
                    new_name = gr.Textbox(label="Nuevo Nombre")
                    new_user = gr.Textbox(label="Nuevo Usuario")
                    new_pass = gr.Textbox(label="Nueva Contraseña (opcional)", type="password")
                with gr.Row():
                    btn_update = gr.Button("✏️ Actualizar")
                    btn_block = gr.Button("🚫 Bloquear / Desbloquear")
                    btn_delete = gr.Button("🗑 Eliminar", variant="stop")
                admin_msg = gr.Markdown()

        def do_login(u, p):
            user_id, full_name, success, msg = login_usuario(u, p)
            if success:
                admin_visible = (u == "1978")
                return gr.update(visible=False), gr.update(visible=True), user_id, full_name, f"✅ Bienvenido **{full_name}**", gr.update(visible=admin_visible)
            return gr.update(visible=True), gr.update(visible=False), None, "", f"❌ {msg}", gr.update(visible=False)

        btn_login.click(do_login, [login_user, login_pass], [login_screen, main_app, current_user_id, current_full_name, user_display, admin_tab])

        btn_reg.click(lambda n,u,p: registrar_usuario(n,u,p), [reg_name, reg_user, reg_pass], reg_msg)

        btn_logout.click(lambda: (gr.update(visible=True), gr.update(visible=False), None, "", "", gr.update(visible=False)),
                         None, [login_screen, main_app, current_user_id, current_full_name, user_display, admin_tab])

        refresh_btn.click(lambda: get_all_users(), None, users_table)
        btn_update.click(lambda uid,name,user,passw: update_user(uid,name,user,passw), [selected_id, new_name, new_user, new_pass], admin_msg)
        btn_block.click(lambda uid: toggle_block(uid), [selected_id], admin_msg)
        btn_delete.click(lambda uid: delete_user(uid), [selected_id], admin_msg)

demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
