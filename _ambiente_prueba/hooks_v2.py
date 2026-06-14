"""
MÓDULO DE HOOKS DE RETENCIÓN V2 — enfoque correcto (integrado al pipeline)
Inserta hooks ENTRE escenas (límites naturales), recalculando audio y subtítulos.

Diferencias clave vs V1:
  - Los hooks se insertan en los límites de escena (NO cortan frases a la mitad)
  - El audio de narración se PARTE en esos puntos e inserta silencio+stinger
  - Los subtítulos se recalculan sumando el desplazamiento de cada hook
  - Se concatena todo de una vez (sin re-encodes múltiples del video final)

Función principal: planificar_hooks() decide dónde van; el worker usa el plan
para construir los clips y el audio ya con los hooks integrados.
"""
import os, subprocess, random

def _dur(ruta):
    try:
        r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                            '-of','csv=p=0', ruta], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0

def _clip_valido(ruta, min_dur=0.2):
    return os.path.exists(ruta) and os.path.getsize(ruta) > 1000 and _dur(ruta) >= min_dur


def planificar_hooks(num_escenas, duraciones_escenas, hooks_frases, es_short, dur_hook=1.8):
    """
    Decide DÓNDE caen los re-hooks (en qué límites de escena) y con qué frase/formato.
    Devuelve:
      - hook_inicial: frase del hook inicial (o None)
      - inserciones: lista de dicts {despues_de_escena, frase, formato, dur}
        'despues_de_escena' = índice de escena tras la cual se inserta el re-hook
    NO toca archivos; solo planifica. Determinista por semilla (reproducible).
    """
    frase_inicial = hooks_frases[0] if hooks_frases else None
    frases_inter = [f for f in hooks_frases[1:] if f and str(f).strip()]

    dur_total = sum(duraciones_escenas) if duraciones_escenas else 0
    if dur_total < 5 or num_escenas < 2:
        return frase_inicial, []  # solo hook inicial, sin re-hooks

    # Cuántos re-hooks
    if es_short:
        n = min(1, len(frases_inter))
    else:
        n = min(len(frases_inter), max(1, int(dur_total // 75)))
    if n <= 0:
        return frase_inicial, []

    # Tiempos objetivo (repartidos), evitando el inicio (primeras escenas) y el final
    inicio_t = max(8.0, duraciones_escenas[0])
    fin_t = dur_total - 8.0
    if fin_t <= inicio_t:
        return frase_inicial, []
    paso = (fin_t - inicio_t) / (n + 1)
    tiempos_objetivo = [inicio_t + paso * k for k in range(1, n + 1)]

    # Para cada tiempo objetivo, encontrar el LÍMITE DE ESCENA más cercano
    # (acumulado de duraciones). Así el hook cae entre escenas, no a media frase.
    acum = []
    s = 0.0
    for d in duraciones_escenas:
        s += d
        acum.append(s)  # acum[i] = tiempo donde TERMINA la escena i

    inserciones = []
    escenas_usadas = set()
    rnd = random.Random("hooksplan")
    for idx, t_obj in enumerate(tiempos_objetivo):
        # buscar la escena cuyo final esté más cerca del tiempo objetivo
        mejor_i, mejor_dist = None, 1e9
        for i, t_fin in enumerate(acum[:-1]):  # no tras la última escena
            if i in escenas_usadas:
                continue
            dist = abs(t_fin - t_obj)
            if dist < mejor_dist:
                mejor_dist, mejor_i = dist, i
        if mejor_i is None:
            continue
        escenas_usadas.add(mejor_i)
        frase = frases_inter[idx] if idx < len(frases_inter) else frases_inter[-1]
        # Alternar formato A (pattern interrupt) y B (flash-forward)
        formato = "A" if rnd.random() < 0.5 else "B"
        inserciones.append({
            "despues_de_escena": mejor_i,
            "frase": frase,
            "formato": formato,
            "dur": dur_hook,
        })

    # Ordenar por escena
    inserciones.sort(key=lambda x: x["despues_de_escena"])
    return frase_inicial, inserciones


def recalcular_srt(ruta_srt_in, ruta_srt_out, inserciones, duraciones_escenas, dur_hook_inicial):
    """
    Desplaza los tiempos del SRT para compensar los hooks insertados.
    - El hook inicial desplaza TODO el SRT hacia adelante (dur_hook_inicial).
    - Cada re-hook tras la escena i desplaza los subtítulos posteriores a ese punto.
    """
    if not os.path.exists(ruta_srt_in):
        return False
    try:
        # Calcular tiempo de fin de cada escena (para saber a partir de qué segundo desplazar)
        acum = []
        s = 0.0
        for d in duraciones_escenas:
            s += d
            acum.append(s)

        # Lista de (tiempo_original, desplazamiento_a_aplicar_desde_ahi)
        desfases = []
        for ins in inserciones:
            i = ins["despues_de_escena"]
            if i < len(acum):
                desfases.append((acum[i], ins["dur"]))
        desfases.sort()

        def nuevo_t(t):
            # Desplazamiento del hook inicial + los re-hooks anteriores a t
            extra = dur_hook_inicial
            for t_ins, d in desfases:
                if t > t_ins:
                    extra += d
            return t + extra

        def parse_t(s):
            h, m, resto = s.split(":")
            seg, ms = resto.split(",")
            return int(h)*3600 + int(m)*60 + int(seg) + int(ms)/1000.0

        def fmt_t(t):
            h = int(t // 3600); t -= h*3600
            m = int(t // 60); t -= m*60
            seg = int(t); ms = int(round((t - seg)*1000))
            if ms >= 1000: seg += 1; ms = 0
            return f"{h:02d}:{m:02d}:{seg:02d},{ms:03d}"

        with open(ruta_srt_in, encoding="utf-8") as f:
            lineas = f.read().split("\n")
        out = []
        for ln in lineas:
            if "-->" in ln:
                a, b = ln.split("-->")
                ta = nuevo_t(parse_t(a.strip()))
                tb = nuevo_t(parse_t(b.strip()))
                out.append(f"{fmt_t(ta)} --> {fmt_t(tb)}")
            else:
                out.append(ln)
        with open(ruta_srt_out, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        return True
    except Exception as e:
        print(f"   [HOOKS] Error recalculando SRT: {e}")
        return False


# ═══════════ GENERACIÓN DE CLIPS DE HOOK ═══════════
def _generar_stinger(ruta_salida, dur=1.2, tipo="whoosh"):
    try:
        if tipo == "whoosh":
            filtro = (f"anoisesrc=d={dur}:c=pink:a=0.3,"
                      f"afade=t=in:d=0.3,afade=t=out:st={dur*0.5:.2f}:d={dur*0.5:.2f},"
                      f"highpass=f=200,lowpass=f=3000")
        else:
            filtro = f"sine=frequency=80:duration={dur},afade=t=out:st=0.1:d={dur-0.1:.2f}"
        cmd = ['ffmpeg','-y','-f','lavfi','-i', filtro, '-ar','44100','-ac','2','-q:a','5', ruta_salida]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(ruta_salida)
    except Exception:
        return False

def _texto_en_frame(ruta_img, frase, ruta_salida, w, h, pil, fuentes):
    if not pil or not frase:
        return False
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.open(ruta_img).convert('RGBA').resize((w, h))
        img = Image.alpha_composite(img, Image.new('RGBA', img.size, (0,0,0,120)))
        draw = ImageDraw.Draw(img)
        fsize = int(h * 0.072)
        font = None
        for rf in fuentes:
            if os.path.exists(rf):
                try: font = ImageFont.truetype(rf, fsize); break
                except: continue
        if not font: font = ImageFont.load_default()
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
        alto_l = int(fsize*1.25)
        y0 = (h - alto_l*len(lineas))//2
        for idx, l in enumerate(lineas):
            bb = draw.textbbox((0,0), l, font=font); tw = bb[2]-bb[0]
            x = (w-tw)//2; y = y0 + idx*alto_l
            for dx in range(-3,4):
                for dy in range(-3,4):
                    draw.text((x+dx,y+dy), l, font=font, fill=(0,0,0,255))
            draw.text((x,y), l, font=font, fill=(255,220,40,255))
        img.convert('RGB').save(ruta_salida)
        return os.path.exists(ruta_salida)
    except Exception as e:
        print(f"   [HOOK] texto: {e}")
        return False

def generar_clip_hook(frase, img, ruta_salida, w, h, fps, carpeta, pil, fuentes, formato="A", dur=1.8):
    """Genera UN clip de hook (visual + stinger), audio EXACTO = dur. Formato A o B."""
    try:
        frame = os.path.join(carpeta, f"_hkf_{random.randint(1000,99999)}.png")
        if not _texto_en_frame(img, frase, frame, w, h, pil, fuentes):
            frame = img
        tf = int(dur*fps)
        if formato == "A":  # pattern interrupt: zoom punch + flash blanco
            vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                  f"zoompan=z='1.0+0.4*on/{tf}':d={tf}:s={w}x{h}:fps={fps},"
                  f"fade=t=in:st=0:d=0.08:color=white")
            tipo_s = "whoosh"
        else:  # flash-forward: zoom out + fades (teaser)
            vf = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                  f"zoompan=z='1.15-0.1*on/{tf}':d={tf}:s={w}x{h}:fps={fps},"
                  f"fade=t=in:st=0:d=0.15,fade=t=out:st={dur-0.2:.2f}:d=0.2")
            tipo_s = "impact"
        vtmp = os.path.join(carpeta, f"_hkv_{random.randint(1000,99999)}.mp4")
        subprocess.run(['ffmpeg','-y','-loop','1','-i', frame,'-vf', vf,'-t', str(dur),
                        '-r', str(fps),'-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p', vtmp],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not _clip_valido(vtmp): return None
        stinger = os.path.join(carpeta, f"_hks_{random.randint(1000,99999)}.mp3")
        _generar_stinger(stinger, dur, tipo_s)
        if os.path.exists(stinger):
            subprocess.run(['ffmpeg','-y','-i', vtmp,'-i', stinger,'-map','0:v','-map','1:a',
                            '-c:v','copy','-c:a','aac','-b:a','192k','-af','apad','-t', str(dur), ruta_salida],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['ffmpeg','-y','-i', vtmp,'-f','lavfi','-i','anullsrc=r=44100:cl=stereo',
                            '-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-t', str(dur), ruta_salida],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for t in [frame, vtmp, stinger]:
            if t != img:
                try: os.remove(t)
                except: pass
        return ruta_salida if _clip_valido(ruta_salida) else None
    except Exception as e:
        print(f"   [HOOK] clip {formato}: {e}")
        return None


def construir_audio_con_hooks(ruta_audio_in, ruta_audio_out, inserciones, duraciones_escenas,
                               dur_hook_inicial, carpeta, hook_inicial_presente):
    """
    Reconstruye el audio de narración insertando, en cada punto de hook, un tramo
    de silencio de duración = dur del hook (para que el audio NO pise el hook visual,
    y narración + video queden sincronizados).
    El hook visual trae su propio stinger en SU pista, así que aquí solo insertamos
    silencio en la narración (el stinger del clip suena durante ese silencio).
    """
    try:
        # Puntos (en segundos del audio original) donde cortar e insertar silencio
        acum = []
        s = 0.0
        for d in duraciones_escenas:
            s += d
            acum.append(s)
        cortes = []  # (tiempo_corte, duracion_silencio)
        if hook_inicial_presente:
            cortes.append((0.0, dur_hook_inicial))  # silencio al inicio
        for ins in inserciones:
            i = ins["despues_de_escena"]
            if i < len(acum):
                cortes.append((acum[i], ins["dur"]))
        cortes.sort()
        if not cortes:
            import shutil; shutil.copy(ruta_audio_in, ruta_audio_out); return True

        dur_audio = _dur(ruta_audio_in)
        # Construir segmentos de narración entre cortes + silencios
        partes = []
        t_prev = 0.0
        idx = 0
        for (t_corte, dur_sil) in cortes:
            # Segmento de narración de t_prev a t_corte
            if t_corte > t_prev + 0.05:
                seg = os.path.join(carpeta, f"_au_seg_{idx}.wav")
                subprocess.run(['ffmpeg','-y','-i', ruta_audio_in,'-ss', str(t_prev),'-to', str(t_corte),
                                '-c:a','pcm_s16le','-ar','44100','-ac','2', seg],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if _clip_valido(seg, 0.05): partes.append(seg)
                idx += 1
            # Silencio del hook
            sil = os.path.join(carpeta, f"_au_sil_{idx}.wav")
            subprocess.run(['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=44100:cl=stereo',
                            '-t', str(dur_sil),'-c:a','pcm_s16le','-ar','44100','-ac','2', sil],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if _clip_valido(sil, 0.05): partes.append(sil)
            idx += 1
            t_prev = t_corte
        # Resto de narración
        if dur_audio > t_prev + 0.05:
            seg = os.path.join(carpeta, f"_au_seg_{idx}.wav")
            subprocess.run(['ffmpeg','-y','-i', ruta_audio_in,'-ss', str(t_prev),
                            '-c:a','pcm_s16le','-ar','44100','-ac','2', seg],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if _clip_valido(seg, 0.05): partes.append(seg)

        if len(partes) < 2:
            import shutil; shutil.copy(ruta_audio_in, ruta_audio_out); return True

        # Concatenar con el filtro concat de audio (más robusto que el demuxer para AAC)
        inputs = []
        for p in partes:
            inputs.extend(['-i', p])
        n = len(partes)
        filtro = "".join(f"[{k}:a]" for k in range(n)) + f"concat=n={n}:v=0:a=1[out]"
        cmd = ['ffmpeg','-y'] + inputs + ['-filter_complex', filtro, '-map','[out]',
               '-c:a','aac','-b:a','192k', ruta_audio_out]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for p in partes:
            try: os.remove(p)
            except: pass
        return _clip_valido(ruta_audio_out, 1.0)
    except Exception as e:
        print(f"   [HOOKS] Error audio: {e}")
        try:
            import shutil; shutil.copy(ruta_audio_in, ruta_audio_out)
        except: pass
        return False
