# -*- coding: utf-8 -*-
"""
product_clips.py — Motor de CLIPS DE PRODUCTOS por movimiento de imagen.

Toma las fotos de un producto (carpeta de entrada) y genera un clip corto con
movimiento profesional (zoom, paneo, parallax), transiciones, y opcionalmente
texto/precio y música. NO necesita ComfyUI ni IA de video: usa FFmpeg, así que
es RÁPIDO y funciona en cualquier máquina con FFmpeg.

Uso básico:
    python product_clips.py --producto "Audífonos X" --precio "$499"

Lee las fotos de RUTAS['entrada'] y guarda el clip en RUTAS['salida'].
NUNCA sube nada a ninguna plataforma.
"""
import os
import sys
import subprocess
import random
import argparse

# Cargar configuración del módulo de productos
try:
    import config_productos as CFG
except Exception:
    # permitir importar aunque se ejecute desde otra carpeta
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import config_productos as CFG


def _listar_fotos(carpeta):
    """Lista las fotos del producto en orden (jpg/png/webp)."""
    if not os.path.isdir(carpeta):
        return []
    exts = (".jpg", ".jpeg", ".png", ".webp")
    fotos = [os.path.join(carpeta, f) for f in sorted(os.listdir(carpeta))
             if f.lower().endswith(exts)]
    return fotos


def _resolucion():
    if CFG.FORMATO["orientacion"] == "vertical":
        return CFG.FORMATO["resolucion_vertical"]
    return CFG.FORMATO["resolucion_horizontal"]


def _clip_de_foto(foto, salida_clip, movimiento, dur, w, h, fps):
    """Genera un clip de una sola foto con el movimiento indicado (zoom/paneo).
    Usa el filtro zoompan de FFmpeg. La foto se escala para cubrir el encuadre."""
    # frames totales del clip
    frames = int(dur * fps)
    # Preparar el filtro según el movimiento. zoompan trabaja sobre la imagen
    # escalada; 'z' es el zoom, 'x'/'y' el desplazamiento del encuadre.
    # Se sobre-escala a 1.5x para tener margen de paneo sin bordes negros.
    base_scale = f"scale={int(w*1.5)}:{int(h*1.5)}:force_original_aspect_ratio=increase,crop={int(w*1.5)}:{int(h*1.5)}"

    if movimiento == "zoom_in_lento":
        zp = f"zoompan=z='min(zoom+0.0010,1.4)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
    elif movimiento == "zoom_out_lento":
        zp = f"zoompan=z='if(eq(on,0),1.4,max(zoom-0.0010,1.0))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
    elif movimiento == "paneo_izq_der":
        zp = f"zoompan=z=1.2:d={frames}:x='(iw-iw/zoom)*on/{frames}':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
    elif movimiento == "paneo_arriba_abajo":
        zp = f"zoompan=z=1.2:d={frames}:x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*on/{frames}':s={w}x{h}:fps={fps}"
    elif movimiento == "zoom_in_diagonal":
        zp = f"zoompan=z='min(zoom+0.0012,1.4)':d={frames}:x='(iw-iw/zoom)*on/{frames}':y='(ih-ih/zoom)*on/{frames}':s={w}x{h}:fps={fps}"
    else:  # parallax_suave u otros → zoom in muy leve (seguro)
        zp = f"zoompan=z='min(zoom+0.0006,1.25)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"

    vf = f"{base_scale},{zp},format=yuv420p"
    cmd = ['ffmpeg', '-y', '-loop', '1', '-i', foto, '-t', str(dur),
           '-vf', vf, '-c:v', 'libx264', '-preset', 'medium', '-pix_fmt', 'yuv420p',
           '-r', str(fps), salida_clip]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return os.path.exists(salida_clip) and os.path.getsize(salida_clip) > 1000


def _concatenar_clips(clips, salida, w, h, fps, transicion="fade"):
    """Une los clips de cada foto en un solo video, con transición entre ellos."""
    if not clips:
        return False
    if len(clips) == 1:
        import shutil
        shutil.copy(clips[0], salida)
        return True
    # Concatenación simple con crossfade (xfade) encadenado
    # Para mantenerlo robusto, si xfade falla, se hace concat duro.
    try:
        # construir filtro xfade encadenado
        dur_trans = 0.4
        inputs = []
        for c in clips:
            inputs += ['-i', c]
        # duración de cada clip
        durs = []
        for c in clips:
            d = _duracion(c)
            durs.append(d if d > 0 else CFG.FORMATO["duracion_por_foto_seg"])
        filtro = ""
        last = "0:v"
        offset = 0.0
        for i in range(1, len(clips)):
            offset += durs[i-1] - dur_trans
            out = f"v{i}"
            filtro += f"[{last}][{i}:v]xfade=transition={_xfade_name(transicion)}:duration={dur_trans}:offset={offset:.3f}[{out}];"
            last = out
        filtro = filtro.rstrip(";")
        cmd = ['ffmpeg', '-y'] + inputs + ['-filter_complex', filtro,
               '-map', f'[{last}]', '-c:v', 'libx264', '-preset', 'medium',
               '-pix_fmt', 'yuv420p', '-r', str(fps), salida]
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if os.path.exists(salida) and os.path.getsize(salida) > 1000:
            return True
    except Exception:
        pass
    # Respaldo: concat duro (sin transición) vía lista
    lista = salida + "_lista.txt"
    with open(lista, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lista,
           '-c:v', 'libx264', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', str(fps), salida]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        os.remove(lista)
    except Exception:
        pass
    return os.path.exists(salida) and os.path.getsize(salida) > 1000


def _xfade_name(t):
    return {"fade": "fade", "slide": "slideleft", "zoom": "smoothleft"}.get(t, "fade")


def _duracion(ruta):
    try:
        r = subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                            '-of', 'csv=p=0', ruta], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def _agregar_texto(video_in, video_out, texto, w, h):
    """Pone el texto del producto (nombre/precio) en pantalla."""
    if not texto:
        import shutil; shutil.copy(video_in, video_out); return True
    pos = CFG.PRESENTACION.get("posicion_texto", "inferior")
    y = f"h-th-{int(h*0.10)}" if pos == "inferior" else f"{int(h*0.08)}"
    # texto con caja semitransparente para legibilidad
    txt = texto.replace(":", "\\:").replace("'", "")
    vf = (f"drawtext=text='{txt}':fontcolor=white:fontsize={int(h*0.045)}:"
          f"box=1:boxcolor=black@0.5:boxborderw=20:x=(w-text_w)/2:y={y}")
    cmd = ['ffmpeg', '-y', '-i', video_in, '-vf', vf,
           '-c:v', 'libx264', '-preset', 'medium', '-pix_fmt', 'yuv420p', video_out]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return os.path.exists(video_out) and os.path.getsize(video_out) > 1000


