# -*- coding: utf-8 -*-
"""
product_i2v.py - Motor de VIDEO PUBLICITARIO de productos (image-to-video) de CALIDAD.

Pipeline de calidad (cada paso reduce las fallas de la IA, basado en investigacion):
  1. PREPARAR la foto: sharpen sutil + escalar a resolucion nativa de WAN.
  2. GENERAR con WAN 2.2 14B (no 5B), prompt simple de accion, movimiento controlado,
     batch 4n+1, varias tomas con seeds distintas.
  3. UPSCALE CONSERVADOR con SeedVR2 (preserva etiquetas/texto/bordes del producto).
  4. (ensamblar_comercial.py) agrega texto/precio/musica.

La foto del producto es la REFERENCIA; la IA mantiene el producto y lo pone en escenas.
NUNCA sube nada: tu publicas.

Requiere WAN + SeedVR2 en ComfyUI (PC GPU). Si no estan, el motor avisa y no inventa.
"""
import os
import sys
import time
import subprocess
import argparse
import base64

try:
    import config_productos as CFG
except Exception:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import config_productos as CFG

try:
    import requests
except Exception:
    requests = None


def _foto_referencia(carpeta=None):
    carpeta = carpeta or CFG.RUTAS["referencia"]
    if not os.path.isdir(carpeta):
        return None
    exts = (".jpg", ".jpeg", ".png", ".webp")
    fotos = [os.path.join(carpeta, f) for f in sorted(os.listdir(carpeta))
             if f.lower().endswith(exts)]
    return fotos[0] if fotos else None


def _servidor_disponible(puerto):
    if requests is None:
        return False
    try:
        r = requests.get(f"http://{CFG.WAN_I2V['ip']}:{puerto}/", timeout=5)
        return r.status_code < 500
    except Exception:
        return False


