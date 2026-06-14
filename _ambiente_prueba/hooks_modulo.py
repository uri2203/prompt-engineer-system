"""
MÓDULO DE HOOKS DE RETENCIÓN — para insertar en worker_cpu.py
Inserta hooks en un video ya ensamblado (con narración), recalculando todo.
Dos formatos alternados aleatoriamente:
  A) PATTERN INTERRUPT: pausa breve + golpe visual (flash/zoom) + stinger + texto
  B) FLASH-FORWARD: corte a imagen teaser de algo que viene + frase gancho + stinger
NUNCA rompe el video: si algo falla, devuelve el video original intacto.
"""
import os, subprocess, random, math

def _dur(ruta):
    """Duración de un archivo de video/audio en segundos."""
    try:
        r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                            '-of','csv=p=0', ruta], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0

def _clip_valido(ruta, min_dur=0.2):
    return os.path.exists(ruta) and os.path.getsize(ruta) > 1000 and _dur(ruta) >= min_dur

def _generar_stinger(ruta_salida, dur=1.2, tipo="whoosh"):
    """Genera un sonido de impacto sintético con FFmpeg (sin archivos externos)."""
    try:
        if tipo == "whoosh":
            # Barrido de ruido filtrado (whoosh) + golpe grave
            filtro = (f"anoisesrc=d={dur}:c=pink:a=0.3,"
                      f"afade=t=in:d=0.3,afade=t=out:st={dur*0.5:.2f}:d={dur*0.5:.2f},"
                      f"highpass=f=200,lowpass=f=3000")
        else:  # "impact" golpe grave
            filtro = (f"sine=frequency=80:duration={dur},"
                      f"afade=t=out:st=0.1:d={dur-0.1:.2f}")
        cmd = ['ffmpeg','-y','-f','lavfi','-i', filtro,
               '-ar','44100','-ac','1','-q:a','5', ruta_salida]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(ruta_salida)
    except Exception:
        return False

def _texto_en_frame(ruta_img_origen, frase, ruta_salida, w, h, pil_disponible, fuentes):
    """Quema texto grande tipo TikTok sobre una imagen."""
    if not pil_disponible or not frase:
        return False
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.open(ruta_img_origen).convert('RGBA')
        img = img.resize((w, h))
        # Oscurecer un poco el fondo para que el texto resalte
        overlay_dark = Image.new('RGBA', img.size, (0,0,0,110))
        img = Image.alpha_composite(img, overlay_dark)
        draw = ImageDraw.Draw(img)
        # Fuente grande (impact)
        fsize = int(h * 0.075)
        font = None
        for rf in fuentes:
            if os.path.exists(rf):
                try: font = ImageFont.truetype(rf, fsize); break
                except: continue
        if not font: font = ImageFont.load_default()
        # Envolver el texto en líneas
        palabras = frase.upper().split()
        lineas, actual = [], ""
        for p in palabras:
            prueba = (actual + " " + p).strip()
            bb = draw.textbbox((0,0), prueba, font=font)
            if bb[2]-bb[0] > w*0.85 and actual:
                lineas.append(actual); actual = p
            else:
                actual = prueba
        if actual: lineas.append(actual)
        # Dibujar centrado verticalmente
        alto_linea = int(fsize * 1.25)
        total_alto = alto_linea * len(lineas)
        y0 = (h - total_alto) // 2
        for idx, linea in enumerate(lineas):
            bb = draw.textbbox((0,0), linea, font=font)
            tw = bb[2]-bb[0]
            x = (w - tw) // 2
            y = y0 + idx*alto_linea
            # Contorno negro grueso + relleno amarillo (estilo viral)
            for dx in range(-3,4):
                for dy in range(-3,4):
                    draw.text((x+dx, y+dy), linea, font=font, fill=(0,0,0,255))
            draw.text((x, y), linea, font=font, fill=(255,220,40,255))
        img.convert('RGB').save(ruta_salida)
        return os.path.exists(ruta_salida)
    except Exception as e:
        print(f"   [HOOK] Error texto: {e}")
        return False