def _agregar_musica(video_in, video_out):
    """Agrega música de fondo si hay archivos en la carpeta de música."""
    carpeta = CFG.PRESENTACION.get("carpeta_musica", "")
    if not (CFG.PRESENTACION.get("musica_fondo") and os.path.isdir(carpeta)):
        import shutil; shutil.copy(video_in, video_out); return True
    pistas = [os.path.join(carpeta, f) for f in os.listdir(carpeta)
              if f.lower().endswith((".mp3", ".wav", ".m4a", ".aac"))]
    if not pistas:
        import shutil; shutil.copy(video_in, video_out); return True
    musica = random.choice(pistas)
    cmd = ['ffmpeg', '-y', '-i', video_in, '-i', musica,
           '-filter_complex', '[1:a]volume=0.5,afade=t=out:st=25:d=3[a]',
           '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-shortest', video_out]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return os.path.exists(video_out) and os.path.getsize(video_out) > 1000


def generar_clip_producto(nombre_producto="", precio="", carpeta_entrada=None, salida=None):
    """
    Genera un clip de producto a partir de las fotos en la carpeta de entrada.
    Devuelve la ruta del clip final o None si falla.
    """
    carpeta_entrada = carpeta_entrada or CFG.RUTAS["entrada"]
    carpeta_salida = CFG.RUTAS["salida"]
    carpeta_temp = CFG.RUTAS["temp"]
    for c in (carpeta_salida, carpeta_temp):
        os.makedirs(c, exist_ok=True)

    fotos = _listar_fotos(carpeta_entrada)
    if not fotos:
        print(f"⚠️ No hay fotos en {carpeta_entrada}. Sube fotos del producto ahí.")
        return None

    print(f"📦 Generando clip de producto: '{nombre_producto}' ({len(fotos)} fotos)")
    w, h = _resolucion()
    fps = CFG.FORMATO["fps"]
    dur_foto = CFG.FORMATO["duracion_por_foto_seg"]
    # respetar duración total máxima
    max_fotos = max(1, int(CFG.FORMATO["duracion_total_max_seg"] / dur_foto))
    fotos = fotos[:max_fotos]

    # 1. Un clip con movimiento por cada foto (rotando los movimientos para variar)
    clips = []
    movimientos = CFG.MOVIMIENTOS_IMAGEN
    for i, foto in enumerate(fotos):
        mov = movimientos[i % len(movimientos)]
        clip = os.path.join(carpeta_temp, f"_pclip_{i:02d}.mp4")
        if _clip_de_foto(foto, clip, mov, dur_foto, w, h, fps):
            clips.append(clip)
            print(f"   foto {i+1}/{len(fotos)}: {mov} ✓")
        else:
            print(f"   foto {i+1}/{len(fotos)}: ⚠️ falló, se omite")
    if not clips:
        print("⚠️ No se pudo generar ningún clip de las fotos.")
        return None

    # 2. Unir con transiciones
    trans = random.choice(CFG.TRANSICIONES)
    video_unido = os.path.join(carpeta_temp, "_unido.mp4")
    if not _concatenar_clips(clips, video_unido, w, h, fps, trans):
        print("⚠️ No se pudieron unir los clips.")
        return None

    # 3. Texto (nombre/precio) si está activado
    texto = ""
    if CFG.PRESENTACION.get("mostrar_texto"):
        texto = nombre_producto + (f"   {precio}" if precio else "")
    video_texto = os.path.join(carpeta_temp, "_texto.mp4")
    _agregar_texto(video_unido, video_texto, texto, w, h)

    # 4. Música si está activada
    nombre_archivo = (nombre_producto or "producto").replace(" ", "_").replace("/", "-")
    salida = salida or os.path.join(carpeta_salida, f"{nombre_archivo}.mp4")
    _agregar_musica(video_texto, salida)

    # limpiar temporales
    for c in clips + [video_unido, video_texto]:
        try: os.remove(c)
        except Exception: pass

    if os.path.exists(salida):
        print(f"✅ Clip de producto listo: {salida}")
        print(f"   ⚠️ Recuerda: este clip NO se sube solo. Publícalo tú manualmente.")
        return salida
    return None


if __name__ == "__main__":
    CFG.resumen()
    ap = argparse.ArgumentParser(description="Genera un clip de producto a partir de fotos.")
    ap.add_argument("--producto", default="", help="Nombre del producto (para el texto en pantalla)")
    ap.add_argument("--precio", default="", help="Precio a mostrar (opcional)")
    ap.add_argument("--entrada", default=None, help="Carpeta con las fotos (opcional)")
    args = ap.parse_args()
    generar_clip_producto(args.producto, args.precio, args.entrada)
