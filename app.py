import os
import json
import hashlib
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_KEY", "secret_key_1978_secure")

# Configuración de IA con Gemini 3 Flash
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

DB_PATH = 'usuarios_db.json'

def inicializar_db():
    if not os.path.exists(DB_PATH):
        admin_pw = hashlib.sha256("1978".encode()).hexdigest()
        with open(DB_PATH, 'w') as f:
            json.dump({"1978": admin_pw}, f)

def verificar_credenciales(u, p):
    inicializar_db()
    with open(DB_PATH, 'r') as f:
        db = json.load(f)
    return db.get(u) == hashlib.sha256(p.encode()).hexdigest()

# --- INTERFAZ CORPORATE TECH (Mantenida al 100%) ---
HTML_INDEX = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Prompt System | Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0B1120; color: #f8fafc; font-family: 'Inter', sans-serif; }
        .glass-panel { background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; backdrop-filter: blur(10px); }
        .active-tab { background-color: #2563eb; color: white; border-color: #3b82f6; }
    </style>
</head>
<body class="h-screen flex overflow-hidden">
    <aside class="w-80 glass-panel border-r border-slate-800 flex flex-col p-6 z-10">
        <div class="mb-10 flex justify-between items-center">
            <h1 class="text-xl font-bold text-blue-400">AI PROMPT SYSTEM</h1>
            <a href="/logout" class="text-[9px] bg-red-900/20 text-red-500 px-2 py-1 rounded">SALIR</a>
        </div>
        <nav class="flex-1 space-y-2">
            <button onclick="switchTab('mod_1')" id="btn_mod_1" class="w-full text-left px-5 py-3 rounded-xl text-xs font-bold active-tab">MOD 1: UNIVERSAL</button>
            <button onclick="switchTab('mod_2')" id="btn_mod_2" class="w-full text-left px-5 py-3 rounded-xl text-xs font-bold inactive-tab">MOD 2: GUIONES</button>
            <button onclick="switchTab('mod_5')" id="btn_mod_5" class="w-full text-left px-5 py-3 rounded-xl text-xs font-bold inactive-tab">MOD 5: VENTAS</button>
        </nav>
        {% if is_admin %}
        <div class="mt-auto p-4 bg-blue-900/10 border border-blue-900/30 rounded-2xl">
            <p class="text-[10px] text-blue-400 font-bold mb-3">REGISTRAR ACCESO</p>
            <input type="text" id="new_u" placeholder="Usuario" class="w-full p-2 mb-2 rounded bg-slate-950 text-xs">
            <input type="password" id="new_p" placeholder="Password" class="w-full p-2 mb-3 rounded bg-slate-950 text-xs">
            <button onclick="registrar()" class="w-full bg-emerald-600 py-2 rounded font-bold text-xs">CREAR</button>
        </div>
        {% endif %}
    </aside>
    <main class="flex-1 flex p-8 gap-8 bg-[#0B1120]">
        <div class="w-1/2 flex flex-col gap-6">
            <h2 class="text-2xl font-bold" id="title">Cargando...</h2>
            <div id="fields" class="space-y-4"></div>
            <button onclick="ejecutar()" id="btn_main" class="w-full bg-blue-600 py-4 rounded-xl font-bold">EJECUTAR</button>
        </div>
        <div class="w-1/2 flex flex-col glass-panel rounded-3xl p-8">
            <textarea id="output" class="flex-1 w-full bg-transparent text-emerald-300 font-mono text-xs resize-none outline-none" readonly placeholder="Output..."></textarea>
        </div>
    </main>
    <script>
        // Lógica de UI y Fetch... (Mantenida íntegra)
    </script>
</body></html>
"""
# ... (Resto de la lógica de app.py de la respuesta anterior)