def _clip_pattern_interrupt(frase, img_congelada, ruta_salida, w, h, fps, carpeta, pil, fuentes, dur=1.6):
    """Formato A: golpe visual (flash + zoom punch) + texto + stinger."""
    try:
        # Frame con texto
        frame_txt = os.path.join(carpeta, f"_hook_txt_{random.randint(1000,9999)}.png")
        if not _texto_en_frame(img_congelada, frase, frame_txt, w, h, pil, fuentes):
            # Sin texto: usar la imagen congelada con flash
            frame_txt = img_congelada
        # Video: zoom punch (zoom rápido) + flash blanco al inicio
        total_frames = int(dur * fps)
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
              f"zoompan=z='1.0+0.4*on/{total_frames}':d={total_frames}:s={w}x{h}:fps={fps},"
              f"fade=t=in:st=0:d=0.08:color=white")
        vtmp = os.path.join(carpeta, f"_hook_v_{random.randint(1000,9999)}.mp4")
        cmd = ['ffmpeg','-y','-loop','1','-i', frame_txt,
               '-vf', vf, '-t', str(dur), '-r', str(fps),
               '-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p', vtmp]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not _clip_valido(vtmp): return None
        # Stinger
        stinger = os.path.join(carpeta, f"_hook_s_{random.randint(1000,9999)}.mp3")
        _generar_stinger(stinger, dur, "whoosh")
        # Mux audio
        if os.path.exists(stinger):
            cmd2 = ['ffmpeg','-y','-i', vtmp,'-i', stinger,
                    '-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-shortest', ruta_salida]
            subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Sin stinger: agregar silencio
            cmd2 = ['ffmpeg','-y','-i', vtmp,'-f','lavfi','-i','anullsrc=r=44100:cl=stereo',
                    '-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-shortest', ruta_salida]
            subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ruta_salida if _clip_valido(ruta_salida) else None
    except Exception as e:
        print(f"   [HOOK] Error pattern interrupt: {e}")
        return None

def _clip_flash_forward(frase, img_teaser, ruta_salida, w, h, fps, carpeta, pil, fuentes, dur=1.8):
    """Formato B: corte a imagen teaser + frase gancho + stinger grave."""
    try:
        frame_txt = os.path.join(carpeta, f"_ff_txt_{random.randint(1000,9999)}.png")
        if not _texto_en_frame(img_teaser, frase, frame_txt, w, h, pil, fuentes):
            frame_txt = img_teaser
        total_frames = int(dur * fps)
        # Efecto distinto: leve sacudida + desaturación (teaser inquietante)
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
              f"zoompan=z='1.15-0.1*on/{total_frames}':d={total_frames}:s={w}x{h}:fps={fps},"
              f"fade=t=in:st=0:d=0.15,fade=t=out:st={dur-0.2:.2f}:d=0.2")
        vtmp = os.path.join(carpeta, f"_ff_v_{random.randint(1000,9999)}.mp4")
        cmd = ['ffmpeg','-y','-loop','1','-i', frame_txt,
               '-vf', vf, '-t', str(dur), '-r', str(fps),
               '-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p', vtmp]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not _clip_valido(vtmp): return None
        stinger = os.path.join(carpeta, f"_ff_s_{random.randint(1000,9999)}.mp3")
        _generar_stinger(stinger, dur, "impact")
        if os.path.exists(stinger):
            cmd2 = ['ffmpeg','-y','-i', vtmp,'-i', stinger,
                    '-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-shortest', ruta_salida]
        else:
            cmd2 = ['ffmpeg','-y','-i', vtmp,'-f','lavfi','-i','anullsrc=r=44100:cl=stereo',
                    '-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-shortest', ruta_salida]
        subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ruta_salida if _clip_valido(ruta_salida) else None
    except Exception as e:
        print(f"   [HOOK] Error flash forward: {e}")
        return None


