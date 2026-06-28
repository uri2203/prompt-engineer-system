# -*- coding: utf-8 -*-
"""
product_i2v.py - Motor de VIDEO PUBLICITARIO de productos (image-to-video).

Toma UNA foto de referencia del producto y genera un COMERCIAL donde la IA (WAN)
mantiene el producto y lo coloca en escenas/ambientes con movimiento real.

Flujo:
  1. Lee la foto de referencia del producto.
  2. Para cada escena elegida, pide a WAN (image-to-video) un clip manteniendo
     el producto en ese ambiente con movimiento de camara.
  3. Une los clips de las escenas.
  4. (Lo hace ensamblar_comercial.py) agrega texto/precio/musica.
  5. Entrega el comercial. NUNCA lo sube: tu publicas.

REQUISITO: WAN corriendo en la PC GPU (ComfyUI). Si WAN no esta disponible,
el motor avisa y NO inventa nada (no cae a slideshow).

Uso:
    python product_i2v.py --producto "Audifonos Pro X" --precio "$499" --escenas premium_mesa,estudio_limpio
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
    """Encuentra la foto de referencia del producto (la primera imagen valida)."""
    carpeta = carpeta or CFG.RUTAS["referencia"]
    if not os.path.isdir(carpeta):
        return None
    exts = (".jpg", ".jpeg", ".png", ".webp")
    fotos = [os.path.join(carpeta, f) for f in sorted(os.listdir(carpeta))
             if f.lower().endswith(exts)]
    return fotos[0] if fotos else None


def _wan_disponible():
    """Verifica si el servidor WAN responde."""
    if requests is None:
        return False
    cfg = CFG.WAN_I2V
    url = f"http://{cfg['ip']}:{cfg['puerto']}/"
    try:
        r = requests.get(url, timeout=5)
        return r.status_code < 500
    except Exception:
        return False


def generar_clip_i2v(foto_ref, prompt_escena, salida_clip, seed=None):
    """
    Pide a WAN un clip image-to-video: mantiene el producto de 'foto_ref' y lo
    anima en la escena descrita por 'prompt_escena'.

    Esta funcion habla con el servidor WAN (ComfyUI API) en la PC GPU. La forma
    EXACTA del payload depende del workflow de ComfyUI que se monte en la Fase P1;
    aqui se deja la estructura y el punto de integracion claramente marcado.

    Devuelve True si genero el clip.
    """
    cfg = CFG.WAN_I2V
    prompt_completo = CFG.PROMPT_MANTENER_PRODUCTO + prompt_escena

    if not _wan_disponible():
        print(f"   ⚠️ WAN no esta disponible en {cfg['ip']}:{cfg['puerto']}.")
        print(f"      Instala ComfyUI + modelo WAN I2V (Fase P1) y vuelve a intentar.")
        return False

    # Leer la foto como base64 (asi se envia la referencia a la API)
    try:
        with open(foto_ref, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
    except Exception as e:
        print(f"   ⚠️ No se pudo leer la foto de referencia: {e}")
        return False

    # ── PUNTO DE INTEGRACION CON WAN (ComfyUI) ──
    # En la Fase P1, aqui se envia el workflow de ComfyUI para image-to-video.
    # Estructura tipica (se ajustara al workflow real):
    payload = {
        "imagen_referencia": img_b64,           # la foto del producto (ancla)
        "prompt": prompt_completo,              # mantener producto + escena
        "negative_prompt": CFG.NEGATIVE_PRODUCTO,
        "width": cfg["resolucion"][0],
        "height": cfg["resolucion"][1],
        "frames": int(cfg["duracion_clip_seg"] * cfg["fps"]),
        "fps": cfg["fps"],
        "steps": cfg["pasos"],
        "seed": seed if seed is not None else int(time.time()) % 1000000,
    }
    url = f"http://{cfg['ip']}:{cfg['puerto']}/generate_i2v"  # endpoint del servidor WAN
    try:
        r = requests.post(url, json=payload, timeout=600)  # I2V es lento: timeout amplio
        if r.status_code == 200:
            # el servidor devuelve el video (bytes) o una ruta; se guarda
            data = r.content
            if data and len(data) > 1000:
                with open(salida_clip, "wb") as f:
                    f.write(data)
                return os.path.exists(salida_clip) and os.path.getsize(salida_clip) > 1000
        print(f"   ⚠️ WAN respondio {r.status_code}.")
        return False
    except Exception as e:
        print(f"   ⚠️ Error hablando con WAN: {e}")
        return False


def _unir_clips(clips, salida, fps):
    """Une los clips de las escenas en un solo video."""
    if not clips:
        return False
    if len(clips) == 1:
        import shutil; shutil.copy(clips[0], salida); return True
    lista = salida + "_lista.txt"
    with open(lista, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lista,
           '-c:v', 'libx264', '-preset', 'medium', '-pix_fmt', 'yuv420p',
           '-r', str(fps), salida]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try: os.remove(lista)
    except Exception: pass
    return os.path.exists(salida) and os.path.getsize(salida) > 1000


def generar_comercial(nombre_producto="", precio="", escenas=None, carpeta_ref=None):
    """
    Genera el comercial completo del producto:
      - foto de referencia -> WAN I2V por cada escena -> unir -> (ensamblar texto/musica).
    Devuelve la ruta del video generado por IA (antes de texto/musica), o None.
    """
    foto = _foto_referencia(carpeta_ref)
    if not foto:
        print(f"⚠️ No hay foto de referencia en {carpeta_ref or CFG.RUTAS['referencia']}.")
        print(f"   Sube UNA foto del producto (fondo limpio) ahi y vuelve a intentar.")
        return None

    # Escenas a usar
    if escenas:
        nombres_escena = [e.strip() for e in escenas if e.strip() in CFG.ESCENAS_COMERCIAL]
    else:
        # tomar las primeras N escenas configuradas
        nombres_escena = list(CFG.ESCENAS_COMERCIAL.keys())[:CFG.ESCENAS_POR_COMERCIAL]
    if not nombres_escena:
        nombres_escena = [CFG.ESCENA_DEFAULT]

    print(f"📦 Comercial de '{nombre_producto}' | foto: {os.path.basename(foto)}")
    print(f"   Escenas: {', '.join(nombres_escena)}")

    if not _wan_disponible():
        print(f"\n⚠️ WAN no esta instalado/corriendo todavia.")
        print(f"   Este motor necesita WAN (image-to-video) en la PC GPU.")
        print(f"   Siguiente paso: instalar ComfyUI + modelo WAN I2V (Fase P1).")
        print(f"   El codigo ya esta listo: en cuanto WAN responda, generara el comercial.")
        return None

    carpeta_temp = CFG.RUTAS["temp"]
    carpeta_salida = CFG.RUTAS["salida"]
    for c in (carpeta_temp, carpeta_salida):
        os.makedirs(c, exist_ok=True)

    # Generar un clip I2V por cada escena (con varios intentos, quedarse con el primero OK)
    clips = []
    for i, nombre_esc in enumerate(nombres_escena):
        prompt_esc = CFG.ESCENAS_COMERCIAL[nombre_esc]
        clip_ok = None
        for intento in range(CFG.WAN_I2V["intentos_por_escena"]):
            clip = os.path.join(carpeta_temp, f"_esc_{i:02d}_t{intento}.mp4")
            print(f"   escena '{nombre_esc}' (intento {intento+1})...")
            if generar_clip_i2v(foto, prompt_esc, clip, seed=None):
                clip_ok = clip
                break
        if clip_ok:
            clips.append(clip_ok)
            print(f"     ✓ generada")
        else:
            print(f"     ⚠️ no se pudo generar esta escena")

    if not clips:
        print("⚠️ No se genero ninguna escena.")
        return None

    # Unir las escenas
    video_ia = os.path.join(carpeta_temp, "_comercial_ia.mp4")
    if not _unir_clips(clips, video_ia, CFG.WAN_I2V["fps"]):
        print("⚠️ No se pudieron unir las escenas.")
        return None

    print(f"✅ Video IA generado: {video_ia}")
    print(f"   (siguiente: ensamblar_comercial.py le agrega texto/precio/musica)")
    return video_ia


if __name__ == "__main__":
    CFG.resumen()
    ap = argparse.ArgumentParser(description="Genera un comercial de producto (image-to-video con WAN).")
    ap.add_argument("--producto", default="", help="Nombre del producto")
    ap.add_argument("--precio", default="", help="Precio (opcional)")
    ap.add_argument("--escenas", default="", help="Escenas separadas por coma (ej: premium_mesa,estudio_limpio)")
    ap.add_argument("--referencia", default=None, help="Carpeta con la foto del producto")
    args = ap.parse_args()
    escenas = args.escenas.split(",") if args.escenas else None
    generar_comercial(args.producto, args.precio, escenas, args.referencia)
