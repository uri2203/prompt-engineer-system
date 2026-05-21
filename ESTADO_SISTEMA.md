# 🏭 DARK FACTORY — SISTEMA PINPINELA
> Archivo de contexto para Claude. Subir al inicio de cada sesión.

---

## 🏗️ ARQUITECTURA GENERAL

Sistema de producción automatizada de contenido para YouTube/Shorts.
Arquitectura cliente-servidor dividida en dos nodos:

### Nodo 1 — Servidor Render (Cloud)
- **Archivo principal:** `app.py` (Flask)
- **URL producción:** `https://prompt-engineer-system-l2r6.onrender.com`
- **Repo GitHub:** `uri2203/prompt-engineer-system`
- **Función:** recibe órdenes del frontend, gestiona cola de tareas, entrega resultados

### Nodo 2 — PC Local Windows (GPU)
- **Ruta base:** `C:\NODO_PINPINELA\`
- **GPU:** RTX 3060
- **Archivos locales (NO están en GitHub):**
  - `worker_cpu.py` — worker principal, hace polling al servidor
  - `pexels_engine.py` — motor de búsqueda de clips Pexels
  - `historial_clips.json` — historial de clips usados (evita repetición)
- **Servicios locales:**
  - Stable Diffusion en `192.168.0.215:7861` (generación de imágenes)
  - XTTS en `C:\NODO_PINPINELA` (generación de voz)

---

## 📁 ESTRUCTURA DEL REPO

```
prompt-engineer-system/
├── app.py                  ← Servidor Flask principal (NO tocar sin análisis)
├── gunicorn.conf.py
├── requirements.txt
├── modulos/
│   ├── ai_engine.py        ← ADN visual + generación de prompts con Gemini
│   ├── pexels_engine.py    ← (versión repo, la local es diferente)
│   ├── voice_engine.py
│   ├── video_engine.py
│   ├── cctv_engine.py
│   ├── trend_engine.py
│   ├── compliance_engine.py
│   ├── neuro_engine.py
│   ├── bot_orquestador.py
│   ├── bot_audio.py
│   ├── bot_video.py
│   ├── mod_1_traductor.py
│   ├── mod_2_guiones.py
│   ├── mod_3_hooks.py
│   ├── mod_4_empaquetado.py
│   ├── mod_5_ventas.py
│   ├── boveda.py           ← almacén de API keys
│   ├── usuarios.py
│   ├── auth.py
│   ├── auditoria.py
│   └── config.py
└── templates/
    ├── workspace.html      ← Frontend principal
    ├── login.html
    ├── usuarios.html
    ├── configuracion.html
    ├── bot_dashboard.html
    ├── adn.html
    ├── mantenimiento.html
    └── layout.html
```

---

## 📺 CANALES ACTIVOS

### La Viuda
- **Estilo:** Terror psicológico, horror atmosférico
- **Imágenes:** 100% Stable Diffusion (ratio_pexels = 0)
- **Formato video:** 9:16 (Shorts)
- **ADN visual:** siluetas, tonos rojos/negros, luces tenues, sin personas reales
- **Prompt SD:** psychological horror, shadowy apparition, chiaroscuro, analog film grain

### Monkygraff
- **Estilo:** Fotoperiodismo geopolítico
- **Imágenes:** 50% Pexels / 50% Stable Diffusion
- **Formato video:** 16:9
- **ADN visual:** militar, industrial, infraestructura, sin personas, RAW photo
- **Prompt SD:** RAW photo, photojournalism, gritty texture, no people

---

## 🔄 FLUJO DE PRODUCCIÓN

```
[workspace.html]
  ↓ Selecciona marca + genera guión (Gemini via ai_engine)
  ↓ POST /api/generate_image  → {prompt, formato, marca}
[app.py]
  ↓ Crea tarea IMAGEN en cola_de_renderizado con {id, tipo, prompt, formato, marca}
[worker_cpu.py — polling cada 2s]
  ↓ Tarea IMAGEN:
      → Lee marca → aplica bloque de estilo correcto
      → Si Monkygraff: busca en Pexels (pexels_engine) o SD fallback
      → Si La Viuda: 100% SD con terror style
  ↓ POST /api/nodo/upload_result → resultado regresa al servidor
[workspace.html]
  ↓ GET /api/check_image/<tarea_id> → recibe imagen final
```

---

## ✅ FIXES APLICADOS EN ESTA SESIÓN

| Fix | Archivo | Descripción |
|-----|---------|-------------|
| ✅ | `workspace.html` | Agregar `marca` al fetch de generate_image |
| ✅ | `app.py` | Pasar `marca` al task IMAGEN en cola_de_renderizado |
| ✅ | `worker_cpu.py` | Agregar bloque de estilo explícito para Monkygraff |
| ✅ | `pexels_engine.py` | Paginación p2/p3 antes de reusar clips + BLOQUEO_ULTIMOS 50→200 |

---

## 🔜 PENDIENTES (EN ORDEN DE PRIORIDAD)

### 1. Colchón de videos
- Producir videos de La Viuda y Monkygraff para acumular contenido
- Detectar y corregir bugs que aparezcan en producción

### 2. Nuevos canales
- Definir ADN visual por canal (estilo, ratio_pexels, keywords, prompts SD)
- Agregar bloque en worker_cpu.py + ADN_CANALES en pexels_engine.py

### 3. Automatización completa
- Pipeline sin intervención manual: generación → render → upload YouTube
- Scheduling automático de publicaciones

### 4. Plan de emergencia Xeon → RTX 3060
- Si el servidor Xeon no responde durante automatización
- La RTX 3060 local debe tomar el trabajo automáticamente
- Definir lógica de failover en worker_cpu.py

---

## ⚠️ REGLAS DE ORO AL TOCAR EL CÓDIGO

1. `app.py` es el archivo más crítico — analizar bien antes de modificar
2. Los archivos locales (`worker_cpu.py`, `pexels_engine.py`) NO están en GitHub — siempre entregar como descarga
3. Cuando se agregue un nuevo canal: actualizar `worker_cpu.py` (bloque de estilo) + `pexels_engine.py` (ADN_CANALES) + `ai_engine.py` (ADN de guiones)
4. La cola `cola_de_renderizado` en app.py es volátil — Render la borra al reiniciar

---

## 🔑 CREDENCIALES (agregar manualmente)
- **GitHub repo:** `uri2203/prompt-engineer-system`
- **GitHub token:** _(pegar aquí al inicio de sesión)_
- **Render URL:** `https://prompt-engineer-system-l2r6.onrender.com`
- **Stable Diffusion:** `192.168.0.215:7861`
- **Pexels API key:** _(en boveda.py)_
- **Gemini API key:** _(en boveda.py)_
- **ElevenLabs:** _(en boveda.py)_