def insertar_hooks_retencion(ruta_video_entrada, ruta_video_salida, hooks_frases,
                              imagenes_escenas, carpeta, w, h, fps,
                              pil_disponible, fuentes, es_short=False):
    """
    Inserta hooks de retención en el video.
    - hooks_frases: lista de frases gancho generadas por Gemini (1ra = hook inicial fuerte)
    - imagenes_escenas: rutas de las imágenes de las escenas (para teasers del flash-forward)
    Devuelve True si insertó hooks; si algo falla, copia el original y devuelve False.
    NUNCA rompe el video.
    """
    import shutil
    try:
        dur_video = _dur(ruta_video_entrada)
        if dur_video < 5 or not hooks_frases:
            shutil.copy(ruta_video_entrada, ruta_video_salida)
            return False

        # ── Decidir cuántos re-hooks según duración ──
        # Hook inicial siempre. Re-hooks intermedios: ~1 cada 75s (largos), 1 max (shorts)
        frase_inicial = hooks_frases[0] if hooks_frases else None
        frases_intermedias = hooks_frases[1:] if len(hooks_frases) > 1 else []

        if es_short:
            n_rehooks = min(1, len(frases_intermedias))
        else:
            n_rehooks = min(len(frases_intermedias), max(1, int(dur_video // 75)))

        # ── Calcular puntos de inserción (evitar los primeros 5s y los últimos 8s) ──
        puntos = []
        if n_rehooks > 0:
            inicio_zona = 8.0
            fin_zona = dur_video - 8.0
            if fin_zona > inicio_zona:
                paso = (fin_zona - inicio_zona) / (n_rehooks + 1)
                for k in range(1, n_rehooks + 1):
                    puntos.append(round(inicio_zona + paso * k, 2))

        # ── Cortar el video en segmentos por los puntos, e intercalar hooks ──
        segmentos = []  # lista ordenada de rutas (segmentos de video + clips hook)
        rnd = random.Random(os.path.basename(carpeta) + "hooks")

        # 1. Hook inicial (se antepone al video completo)
        partes_finales = []
        if frase_inicial:
            img0 = imagenes_escenas[0] if imagenes_escenas else None
            if img0 and os.path.exists(img0):
                hook_ini = os.path.join(carpeta, "_hook_inicial.mp4")
                # El hook inicial siempre es pattern interrupt fuerte
                r = _clip_pattern_interrupt(frase_inicial, img0, hook_ini, w, h, fps,
                                            carpeta, pil_disponible, fuentes, dur=2.0)
                if r:
                    partes_finales.append(r)

        # 2. Cortar el video en los puntos y meter re-hooks entre segmentos
        cortes = [0.0] + puntos + [dur_video]
        for i in range(len(cortes) - 1):
            ini, fin = cortes[i], cortes[i+1]
            seg = os.path.join(carpeta, f"_seg_{i:02d}.mp4")
            cmd = ['ffmpeg','-y','-i', ruta_video_entrada,
                   '-ss', str(ini), '-to', str(fin),
                   '-c:v','libx264','-preset','veryfast','-crf','22',
                   '-c:a','aac','-b:a','192k','-r',str(fps), seg]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if _clip_valido(seg):
                partes_finales.append(seg)
            # Insertar re-hook después de este segmento (excepto el último)
            if i < len(puntos) and i < len(frases_intermedias):
                frase = frases_intermedias[i]
                img_teaser = rnd.choice(imagenes_escenas) if imagenes_escenas else None
                if img_teaser and os.path.exists(img_teaser):
                    hook_path = os.path.join(carpeta, f"_rehook_{i:02d}.mp4")
                    # Alternar aleatoriamente formato A y B
                    if rnd.random() < 0.5:
                        r = _clip_pattern_interrupt(frase, img_teaser, hook_path, w, h, fps,
                                                    carpeta, pil_disponible, fuentes)
                    else:
                        r = _clip_flash_forward(frase, img_teaser, hook_path, w, h, fps,
                                                carpeta, pil_disponible, fuentes)
                    if r:
                        partes_finales.append(r)

        if len(partes_finales) < 2:
            shutil.copy(ruta_video_entrada, ruta_video_salida)
            return False

        # 3. Concatenar todo (segmentos + hooks) en orden
        lista = os.path.join(carpeta, "_hooks_concat.txt")
        with open(lista, "w") as f:
            for p in partes_finales:
                f.write(f"file '{p}'\n")
        cmd_concat = ['ffmpeg','-y','-f','concat','-safe','0','-i', lista,
                      '-c:v','libx264','-preset','veryfast','-crf','22',
                      '-c:a','aac','-b:a','192k','-r',str(fps), ruta_video_salida]
        subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Limpiar temporales
        for p in partes_finales:
            try: os.remove(p)
            except: pass
        try: os.remove(lista)
        except: pass

        if _clip_valido(ruta_video_salida, min_dur=dur_video*0.8):
            n_total = len([x for x in partes_finales]) 
            print(f"   [HOOKS] Insertados: 1 inicial + {len(puntos)} re-hooks (formatos alternados)")
            return True
        else:
            shutil.copy(ruta_video_entrada, ruta_video_salida)
            return False
    except Exception as e:
        print(f"   [HOOKS] Error general, video sin hooks: {e}")
        try:
            import shutil
            shutil.copy(ruta_video_entrada, ruta_video_salida)
        except: pass
        return False
