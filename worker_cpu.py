import requests
import time
import os
import json
import base64
import subprocess
import random
import uuid

# 🚀 CONFIGURACIÓN CORPORATE TECH V8.4.7 - MOTOR HÍBRIDO (ERRADICACIÓN ALIENÍGENA)
PEXELS_API_KEY_LOCAL = "jkdA4ukl8lt61jzm39P5D6tmNzYDHtQMlk8kwEe7mUhPB4jbWtw552an"

IP_GRAFICA_1 = "192.168.0.215"
IP_GRAFICA_2 = "192.168.0.215"
IP_GRAFICA   = IP_GRAFICA_1
RENDER_URL   = "https://prompt-engineer-system-l2r6.onrender.com"
CARPETA_LOCAL  = "C:\\DarkFactory_Renders"
CARPETA_ASSETS = "C:\\DarkFactory_ASSETS"

VOLUMEN_MUSICA = "0.15"

os.environ['no_proxy'] = f'{IP_GRAFICA_1},{IP_GRAFICA_2},localhost,127.0.0.1,render.com'

for _carpeta in [CARPETA_LOCAL, CARPETA_ASSETS]:
    if not os.path.exists(_carpeta):
        os.makedirs(_carpeta)

# ══════════════════════════════════════════════════════════════
# VELOCIDAD DE LOCUCIÓN POR CANAL (palabras por minuto reales)
# ══════════════════════════════════════════════════════════════
VELOCIDAD_PPM = {
    "la viuda":         85,
    "monkygraff":       140,
    "filtradmx":        130,
    "filtrado mx":      130,
    "laesquinarandom":  155,
    "laesquina random": 155,
    "default":          120,
}

PAUSA_PUNTUACION = {
    ".":  0.55,   
    "…":  0.70,   
    "...": 0.70,  
    ",":  0.20,   
    ";":  0.30,   
    "!":  0.40,   
    "?":  0.40,   
    ":":  0.25,   
}

# ── CIRCUIT BREAKER ─────────────────────────────────────────
_errores_render     = 0
_MAX_ERRORES_RENDER = 5
_PAUSA_EMERGENCIA   = 300
_ultimo_error_429   = 0

def _registrar_error_render():
    global _errores_render
    _errores_render += 1
    if _errores_render >= _MAX_ERRORES_RENDER:
        print(f"[CIRCUIT BREAKER] {_errores_render} errores consecutivos. Pausando {_PAUSA_EMERGENCIA}s...")
        time.sleep(_PAUSA_EMERGENCIA)
        _errores_render = 0

def _resetear_errores_render():
    global _errores_render
    _errores_render = 0

# ══════════════════════════════════════════════════════════════
# MOTORES MATEMÁTICOS Y LECTURA DE TIEMPO
# ══════════════════════════════════════════════════════════════

def _obtener_velocidad_canal(marca):
    marca_lower = marca.lower().replace(" ", "")
    for canal, ppm in VELOCIDAD_PPM.items():
        if canal.replace(" ", "") in marca_lower or marca_lower in canal.replace(" ", ""):
            return ppm
    return VELOCIDAD_PPM["default"]