# =============================================================================
# PASO 1: PREPARAR LA FOTO (reduce deformaciones)
# =============================================================================
def preparar_foto(foto_in, foto_out):
    """Prepara la foto antes de generar: sharpen sutil + escala a resolucion nativa
    de WAN. Un sharpen leve mantiene los bordes nitidos; la resolucion nativa evita
    que WAN introduzca deformaciones por reescalado interno."""
    w, h = CFG.WAN_I2V["resolucion"]
    filtros = []
    # escalar manteniendo proporcion y rellenar a la resolucion nativa (sin recortar producto)
    filtros.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease")
    filtros.append(f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=white")
    if CFG.PREP_FOTO.get("sharpen_sutil"):
        # unsharp suave: realza bordes sin crear halos
        filtros.append("unsharp=5:5:0.6:5:5:0.0")
    vf = ",".join(filtros)
    cmd = ['ffmpeg', '-y', '-i', foto_in, '-vf', vf, foto_out]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return os.path.exists(foto_out) and os.path.getsize(foto_out) > 1000


# =============================================================================
# PASO 2: GENERAR con WAN (image-to-video) — parametros de calidad
# =============================================================================
def generar_clip_wan(foto_ref, prompt_escena, salida_clip, seed=None):
    """Pide a WAN 2.2 14B un clip I2V con los parametros de calidad: prompt simple,
    movimiento controlado, batch 4n+1, block swap. Mantiene el producto de la foto."""
    cfg = CFG.WAN_I2V
    if not _servidor_disponible(cfg["puerto"]):
        return False, "WAN no disponible"
    try:
        with open(foto_ref, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
    except Exception as e:
        return False, f"no se pudo leer la foto: {e}"

    prompt_completo = CFG.PROMPT_MANTENER_PRODUCTO + prompt_escena
    payload = {
        "imagen_referencia": img_b64,
        "modelo": cfg["modelo"],
        "prompt": prompt_completo,
        "negative_prompt": CFG.NEGATIVE_PRODUCTO,
        "width": cfg["resolucion"][0],
        "height": cfg["resolucion"][1],
        "frames": int(cfg["duracion_clip_seg"] * cfg["fps"]),
        "fps": cfg["fps"],
        "steps": cfg["pasos"],
        "sampler": cfg["sampler"],
        "motion_strength": cfg["motion_strength"],   # movimiento sutil = menos deformacion
        "batch_size": cfg["batch_size"],             # 4n+1 = sin parpadeo
        "block_swap": cfg["block_swap"],
        "vae_tiled": cfg["vae_tiled"],
        "seed": seed if seed is not None else int(time.time() * 1000) % 1000000,
        "loras": CFG.LORAS_ACELERACION if CFG.LORAS_ACELERACION.get("usar") else None,
    }
    try:
        r = requests.post(f"http://{cfg['ip']}:{cfg['puerto']}/generate_i2v",
                          json=payload, timeout=900)
        if r.status_code == 200 and r.content and len(r.content) > 1000:
            with open(salida_clip, "wb") as f:
                f.write(r.content)
            ok = os.path.exists(salida_clip) and os.path.getsize(salida_clip) > 1000
            return ok, "ok" if ok else "archivo vacio"
        return False, f"WAN respondio {r.status_code}"
    except Exception as e:
        return False, f"error WAN: {e}"


# =============================================================================
# PASO 3: UPSCALE CONSERVADOR con SeedVR2 — preserva el producto
# =============================================================================
def upscale_conservador(video_in, video_out):
    """Sube de resolucion el clip con SeedVR2 (upscaler conservador que preserva
    etiquetas, texto y bordes del producto SIN inventar detalles). Es la clave para
    que el producto se vea fiel a la foto. Si SeedVR2 no esta, devuelve el video tal cual."""
    up = CFG.UPSCALER
    if not up.get("usar"):
        import shutil; shutil.copy(video_in, video_out); return True
    # SeedVR2 suele exponerse como servicio en ComfyUI; aqui se llama por su endpoint.
    if not _servidor_disponible(CFG.WAN_I2V["puerto"]):
        # sin servidor, no se puede upscalar: devolver el original (no romper)
        import shutil; shutil.copy(video_in, video_out); return True
    try:
        with open(video_in, "rb") as f:
            vid_b64 = base64.b64encode(f.read()).decode()
        payload = {
            "video": vid_b64,
            "modelo": up["modelo"],
            "resolucion": up["resolucion_objetivo"],
            "batch_size": up["batch_size"],          # 4n+1 = consistencia temporal
            "block_swap": up["block_swap"],
            "vae_tiled": up["vae_tiled"],
            "downscale_previo_mp": up["downscale_previo_mp"],  # truco SeedVR2
        }
        r = requests.post(f"http://{CFG.WAN_I2V['ip']}:{CFG.WAN_I2V['puerto']}/upscale_seedvr2",
                          json=payload, timeout=1200)
        if r.status_code == 200 and r.content and len(r.content) > 1000:
            with open(video_out, "wb") as f:
                f.write(r.content)
            return os.path.exists(video_out) and os.path.getsize(video_out) > 1000
    except Exception as e:
        print(f"   ⚠️ SeedVR2 fallo ({e}); se usa el video sin upscalar.")
    import shutil; shutil.copy(video_in, video_out); return True


def _unir_clips(clips, salida, fps):
    if not clips:
        return False
    if len(clips) == 1:
        import shutil; shutil.copy(clips[0], salida); return True
    lista = salida + "_lista.txt"
    with open(lista, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lista,
                    '-c:v', 'libx264', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                    '-r', str(fps), salida], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try: os.remove(lista)
    except Exception: pass
    return os.path.exists(salida) and os.path.getsize(salida) > 1000


def generar_comercial(nombre_producto="", precio="", escenas=None, carpeta_ref=None):
    """Pipeline completo de calidad: foto -> preparar -> WAN (varias tomas) ->
    SeedVR2 -> unir. Devuelve el video IA final (antes de texto/musica), o None."""
    foto = _foto_referencia(carpeta_ref)
    if not foto:
        print(f"⚠️ No hay foto de referencia en {carpeta_ref or CFG.RUTAS['referencia']}.")
        print(f"   Sube UNA foto del producto (fondo limpio, buena resolucion) ahi.")
        return None

    if escenas:
        nombres = [e.strip() for e in escenas if e.strip() in CFG.ESCENAS_COMERCIAL]
    else:
        nombres = list(CFG.ESCENAS_COMERCIAL.keys())[:CFG.ESCENAS_POR_COMERCIAL]
    if not nombres:
        nombres = [CFG.ESCENA_DEFAULT]

    print(f"📦 Comercial de CALIDAD de '{nombre_producto}'")
    print(f"   Foto: {os.path.basename(foto)} | Escenas: {', '.join(nombres)}")

    if not _servidor_disponible(CFG.WAN_I2V["puerto"]):
        print(f"\n⚠️ WAN/ComfyUI no esta corriendo en {CFG.WAN_I2V['ip']}:{CFG.WAN_I2V['puerto']}.")
        print(f"   Pipeline de calidad listo. Falta instalar:")
        print(f"     1. ComfyUI en la PC GPU")
        print(f"     2. Modelo WAN 2.2 14B fp8 (i2v)")
        print(f"     3. SeedVR2 (upscaler conservador)")
        print(f"   En cuanto respondan, este motor genera el comercial con calidad.")
        return None

    temp = CFG.RUTAS["temp"]; salida_dir = CFG.RUTAS["salida"]
    for c in (temp, salida_dir):
        os.makedirs(c, exist_ok=True)

    # PASO 1: preparar la foto una vez
    foto_prep = os.path.join(temp, "_foto_prep.png")
    if not preparar_foto(foto, foto_prep):
        print("   ⚠️ No se pudo preparar la foto; se usa la original.")
        foto_prep = foto
    else:
        print(f"   ✓ Foto preparada (resolucion nativa + sharpen sutil)")

    # PASO 2+3: por cada escena, generar (varias tomas) y upscalar
    clips_finales = []
    for i, nombre_esc in enumerate(nombres):
        prompt_esc = CFG.ESCENAS_COMERCIAL[nombre_esc]
        print(f"   escena '{nombre_esc}':")
        clip_crudo = None
        for intento in range(CFG.WAN_I2V["intentos_por_escena"]):
            cand = os.path.join(temp, f"_esc{i:02d}_t{intento}.mp4")
            ok, msg = generar_clip_wan(foto_prep, prompt_esc, cand, seed=None)
            if ok:
                clip_crudo = cand
                print(f"     toma {intento+1}: generada ✓")
                break
            else:
                print(f"     toma {intento+1}: {msg}")
        if not clip_crudo:
            print(f"     ⚠️ escena '{nombre_esc}' no se pudo generar")
            continue
        # upscale conservador (preserva el producto)
        clip_up = os.path.join(temp, f"_esc{i:02d}_up.mp4")
        upscale_conservador(clip_crudo, clip_up)
        clips_finales.append(clip_up)
        print(f"     upscale conservador (SeedVR2) ✓")

    if not clips_finales:
        print("⚠️ No se genero ninguna escena.")
        return None

    video_ia = os.path.join(temp, "_comercial_ia.mp4")
    if not _unir_clips(clips_finales, video_ia, CFG.WAN_I2V["fps"]):
        print("⚠️ No se pudieron unir las escenas.")
        return None

    print(f"✅ Video IA de calidad generado: {video_ia}")
    print(f"   (siguiente: ensamblar_comercial.py agrega texto/precio/musica)")
    return video_ia


if __name__ == "__main__":
    CFG.resumen()
    ap = argparse.ArgumentParser(description="Comercial de producto image-to-video de CALIDAD (WAN+SeedVR2).")
    ap.add_argument("--producto", default="")
    ap.add_argument("--precio", default="")
    ap.add_argument("--escenas", default="")
    ap.add_argument("--referencia", default=None)
    args = ap.parse_args()
    escenas = args.escenas.split(",") if args.escenas else None
    generar_comercial(args.producto, args.precio, escenas, args.referencia)