def _obtener_duracion_audio(ruta_audio, texto_locucion, marca_audio):
    try:
        ruta_safe = ruta_audio.replace("\\", "/")
        cmd_dur = [
            'ffprobe', '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            ruta_safe
        ]
        dur_str = subprocess.check_output(cmd_dur, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        duracion_real = float(dur_str)
        if duracion_real < 5.0:
            raise ValueError("Duración leída demasiado corta (posible corrupción).")
        print(f"   [SYNC] FFprobe leyó duración exacta: {duracion_real:.2f}s")
        return duracion_real
    except Exception as e:
        num_palabras = len(texto_locucion.split())
        ppm = _obtener_velocidad_canal(marca_audio)
        dur_estimada = (num_palabras / ppm) * 60.0
        print(f"   [⚠️ ALERTA CRÍTICA] FFprobe falló. Usando Motor Matemático: {dur_estimada:.2f}s")
        return dur_estimada

def _generar_srt_calibrado(texto_completo, dur_total_audio, marca, ruta_srt):
    import re
    frases_raw = re.split(r'(?<=[.!?])\s+', texto_completo.strip())
    frases_raw = [f.strip() for f in frases_raw if f.strip()]
    chunks = []
    for frase in frases_raw:
        palabras = frase.split()
        if len(palabras) <= 5:
            chunks.append(frase)
        else:
            for j in range(0, len(palabras), 5):
                parte = " ".join(palabras[j:j+5])
                if parte.strip():
                    chunks.append(parte)
    if not chunks:
        return
    total_palabras = sum(len(c.split()) for c in chunks)
    if total_palabras == 0:
        return
    duraciones = [(len(c.split()) / total_palabras) * dur_total_audio for c in chunks]
    duraciones = [max(d, 0.5) for d in duraciones]
    suma = sum(duraciones)
    if suma > dur_total_audio:
        duraciones = [d * dur_total_audio / suma for d in duraciones]
    tiempo = 0.0
    total  = len(chunks)
    with open(ruta_srt, "w", encoding="utf-8") as srt:
        for idx, (chunk, dur) in enumerate(zip(chunks, duraciones)):
            ini   = tiempo
            fin_t = dur_total_audio if idx == total - 1 else min(tiempo + dur, dur_total_audio)
            if ini >= fin_t:
                continue
            h_i,m_i=int(ini//3600),int((ini%3600)//60)
            s_i,ms_i=int(ini%60),int((ini%1)*1000)
            h_f,m_f=int(fin_t//3600),int((fin_t%3600)//60)
            s_f,ms_f=int(fin_t%60),int((fin_t%1)*1000)
            srt.write(
                f"{idx+1}\n"
                f"{h_i:02d}:{m_i:02d}:{s_i:02d},{ms_i:03d} --> "
                f"{h_f:02d}:{m_f:02d}:{s_f:02d},{ms_f:03d}\n"
                f"{chunk.upper()}\n\n"
            )
            tiempo = fin_t

def _generar_subtitulos_shorts(ruta_audio, texto_locucion, escenas_texto, marca, carpeta_reciente, dur_total):
    ruta_srt = os.path.join(carpeta_reciente, "subtitulos.srt").replace("\\", "/")

    print("📝 Intentando sync real con Whisper...")
    try:
        cmd_whisper = [
            "whisper", ruta_audio,
            "--language", "es",
            "--output_format", "srt",
            "--output_dir", carpeta_reciente,
            "--model", "small",        
            "--max_line_width", "5",   
            "--max_line_count", "1"
        ]
        resultado_whisper = subprocess.run(cmd_whisper, capture_output=True, timeout=300)
        srt_whisper = os.path.join(carpeta_reciente, "locucion.srt")
        if os.path.exists(srt_whisper) and os.path.getsize(srt_whisper) > 0:
            os.replace(srt_whisper, ruta_srt)
            print(f"   [OK] Whisper generó sync real. Modelo: small | Canal: {marca}")
            return ruta_srt
        else:
            print("   [WHISPER] Archivo SRT vacío o no generado.")
    except FileNotFoundError:
        print("   [WHISPER] No instalado en este sistema.")
    except subprocess.TimeoutExpired:
        print("   [WHISPER] Timeout — audio demasiado largo para el modelo base.")
    except Exception as e:
        print(f"   [WHISPER] Error inesperado: {e}")

    print(f"   [FALLBACK] Usando estimación calibrada para canal '{marca}'...")
    if escenas_texto and len(escenas_texto) > 0:
        texto_completo = " ".join(escenas_texto)
    else:
        texto_completo = texto_locucion

    if not texto_completo.strip():
        print("   [ERROR] Texto vacío. No se pueden generar subtítulos.")
        return None

    _generar_srt_calibrado(texto_completo, dur_total, marca, ruta_srt)
    return ruta_srt

# ══════════════════════════════════════════════════════════════
# GENERADORES DE DOCUMENTOS WORD
# ══════════════════════════════════════════════════════════════

def _generar_word_paquete(paquete, marca, formato, carpeta):
    import tempfile, subprocess as sp
    es_largo   = "16:9" in formato
    carpeta_js = carpeta.replace("\\", "/")
    ruta_out   = f"{carpeta_js}/paquete_publicacion.docx"

    tmp_json = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8')
    json.dump(paquete, tmp_json, ensure_ascii=False)
    tmp_json.close()
    ruta_json  = tmp_json.name.replace("\\", "/")
    fmt_label  = "Largo 16:9" if es_largo else "Short 9:16"
    es_largo_js = "true" if es_largo else "false"

    js = f"""
const {{ Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, ShadingType }} = require('docx');
const fs = require('fs');
const p = JSON.parse(fs.readFileSync('{ruta_json}', 'utf8'));
const CR="C0392B",CN="1A1A1A",CG="F5F5F5",CA="2980B9";
function sec(t){{ return new Paragraph({{ children:[new TextRun({{text:t,bold:true,color:"FFFFFF",size:26,font:"Arial"}})], shading:{{fill:CR,type:ShadingType.CLEAR}}, spacing:{{before:300,after:100}}, indent:{{left:200,right:200}} }}); }}
function blq(t,it=false,c=CN){{ return new Paragraph({{ children:[new TextRun({{text:t||"",size:22,font:"Arial",italics:it,color:c}})], shading:{{fill:CG,type:ShadingType.CLEAR}}, spacing:{{before:80,after:160}}, indent:{{left:200,right:200}} }}); }}
function sep(){{ return new Paragraph({{ border:{{bottom:{{style:BorderStyle.SINGLE,size:2,color:"DDDDDD"}}}}, spacing:{{before:160,after:160}} }}); }}
const ch=[
  new Paragraph({{children:[new TextRun({{text:"PAQUETE DE PUBLICACION",bold:true,size:40,font:"Arial",color:CR}})],alignment:AlignmentType.CENTER,spacing:{{before:0,after:60}}}}),
  new Paragraph({{children:[new TextRun({{text:"Canal: {marca}  |  Formato: {fmt_label}",size:20,font:"Arial",color:"777777"}})],alignment:AlignmentType.CENTER,spacing:{{before:0,after:40}}}}),
  new Paragraph({{border:{{bottom:{{style:BorderStyle.SINGLE,size:6,color:CR}}}},spacing:{{before:0,after:300}}}}),
  sec("TITULO SEO OPTIMIZADO"),
  new Paragraph({{children:[new TextRun({{text:p.titulo_final||"",bold:true,size:26,font:"Arial",color:CN}})],shading:{{fill:CG,type:ShadingType.CLEAR}},spacing:{{before:100,after:200}},indent:{{left:200,right:200}}}}),
  sep(),
  sec("DESCRIPCION COMPLETA"),
  ...(p.descripcion||"").split("\\n\\n").filter(x=>x.trim()).map(x=>new Paragraph({{children:[new TextRun({{text:x.trim(),size:22,font:"Arial",color:CN}})],shading:{{fill:CG,type:ShadingType.CLEAR}},spacing:{{before:80,after:80}},indent:{{left:200,right:200}}}})),
  sep(),sec("HASHTAGS"),blq(p.hashtags||"",false,CA),
  sep(),sec("KEYWORDS"),blq(p.keywords||""),
  sep(),sec("PRIMER COMENTARIO FIJO"),blq(p.primer_comentario||"",true),
  sep(),sec("PROMPT HOOK"),blq(p.prompt_hook||"",true,"555555"),
];
if({es_largo_js} && p.prompt_miniatura_A){{
  ch.push(sep(),sec("MINIATURA A"),blq(p.prompt_miniatura_A||"",true,"555555"),
          sec("MINIATURA B"),blq(p.prompt_miniatura_B||"",true,"555555"),
          sec("MINIATURA C"),blq(p.prompt_miniatura_C||"",true,"555555"));
}}
ch.push(new Paragraph({{border:{{top:{{style:BorderStyle.SINGLE,size:6,color:CR}}}},spacing:{{before:300,after:100}}}}));
ch.push(new Paragraph({{children:[new TextRun({{text:"Generado por Dark Factory — Sistema Pinpinela",size:18,font:"Arial",color:"AAAAAA",italics:true}})],alignment:AlignmentType.CENTER}}));
const doc=new Document({{styles:{{default:{{document:{{run:{{font:"Arial",size:22}}}}}}}},sections:[{{properties:{{page:{{size:{{width:12240,height:15840}},margin:{{top:1440,right:1440,bottom:1440,left:1440}}}}}},children:ch}}]}});
Packer.toBuffer(doc).then(buf=>{{fs.writeFileSync('{ruta_out}',buf);console.log('OK');}}).catch(e=>{{console.error(e);process.exit(1);}});
"""
    tmp_js = tempfile.NamedTemporaryFile(suffix='.js', delete=False, mode='w', encoding='utf-8')
    tmp_js.write(js)
    tmp_js.close()
    result = sp.run(['node', tmp_js.name], capture_output=True, text=True)
    os.unlink(tmp_js.name)
    os.unlink(tmp_json.name)
    if result.returncode != 0:
        raise Exception(result.stderr)

def _generar_word_guion(texto_locucion, marca, formato, tarea, carpeta):
    import tempfile, subprocess as sp
    es_largo   = "16:9" in formato
    carpeta_js = carpeta.replace("\\", "/")
    ruta_out   = f"{carpeta_js}/guion_completo.docx"
    fmt_label  = "Largo 16:9" if es_largo else "Short 9:16"

    guion_data = {
        "titulo":   tarea.get("titulo_sugerido", "Guion sin titulo"),
        "marca":    marca,
        "formato":  fmt_label,
        "escenas":  tarea.get("escenas", []),
        "locucion": texto_locucion
    }
    tmp_json = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8')
    json.dump(guion_data, tmp_json, ensure_ascii=False)
    tmp_json.close()
    ruta_json = tmp_json.name.replace("\\", "/")

    js = f"""
const {{ Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, ShadingType }} = require('docx');
const fs = require('fs');
const d = JSON.parse(fs.readFileSync('{ruta_json}', 'utf8'));
const CR="C0392B",CN="1A1A1A",CG="F5F5F5";
function sep(){{ return new Paragraph({{border:{{bottom:{{style:BorderStyle.SINGLE,size:1,color:"EEEEEE"}}}},spacing:{{before:60,after:60}}}}); }}
const ch=[
  new Paragraph({{children:[new TextRun({{text:"GUION COMPLETO",bold:true,size:40,font:"Arial",color:CR}})],alignment:AlignmentType.CENTER,spacing:{{before:0,after:60}}}}),
  new Paragraph({{children:[new TextRun({{text:"Canal: "+d.marca+"  |  Formato: "+d.formato,size:20,font:"Arial",color:"777777"}})],alignment:AlignmentType.CENTER,spacing:{{before:0,after:40}}}}),
  new Paragraph({{children:[new TextRun({{text:d.titulo,bold:true,size:28,font:"Arial",color:CN}})],alignment:AlignmentType.CENTER,shading:{{fill:CG,type:ShadingType.CLEAR}},spacing:{{before:100,after:60}},indent:{{left:200,right:200}}}}),
  new Paragraph({{border:{{bottom:{{style:BorderStyle.SINGLE,size:6,color:CR}}}},spacing:{{before:0,after:300}}}}),
];
if(d.escenas && d.escenas.length>0){{
  d.escenas.forEach(e=>{{
    ch.push(new Paragraph({{children:[new TextRun({{text:"ESCENA "+e.id_escena,bold:true,size:22,font:"Arial",color:CR}})],spacing:{{before:200,after:40}},indent:{{left:200}}}}));
    ch.push(new Paragraph({{children:[new TextRun({{text:"LOCUCION:",bold:true,size:20,font:"Arial",color:CN}})],spacing:{{before:40,after:20}},indent:{{left:200}}}}));
    ch.push(new Paragraph({{children:[new TextRun({{text:e.texto_locucion||"",size:20,font:"Arial",color:CN}})],shading:{{fill:CG,type:ShadingType.CLEAR}},spacing:{{before:20,after:40}},indent:{{left:200,right:200}}}}));
    ch.push(new Paragraph({{children:[new TextRun({{text:"PROMPT VISUAL:",bold:true,size:18,font:"Arial",color:"555555"}})],spacing:{{before:20,after:20}},indent:{{left:200}}}}));
    ch.push(new Paragraph({{children:[new TextRun({{text:e.prompt_visual||"",size:18,font:"Arial",color:"777777",italics:true}})],spacing:{{before:0,after:60}},indent:{{left:200,right:200}}}}));
    ch.push(sep());
  }});
}} else {{
  d.locucion.split("\\n").filter(p=>p.trim()).forEach(p=>{{
    ch.push(new Paragraph({{children:[new TextRun({{text:p.trim(),size:22,font:"Arial",color:CN}})],spacing:{{before:80,after:80}},indent:{{left:200,right:200}}}}));
  }});
}}
ch.push(new Paragraph({{children:[new TextRun({{text:"Generado por Dark Factory — Sistema Pinpinela",size:18,font:"Arial",color:"AAAAAA",italics:true}})],alignment:AlignmentType.CENTER,spacing:{{before:300}}}}));
const doc=new Document({{styles:{{default:{{document:{{run:{{font:"Arial",size:22}}}}}}}},sections:[{{properties:{{page:{{size:{{width:12240,height:15840}},margin:{{top:1440,right:1440,bottom:1440,left:1440}}}}}},children:ch}}]}});
Packer.toBuffer(doc).then(buf=>{{fs.writeFileSync('{ruta_out}',buf);console.log('OK');}}).catch(e=>{{console.error(e);process.exit(1);}});
"""
    tmp_js = tempfile.NamedTemporaryFile(suffix='.js', delete=False, mode='w', encoding='utf-8')
    tmp_js.write(js)
    tmp_js.close()
    result = sp.run(['node', tmp_js.name], capture_output=True, text=True)
    os.unlink(tmp_js.name)
    os.unlink(tmp_json.name)
    if result.returncode != 0:
        raise Exception(result.stderr)


# ══════════════════════════════════════════════════════════════
# BUCLE PRINCIPAL DE PROCESAMIENTO
# ══════════════════════════════════════════════════════════════

def procesar():
    try:
        res = requests.post(
            f"{RENDER_URL}/api/nodo/polling",
            json={"nodo_id": "XEON_ASSEMBLER"},
            timeout=400
        )
        if res.status_code == 429:
            print("[CIRCUIT BREAKER] 429 en polling — pausando 60s...")
            time.sleep(60)
            return
        if res.status_code != 200:
            _registrar_error_render()
            return
        _resetear_errores_render()
        data = res.json()

        if data.get("hay_trabajo"):
            tarea    = data["tarea"]
            tarea_id = tarea["id"]
            tipo_tarea = tarea.get("tipo", "IMAGEN")

            # ══════════════════════════════════════════════════
            # RUTA 1: ENSAMBLAJE DE ALTA FIDELIDAD
            # ══════════════════════════════════════════════════
            if tipo_tarea == "ENSAMBLAJE":
                print(f"\n🎬 [ENSAMBLAJE V8.4.7] Iniciando Motor Híbrido Multicapa...")

                texto_locucion = tarea.get("texto_locucion", "")
                marca_audio    = tarea.get("marca", "La Viuda")

                if not texto_locucion:
                    print("⚠️ No hay texto de locución en la tarea.")
                    return

                carpetas = [
                    os.path.join(CARPETA_LOCAL, d)
                    for d in os.listdir(CARPETA_LOCAL)
                    if os.path.isdir(os.path.join(CARPETA_LOCAL, d))
                ]
                if not carpetas:
                    return
                carpeta_reciente = max(carpetas, key=os.path.getmtime)

                ruta_formato = os.path.join(carpeta_reciente, "formato.txt")
                formato_ensamblaje = "9:16"
                if os.path.exists(ruta_formato):
                    with open(ruta_formato, "r") as f:
                        formato_ensamblaje = f.read().strip()

                es_largo_video = "16:9" in formato_ensamblaje
                w, h = (1024, 576) if es_largo_video else (576, 1024)

                carpeta_marca_assets = os.path.join(CARPETA_ASSETS, marca_audio)
                ruta_musica_fondo    = os.path.join(carpeta_marca_assets, "musica_fondo.mp3")
                ruta_intro_dinamico  = os.path.join(carpeta_marca_assets, "intro_169.mp4" if es_largo_video else "intro_916.mp4")
                ruta_outro_dinamico  = os.path.join(carpeta_marca_assets, "outro_169.mp4" if es_largo_video else "outro_916.mp4")
                ruta_audio           = os.path.join(carpeta_reciente, "locucion.mp3")

                print("🎙️ Generando audio con motor de voz local (XTTS)...")
                try:
                    import sys
                    sys.path.insert(0, "C:\\NODO_PINPINELA")
                    from voice_local import generar_audio_local
                    resultado = generar_audio_local(texto_locucion, marca_audio, ruta_audio)
                    if resultado:
                        ruta_audio = resultado
                        print(f"✅ Audio local generado: {ruta_audio}")
                    else:
                        print("⚠️ Error en voz local.")
                        return
                except Exception as e:
                    print(f"⚠️ Error voz local: {e}")
                    return

                archivos_escenas = sorted([
                    f for f in os.listdir(carpeta_reciente)
                    if f.startswith('escena_') and (f.endswith('.png') or f.endswith('.mp4'))
                ])
                num_escenas = len(archivos_escenas)
                if num_escenas == 0:
                    print("⚠️ No hay escenas PNG o MP4 en la carpeta.")
                    return

                duracion_audio = _obtener_duracion_audio(ruta_audio, texto_locucion, marca_audio)
                fps = 30

                def calcular_duraciones(num_imgs, dur_total, target_fps=30):
                    pesos = []
                    for i in range(num_imgs):
                        pos  = i / max(num_imgs - 1, 1)
                        peso = 0.7 + 0.6 * (1 - abs(pos - 0.5) * 2)
                        pesos.append(peso)
                    total_pesos = sum(pesos)

                    total_frames = int(dur_total * target_fps)
                    frames_asignados = 0
                    duraciones_finales = []

                    for i in range(num_imgs):
                        if i == num_imgs - 1:
                            frames_escena = total_frames - frames_asignados
                        else:
                            frames_escena = int(total_frames * (pesos[i] / total_pesos))

                        frames_asignados += frames_escena
                        duraciones_finales.append(frames_escena / target_fps)

                    return duraciones_finales

                duraciones_escenas = calcular_duraciones(num_escenas, duracion_audio, fps)

                efectos_por_tipo = {
                    'tension':    ['zoom_in_slow', 'pan_l_slow', 'pan_r_slow'],
                    'impacto':    ['zoom_in_fast', 'flash_zoom', 'shake'],
                    'transicion': ['slide_l', 'slide_r', 'slide_up', 'slide_down', 'fade_pan'],
                }

                def detectar_tipo_escena(texto):
                    texto = texto.lower()
                    palabras_impacto = [
                        'entonces', 'de repente', 'pero', 'jamás', 'nunca', 'murió',
                        'desapareció', 'encontraron', 'revelación', 'encontró',
                        'descubrió', 'confesó', 'ataque', 'golpe', 'disparo'
                    ]
                    palabras_tension = [
                        'silencio', 'oscuridad', 'nadie', 'solo', 'espera', 'escucha',
                        'sientes', 'sabes', 'algo', 'sombra', 'frío', 'miedo',
                        'extraño', 'raro', 'oculto', 'susurro'
                    ]
                    score_i = sum(1 for p in palabras_impacto if p in texto)
                    score_t = sum(1 for p in palabras_tension  if p in texto)
                    if score_i > score_t: return 'impacto'
                    if score_t > 0:       return 'tension'
                    return 'transicion'

                ultimo_efecto = [None]

                def elegir_efecto(tipo):
                    opciones = efectos_por_tipo[tipo][:]
                    if ultimo_efecto[0] in opciones and len(opciones) > 1:
                        opciones = [e for e in opciones if e != ultimo_efecto[0]]
                    efecto = random.choice(opciones)
                    ultimo_efecto[0] = efecto
                    return efecto

                def construir_filtro_movimiento(efecto, total_frames, fps, w, h):
                    es_largo = w > h
                    if efecto == 'zoom_in_slow':
                        return f"zoompan=z='1.20+0.05*sin(on/100)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'zoom_in_fast':
                        return f"zoompan=z='1.35+0.10*sin(on/80)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'flash_zoom':
                        return f"zoompan=z='1.45+0.10*cos(on/60)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'shake':
                        intensidad = 15 if es_largo else 10
                        return f"zoompan=z=1.30:x='iw/2-(iw/zoom/2)+{intensidad}*sin(on*2.5)':y='ih/2-(ih/zoom/2)+{intensidad//2}*cos(on*2.5)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'pan_l_slow':
                        dist = 0.10 if es_largo else 0.08
                        return f"zoompan=z=1.35:x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/120)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'pan_r_slow':
                        dist = 0.10 if es_largo else 0.08
                        return f"zoompan=z=1.35:x='iw/2-(iw/zoom/2)+(iw*{dist})*cos(on/120)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'slide_l':
                        dist = 0.14 if es_largo else 0.12
                        return f"zoompan=z=1.45:x='iw/2-(iw/zoom/2)+(iw*{dist})*sin(on/90)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'slide_r':
                        dist = 0.14 if es_largo else 0.12
                        return f"zoompan=z=1.45:x='iw/2-(iw/zoom/2)+(iw*{dist})*cos(on/90)':y='ih/2-(ih/zoom/2)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'slide_up':
                        dist = 0.14 if es_largo else 0.12
                        return f"zoompan=z=1.45:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+(ih*{dist})*sin(on/100)':d={total_frames}:fps={fps}:s={w}x{h}"
                    elif efecto == 'slide_down':
                        dist = 0.14 if es_largo else 0.12
                        return f"zoompan=z=1.45:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+(ih*{dist})*cos(on/100)':d={total_frames}:fps={fps}:s={w}x{h}"
                    else:
                        return f"zoompan=z=1.30:x='iw/2-(iw/zoom/2)+(iw*0.08)*sin(on/100)':y='ih/2-(ih/zoom/2)+(ih*0.08)*cos(on/100)':d={total_frames}:fps={fps}:s={w}x{h}"

                escenas_data   = tarea.get("escenas", [])
                textos_escenas = [e.get("texto_locucion", "") for e in escenas_data] if escenas_data else []
                clips_temp     = []
                
                es_cartoon_fx = (marca_audio.lower() in ["la esquina random", "laesquinarandom"])

                UMBRAL_SUB_EFECTOS = 12.0

                print(f"⚙️ Procesando {num_escenas} matrices visuales con CPU Xeon...")
                for i, archivo in enumerate(archivos_escenas):
                    path_origen = os.path.join(carpeta_reciente, archivo).replace("\\", "/")
                    path_clip   = os.path.join(carpeta_reciente, f"clip_{i:02d}.mp4")

                    texto_escena  = textos_escenas[i] if i < len(textos_escenas) else ""
                    tipo   = detectar_tipo_escena(texto_escena)
                    efecto = elegir_efecto(tipo)

                    dur_original = duraciones_escenas[i]
                    dur_exacta   = dur_original

                    if i == num_escenas - 1:
                        dur_exacta += 15.0  

                    total_frames = int(round(dur_exacta * fps)) 

                    if es_cartoon_fx:
                        glitch_fx = ""
                    else:
                        if tipo == 'impacto':
                            t_glitch = max(0.1, dur_original - 0.2)
                            t_negate = max(0.15, dur_original - 0.1)
                            glitch_fx = (
                                f",rgbashift=rh=20:bv=20:enable='between(t,{t_glitch:.3f},{dur_exacta:.3f})'"
                                f",negate=enable='between(t,{t_negate:.3f},{dur_exacta:.3f})'"
                            )
                        elif tipo == 'tension':
                            t_glitch  = max(0.1, dur_original - 0.3)
                            glitch_fx = f",rgbashift=rh=8:bv=8:enable='between(t,{t_glitch:.3f},{dur_exacta:.3f})'"
                        else:
                            glitch_fx = ""

                    if archivo.endswith('.png') and dur_exacta > UMBRAL_SUB_EFECTOS:
                        num_subs = 3 if dur_exacta > 20.0 else 2
                        dur_sub = dur_exacta / num_subs

                        efectos_sub = [efecto]
                        for _ in range(num_subs - 1):
                            efectos_sub.append(elegir_efecto(tipo))

                        sub_clips = []
                        escala_previa = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                        for k, efx in enumerate(efectos_sub):
                            sub_path    = os.path.join(carpeta_reciente, f"clip_{i:02d}_s{k}.mp4")
                            sub_frames  = int(round(dur_sub * fps))
                            mf_sub      = construir_filtro_movimiento(efx, sub_frames, fps, w, h)
                            glitch_sub = glitch_fx if k == num_subs - 1 else ""
                            vf_sub = f"{escala_previa}{mf_sub},fade=t=in:st=0:d=0.1,noise=alls=5:allf=t+u,vignette=PI/4,setpts=PTS-STARTPTS{glitch_sub}"
                            cmd_sub = [
                                'ffmpeg', '-y', '-i', path_origen,
                                '-vf', vf_sub, '-t', str(dur_sub),
                                '-c:v', 'libx264', '-preset', 'ultrafast',
                                '-threads', '0', '-pix_fmt', 'yuv420p', '-r', str(fps), sub_path
                            ]
                            subprocess.run(cmd_sub, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            sub_clips.append(sub_path)

                        list_sub = os.path.join(carpeta_reciente, f"subs_{i:02d}.txt")
                        with open(list_sub, "w") as flist:
                            for sc in sub_clips:
                                flist.write(f"file '{sc.replace(chr(92), '/')}'\n")
                        cmd_concat_sub = [
                            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_sub,
                            '-c', 'copy', path_clip
                        ]
                        subprocess.run(cmd_concat_sub, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        for sc in sub_clips:
                            try: os.remove(sc)
                            except: pass
                        try: os.remove(list_sub)
                        except: pass

                        clips_temp.append(path_clip)
                        print(f"   [OK] Escena {i+1} (SD-Dinamica {num_subs}x) — tipo:{tipo} efectos:{','.join(efectos_sub)}")
                        continue

                    if archivo.endswith('.png'):
                        escala_previa = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                        mf = construir_filtro_movimiento(efecto, total_frames, fps, w, h)
                        vf_string = f"{escala_previa}{mf},fade=t=in:st=0:d=0.1,noise=alls=5:allf=t+u,vignette=PI/4,setpts=PTS-STARTPTS{glitch_fx}"
                        cmd_scene = [
                            'ffmpeg', '-y', '-i', path_origen,
                            '-vf', vf_string, '-t', str(dur_exacta),
                            '-c:v', 'libx264', '-preset', 'ultrafast',
                            '-threads', '0', '-pix_fmt', 'yuv420p', '-r', str(fps), path_clip
                        ]
                    else:
                        vf_string = f"fade=t=in:st=0:d=0.1,noise=alls=5:allf=t+u,vignette=PI/4,setpts=PTS-STARTPTS{glitch_fx}"
                        cmd_scene = [
                            'ffmpeg', '-y', '-stream_loop', '-1', '-i', path_origen,
                            '-vf', vf_string, '-t', str(dur_exacta),
                            '-c:v', 'libx264', '-preset', 'ultrafast',
                            '-threads', '0', '-pix_fmt', 'yuv420p', '-r', str(fps), path_clip
                        ]

                    subprocess.run(cmd_scene, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    clips_temp.append(path_clip)
                    print(f"   [OK] Escena {i+1} ({'SD' if archivo.endswith('.png') else 'Pexels'}) — tipo:{tipo} efecto:{efecto}")

                filtro_sub = ""
                if not es_largo_video:
                    escenas_texto = tarea.get("escenas_texto", [])
                    ruta_srt = _generar_subtitulos_shorts(
                        ruta_audio, texto_locucion, escenas_texto, marca_audio, carpeta_reciente, duracion_audio
                    )
                    if ruta_srt and os.path.exists(ruta_srt):
                        sub_path = ruta_srt.replace('\\', '/').replace(':', '\\:')
                        filtro_sub = (
                            f"subtitles='{sub_path}':force_style='"
                            f"Alignment=10,FontSize=18,MarginV=0,Bold=1,"
                            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                            f"BackColour=&H80000000,BorderStyle=4,Outline=2,Shadow=1'"
                        )
                else:
                    print("📝 Video largo (16:9) — subtítulos desactivados.")

                print("🔗 FASE 1: Ensamblando cuerpo principal...")
                list_file = os.path.join(carpeta_reciente, "concat_list.txt")
                with open(list_file, "w") as f:
                    for clip in clips_temp:
                        safe = clip.replace('\\', '/')
                        f.write(f"file '{safe}'\n")

                ruta_base       = os.path.join(carpeta_reciente, "paso1_base.mp4")
                ruta_con_musica = os.path.join(carpeta_reciente, "paso2_musica.mp4")
                ruta_final      = os.path.join(carpeta_reciente, "00_FINAL_EXTREME_DYNAMICS.mp4")

                filtros_video = [
                    '-vf', f"setpts=PTS-STARTPTS,{filtro_sub}" if filtro_sub else "setpts=PTS-STARTPTS",
                    '-c:v', 'libx264', '-preset', 'veryfast', '-threads', '0', '-crf', '22',
                    '-force_key_frames', 'expr:gte(t,n_forced*4)', '-pix_fmt', 'yuv420p'
                ]

                cmd_merge = (
                    ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_file, '-i', ruta_audio.replace("\\", "/")]
                    + filtros_video
                    + ['-c:a', 'aac', '-shortest', ruta_base]
                )
                subprocess.run(cmd_merge, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                for clip in clips_temp:
                    try:
                        os.remove(clip)
                    except Exception:
                        pass
                try:
                    os.remove(list_file)
                except Exception:
                    pass

                print("🎵 FASE 2: Evaluando inyección de música de fondo...")
                ruta_actual = ruta_base
                if os.path.exists(ruta_musica_fondo):
                    print(f"   [OK] Mezclando pista de fondo (Volumen: {VOLUMEN_MUSICA}) de {marca_audio}")
                    cmd_mix = [
                        'ffmpeg', '-y', '-i', ruta_actual,
                        '-stream_loop', '-1', '-i', ruta_musica_fondo.replace("\\", "/"),
                        '-filter_complex', f"[1:a]volume={VOLUMEN_MUSICA}[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
                        '-map', '0:v', '-map', '[aout]',
                        '-c:v', 'copy', '-c:a', 'aac', ruta_con_musica
                    ]
                    subprocess.run(cmd_mix, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    ruta_actual = ruta_con_musica
                    try:
                        os.remove(ruta_base)
                    except Exception:
                        pass
                else:
                    print(f"   [INFO] No se encontró música para {marca_audio}. Saltando mezcla.")

                print("🎬 FASE 3: Evaluando inyección de Intro/Outro...")
                hay_intro = os.path.exists(ruta_intro_dinamico)
                hay_outro = os.path.exists(ruta_outro_dinamico)

                if hay_intro or hay_outro:
                    inputs         = []
                    filter_parts   = []
                    concat_elements = ""
                    idx = 0

                    if hay_intro:
                        print(f"   [OK] Detectado Intro: {os.path.basename(ruta_intro_dinamico)}")
                        inputs.extend(['-i', ruta_intro_dinamico.replace("\\", "/")])
                        filter_parts.append(f"[{idx}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{idx}];")
                        concat_elements += f"[v{idx}][{idx}:a]"
                        idx += 1

                    inputs.extend(['-i', ruta_actual.replace("\\", "/")])
                    filter_parts.append(f"[{idx}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{idx}];")
                    concat_elements += f"[v{idx}][{idx}:a]"
                    idx += 1

                    if hay_outro:
                        print(f"   [OK] Detectado Outro: {os.path.basename(ruta_outro_dinamico)}")
                        inputs.extend(['-i', ruta_outro_dinamico.replace("\\", "/")])
                        filter_parts.append(f"[{idx}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{idx}];")
                        concat_elements += f"[v{idx}][{idx}:a]"
                        idx += 1

                    filter_complex = "".join(filter_parts) + f"{concat_elements}concat=n={idx}:v=1:a=1[vout][aout]"
                    cmd_concat = (
                        ['ffmpeg', '-y'] + inputs + [
                            '-filter_complex', filter_complex,
                            '-map', '[vout]', '-map', '[aout]',
                            '-c:v', 'libx264', '-preset', 'fast', '-crf', '22', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '192k',
                            ruta_final
                        ]
                    )
                    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    try:
                        os.remove(ruta_actual)
                    except Exception:
                        pass
                else:
                    print("   [INFO] Sin Intro/Outro detectados. Finalizando arquitectura base.")
                    os.rename(ruta_actual, ruta_final)

                print(f"🏆 [OPERACIÓN EXITOSA V8.4.7] Video finalizado: {ruta_final}\n")

                print("📦 Generando paquete de publicación SEO...")
                paquete = {}
                try:
                    res_paquete = requests.post(
                        f"{RENDER_URL}/api/interna/generar_paquete",
                        json={
                            "clave_interna":  "admin1978_master_key",
                            "marca":          marca_audio,
                            "titulo":         tarea.get("titulo_sugerido", ""),
                            "texto_locucion": texto_locucion,   
                            "formato":        formato_ensamblaje
                        },
                        timeout=400
                    )
                    if res_paquete.status_code == 200:
                        paquete = res_paquete.json().get("paquete", {})
                        ruta_paquete = os.path.join(carpeta_reciente, "paquete_publicacion.json")
                        with open(ruta_paquete, "w", encoding="utf-8") as f:
                            json.dump(paquete, f, indent=4, ensure_ascii=False)
                        print(f"✅ [PAQUETE] Guardado en: {ruta_paquete}")
                        if "16:9" in formato_ensamblaje:
                            for opcion in ['A', 'B', 'C']:
                                prompt_min = paquete.get(f"prompt_miniatura_{opcion}", "")
                                if prompt_min:
                                    requests.post(
                                        f"{RENDER_URL}/api/nodo/encolar_tarea",
                                        json={
                                            "id":              str(uuid.uuid4()),
                                            "tipo":            "IMAGEN",
                                            "prompt":          prompt_min,
                                            "formato":         "16:9",
                                            "marca":           marca_audio,
                                            "carpeta_destino": carpeta_reciente,
                                            "nombre_archivo":  f"miniatura_{opcion}.png"
                                        },
                                        timeout=400
                                    )
                            print("🖼️ [PAQUETE] 3 miniaturas encoladas.")
                    else:
                        print(f"⚠️ [PAQUETE] Error del servidor: {res_paquete.status_code}")
                except Exception as e:
                    print(f"⚠️ [PAQUETE] Error: {e}")

                try:
                    if paquete:
                        _generar_word_paquete(paquete, marca_audio, formato_ensamblaje, carpeta_reciente)
                        print("✅ [WORD] paquete_publicacion.docx generado.")
                except Exception as e:
                    print(f"⚠️ [WORD] Error paquete: {e}")

                try:
                    _generar_word_guion(texto_locucion, marca_audio, formato_ensamblaje, tarea, carpeta_reciente)
                except Exception as e:
                    print(f"⚠️ [WORD] Error guión: {e}")

            # ══════════════════════════════════════════════════
            # RUTA 2: GENERACIÓN DE IMÁGENES/VIDEOS (SD + PEXELS)
            # ══════════════════════════════════════════════════
            else:
                raw_prompt = tarea["prompt"]
                print(f"\n🚀 [ORDEN VISUAL] ID: {tarea_id}")
                try:
                    escenas = json.loads(raw_prompt)
                except Exception:
                    escenas = [{"id": 1, "prompt": raw_prompt}]

                marca_tarea     = tarea.get("marca", "La Viuda")
                formato_tarea   = tarea.get("formato", "9:16")
                carpeta_destino = tarea.get("carpeta_destino", None)
                nombre_archivo  = tarea.get("nombre_archivo", None)
                pexels_api_key  = (
                    PEXELS_API_KEY_LOCAL
                    if PEXELS_API_KEY_LOCAL and PEXELS_API_KEY_LOCAL != "PEGA_TU_LLAVE_REAL_AQUI"
                    else tarea.get("pexels_api_key", "")
                )

                try:
                    import sys
                    sys.path.insert(0, "C:\\NODO_PINPINELA")
                    from pexels_engine import buscar_clip_pexels, usar_pexels
                    pexels_disponible = True
                except Exception as e:
                    print(f"   [PEXELS] Motor no disponible: {e}")
                    pexels_disponible = False

                if carpeta_destino and nombre_archivo:
                    w, h     = (1920, 1080)
                    carpeta_p = carpeta_destino
                else:
                    w, h     = (1024, 576) if "16:9" in formato_tarea else (576, 1024)
                    carpeta_p = os.path.join(CARPETA_LOCAL, tarea_id)
                    os.makedirs(carpeta_p, exist_ok=True)
                    with open(os.path.join(carpeta_p, "formato.txt"), "w") as f:
                        f.write(formato_tarea)

                ip_render = IP_GRAFICA_1
                if "16:9" in formato_tarea:
                    print(f"🎬 16:9 LARGO → 3060 [{IP_GRAFICA_1}]")
                else:
                    print(f"📱 9:16 SHORT → 3060 [{IP_GRAFICA_1}]")

                img_prev = ""

                for i, esc in enumerate(escenas):
                    p = esc.get("prompt", "")
                    if not p:
                        continue
                    nodo_num     = 1 if ip_render == IP_GRAFICA_1 else 2
                    prompt_esc   = esc.get("prompt_visual", p)
                    pexels_query = esc.get("pexels_query", None)
                    es_miniatura = bool(carpeta_destino and nombre_archivo)

                    if es_miniatura:
                        path_out_png = os.path.join(carpeta_p, nombre_archivo)
                        path_out_mp4 = path_out_png.replace(".png", ".mp4")
                    else:
                        path_out_png = os.path.join(carpeta_p, f"escena_{i+1:02d}.png")
                        path_out_mp4 = os.path.join(carpeta_p, f"escena_{i+1:02d}.mp4")

                    print(f"⚙️ NODO {nodo_num}: Escena {i+1}/{len(escenas)}...")

                    uso_pexels = (
                        pexels_disponible and pexels_api_key
                        and not es_miniatura and usar_pexels(marca_tarea)
                    )

                    if uso_pexels:
                        ok_pexels = buscar_clip_pexels(
                            prompt_visual=prompt_esc, marca=marca_tarea,
                            formato=formato_tarea, api_key=pexels_api_key,
                            carpeta_destino=carpeta_p,
                            nombre_archivo=os.path.basename(path_out_mp4),
                            pexels_query=pexels_query
                        )
                        if ok_pexels:
                            print(f"   [OK] Escena {i+1} — Pexels ✅")
                            continue
                        print(f"   [FALLBACK] Escena {i+1} → SD")

                    if es_miniatura:
                        prompt_limpio = (
                            f"{prompt_esc}, photorealistic, extreme detail, single focal element, "
                            f"dramatic lighting, high contrast, sharp focus, professional photography, "
                            f"no people, no humans, no text"
                        )
                        payload = {
                            "prompt": prompt_limpio,
                            "negative_prompt": (
                                "person, people, human, face, body, blurry, dark, underexposed, "
                                "low contrast, generic, boring, text, watermark, logo, multiple objects, "
                                "busy composition, dull, flat lighting, overexposed, washed out, "
                                "cartoon, anime, illustration, 3d render, cgi"
                            ),
                            "steps": 40, "cfg_scale": 10,
                            "width": w, "height": h,
                            "sampler_name": "DPM++ 2M Karras",
                            "batch_size": 1, "n_iter": 1
                        }
                    else:
                        marca_limpia = marca_tarea.lower()
                        
                        if marca_limpia in ["la esquina random", "laesquinarandom"]:
                            prompt_limpio = f"{prompt_esc}, funny cartoon style, 2D animation, vibrant flat colors, comic book aesthetic, expressive caricature, exaggerated facial expressions, humorous situation, vibrant lighting, cel shaded"
                            neg_prompt = "photorealistic, realistic, 3d render, hyperrealistic, photography, raw photo, dark, gloomy, horror, serious, monochrome, anime, manga, text, watermark, deformed, bad anatomy, blurry"
                        
                        elif marca_limpia in ["la viuda", "laviuda"]:
                            # MATRIZ VISUAL TERROR PSICOLÓGICO ESTRICTO (V8.4.7 - ERRADICACIÓN SCI-FI)
                            prompt_limpio = (
                                f"{prompt_esc}, terrifying psychological horror, creepy pareidolia, paranormal shadowy apparition, ghostly dark figure, supernatural shadow, "
                                f"extreme low key lighting, chiaroscuro, deep saturated red and pitch black shadows, "
                                f"high contrast, rough decaying textures, heavy vintage analog film grain, macabre atmosphere, "
                                f"no realistic humans, no blood"
                            )
                            neg_prompt = (
                                "normal living person, clear human face, detailed human body, realistic human, "
                                "alien, extraterrestrial, grey alien, UFO, martian, sci-fi, science fiction, mutant, creature, monster, tentacles, "
                                "blood, gore, red liquid, violent, text, watermark, blurry, low quality, "
                                "anime, cartoon, 3d render, cgi, clean, modern architecture, office, hospital, "
                                "subway, safe, bright, mundane, well lit, symmetrical, empty liminal space"
                            )

                        elif marca_limpia in ["monkygraff"]:
                            # MATRIZ VISUAL FOTOPERIODISMO GEOPOLÍTICO
                            prompt_limpio = (
                                f"{prompt_esc}, RAW photo, photojournalism, real photography, "
                                f"shot on location, harsh natural lighting, gritty texture, "
                                f"physical environment, no people, no faces, no cgi, no digital art"
                            )
                            neg_prompt = (
                                "person, people, human, face, body, horror, dark, terror, ghost, shadow figure, "
                                "neon, glowing, hologram, digital, abstract, wireframe, sci-fi, futuristic, "
                                "3d render, cartoon, anime, text, watermark, blurry, low quality, "
                                "psychological horror, paranormal, supernatural, creepy"
                            )

                        else:
                            prompt_limpio = (
                                f"{prompt_esc}, RAW photo, photorealistic, real photography, "
                                f"no people, no humans, no persons, natural lighting, film grain, "
                                f"gritty texture, shot on location, physical environment, "
                                f"no cgi, no digital art, no abstract"
                            )
                            neg_prompt = (
                                "person, people, human, man, woman, boy, girl, face, body, character, "
                                "figure, portrait, selfie, eye, eyes, closeup face, macro face, skin pores, "
                                "eyelash, eyebrow, iris, pupil, canon, nikon, sony, logo, brand, watermark, "
                                "text, collage, split screen, multiple panels, deformed, blurry, low quality, "
                                "nude, naked, nsfw, explicit, anime, cartoon, illustration, 3d render, "
                                "videogame, cgi, digital art, concept art, abstract, glowing lines, neon, "
                                "hologram, sci-fi, futuristic, cyber, wireframe, network visualization, "
                                "data visualization, particle effects, blue glow, tron, virtual, simulation, "
                                "render, unreal engine, octane, vray, digital painting, fantasy, surreal, vfx"
                            )

                        payload = {
                            "prompt": prompt_limpio,
                            "negative_prompt": neg_prompt,
                            "steps": 25, "cfg_scale": 7,
                            "width": w, "height": h,
                            "sampler_name": "DPM++ 2M Karras",
                            "batch_size": 1, "n_iter": 1
                        }

                    sd_ok = False
                    for intento_sd in range(3):
                        try:
                            print(f"   [SD] Intento {intento_sd+1}/3 escena {i+1}...")
                            res_sd = requests.post(
                                f"http://{ip_render}:7861/sdapi/v1/txt2img",
                                json=payload, timeout=300
                            )
                            if res_sd.status_code == 200:
                                b64 = res_sd.json()['images'][0]
                                if not img_prev:
                                    img_prev = b64
                                with open(path_out_png, "wb") as f:
                                    f.write(base64.b64decode(b64))
                                print(f"   [OK] Nodo {nodo_num} — Escena {i+1} SD ✅")
                                sd_ok = True
                                break
                            else:
                                print(f"   ⚠️ SD respondió {res_sd.status_code} — reintentando...")
                                time.sleep(5)
                        except Exception as e:
                            print(f"   ⚠️ SD error intento {intento_sd+1}: {e}")
                            time.sleep(5)
                    if not sd_ok:
                        print(f"   ❌ Escena {i+1} falló en SD después de 3 intentos.")

                try:
                    payload_upload = {"tarea_id": tarea_id}
                    if img_prev:
                        payload_upload["image_b64"] = f"data:image/png;base64,{img_prev}"
                    requests.post(
                        f"{RENDER_URL}/api/nodo/upload_result",
                        json=payload_upload, timeout=400
                    )
                    print(f"✅ [LOTE COMPLETADO] Nodo local sincronizado.\n")
                except Exception as e:
                    print(f"⚠️ Error al sincronizar cierre de lote: {e}")

    except Exception as e:
        print(f"⚠️ Error en ciclo de ejecución: {e}")


print("⚡ NODO XEON ONLINE - CORPORATE TECH V8.4.7 (ERRADICACIÓN ALIENÍGENA - LA VIUDA)")
while True:
    procesar()
    time.sleep(2)