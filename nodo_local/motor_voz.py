import os
import subprocess
import uuid
import soundfile as sf
import gc
import torch
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

# ─── RUTAS APPLIO ────────────────────────────────────────────────────────────
APPLIO        = r"C:\Applio"
PYTHON_APPLIO = r"C:\Applio\env\python.exe"
SCRIPT_APPLIO = os.path.join(APPLIO, "core.py")
CARPETA_TMP   = r"C:\NODO_PINPINELA\audio_tmp"
os.makedirs(CARPETA_TMP, exist_ok=True)

# ─── KOKORO TTS ──────────────────────────────────────────────────────────────
VOCES_KOKORO = {
    "La Viuda":         {"lang": "e",  "voice": "em_alex",  "speed": 0.65},
    "Monkygraff":       {"lang": "e",  "voice": "em_alex",  "speed": 0.90},
    "FiltradoMX":       {"lang": "es", "voice": "ef_dora",  "speed": 0.90},
    "LaesquinaRandom":  {"lang": "es", "voice": "em_alex",  "speed": 1.05},
}

# ─── MODELOS RVC ──────────────────────────────────────────────────────────────
def _buscar_pth(carpeta, pth_forzado=None):
    if pth_forzado and os.path.exists(pth_forzado):
        return pth_forzado
    if not os.path.exists(carpeta):
        return None
    candidatos = [f for f in os.listdir(carpeta)
                  if f.endswith(".pth")
                  and not f.startswith("D_")
                  and not f.startswith("G_")]
    if candidatos:
        def _extraer_epochs(nombre):
            try:
                partes = nombre.replace(".pth","").split("_")
                for p in reversed(partes):
                    if p.endswith("e") and p[:-1].isdigit():
                        return int(p[:-1])
            except: pass
            return 0
        candidatos.sort(key=_extraer_epochs, reverse=True)
        return os.path.join(carpeta, candidatos[0])
    return None

def _buscar_index(carpeta):
    if not os.path.exists(carpeta):
        return None
    for f in os.listdir(carpeta):
        if f.endswith(".index"):
            return os.path.join(carpeta, f)
    return None

def _construir_modelos_rvc():
    base = r"C:\Applio\logs"
    canales = {
        "La Viuda": {
            "carpeta":        os.path.join(base, "LaViuda"),
            "pitch":          "-10",
            "index_rate":     "0.50",
            "protect":        "0.1",
            "clean_strength": "0.7",
        },
        "Monkygraff": {
            "carpeta":        os.path.join(base, "MonkyGraff"),
            "pitch":          "-1",
            "index_rate":     "0.70",
            "protect":        "0.1",
            "clean_strength": "0.40",
        },
        "FiltradoMX": {
            "carpeta":        os.path.join(base, "FiltradoMX_v3"),
            "pth_forzado":    r"C:\Applio\logs\FiltradoMX_v3\FiltradoMX_v3_200e_51400s.pth",
            "index":          r"C:\Applio\logs\FiltradoMX_v3\FiltradoMX_v3.index",
            "pitch":          "0",
            "index_rate":     "0.75",
            "protect":        "0.33",
            "clean_strength": "0.30",
        },
        "LaesquinaRandom": {
            "carpeta":        os.path.join(base, "LaEsquinaRandom"),
            "pitch":          "1",
            "index_rate":     "0.60",
            "protect":        "0.40",
            "clean_strength": "0.40",
        },
    }
    modelos = {}
    for canal, cfg in canales.items():
        pth   = _buscar_pth(cfg["carpeta"], cfg.get("pth_forzado"))
        index = cfg.get("index") if cfg.get("index") else _buscar_index(cfg["carpeta"])
        
        if pth:
            modelos[canal] = {
                "pth":            pth,
                "index":          index or "",
                "pitch":          cfg["pitch"],
                "index_rate":     cfg["index_rate"] if index else "0.0",
                "protect":        cfg["protect"],
                "clean_strength": cfg["clean_strength"],
            }
            estado_index = f"index: {os.path.basename(index)}" if index else "sin index"
            print(f"[RVC] {canal} — {os.path.basename(pth)} | {estado_index}")
        else:
            print(f"[RVC] {canal} — sin modelo .pth (usará Kokoro directo)")
    return modelos

MODELOS_RVC = _construir_modelos_rvc()

def forzar_limpieza_vram():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    print("[HARDWARE] VRAM purgada correctamente.")

# ─── EDGE TTS ──────────────────────────────────────────────────────────────
VOCES_EDGE = {
    "FiltradoMX":      "es-MX-DaliaNeural",
    "LaesquinaRandom": "es-MX-JorgeNeural",
}

def generar_edge_tts(texto, voz, ruta_salida_wav):
    import asyncio, subprocess as sp
    ruta_mp3_tmp = ruta_salida_wav.replace(".wav", "_edge.mp3")
    async def _run():
        import edge_tts
        comunicar = edge_tts.Communicate(texto, voz, rate="-5%", volume="+0%")
        await comunicar.save(ruta_mp3_tmp)
    asyncio.run(_run())
    if not os.path.exists(ruta_mp3_tmp): return False
    subprocess.run(["ffmpeg", "-y", "-i", ruta_mp3_tmp, "-ar", "44100", "-ac", "1", ruta_salida_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try: os.remove(ruta_mp3_tmp)
    except: pass
    return os.path.exists(ruta_salida_wav)

# ─── KOKORO TTS ──────────────────────────────────────────────────────────────
def generar_kokoro_tts(texto, config_voz, ruta_salida_wav):
    from kokoro import KPipeline
    import numpy as np
    try:
        pipeline = KPipeline(lang_code=config_voz["lang"])
        generator = pipeline(texto, voice=config_voz["voice"], speed=config_voz["speed"], split_pattern=r'\n+')
        audio_chunks = [audio for _, _, audio in generator]
        if not audio_chunks: raise RuntimeError("Kokoro no generó audio")
        audio_completo = np.concatenate(audio_chunks)
        sf.write(ruta_salida_wav, audio_completo, 24000)
        print(f"[KOKORO] Audio generado: {ruta_salida_wav}")
    finally:
        forzar_limpieza_vram()

# ─── RVC ──────────────────────────────────────────────────────────────
def aplicar_rvc(ruta_entrada, ruta_salida, modelo):
    cmd = [
        PYTHON_APPLIO, SCRIPT_APPLIO, "infer",
        f"--pitch={modelo['pitch']}",
        "--index_rate",      modelo["index_rate"],
        "--volume_envelope", "1",
        "--protect",         modelo["protect"],
        "--f0_method",       "rmvpe",
        "--input_path",      ruta_entrada,
        "--output_path",     ruta_salida,
        "--pth_path",        modelo["pth"],
        "--export_format",   "MP3",
        "--embedder_model",  "contentvec",
        "--clean_audio",     "True",
        "--clean_strength",  modelo["clean_strength"],
        "--split_audio",     "False",
    ]
    index_path = modelo.get("index") or ""
    if float(modelo.get("index_rate", "0")) == 0.0: index_path = ""
    cmd += ["--index_path", index_path]
    result = subprocess.run(cmd, cwd=APPLIO)
    forzar_limpieza_vram()
    return result.returncode == 0

def normalizar_audio(ruta_entrada, ruta_salida):
    subprocess.run(["ffmpeg", "-y", "-i", ruta_entrada, "-ar", "44100", "-ac", "1", "-b:a", "128k", ruta_salida], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.exists(ruta_salida)

# ─── ENDPOINTS ──────────────────────────────────────────────────────────────
@app.route('/generar_audio', methods=['POST'])
def generar_audio():
    data   = request.json
    texto  = data.get("texto", "")
    marca  = data.get("marca", "La Viuda")
    job_id = data.get("job_id", str(uuid.uuid4())[:8])

    if not texto: return jsonify({"error": "No enviaste texto"}), 400

    config_voz = VOCES_KOKORO.get(marca, VOCES_KOKORO["La Viuda"])
    modelo_rvc = MODELOS_RVC.get(marca)

    voz_edge = VOCES_EDGE.get(marca)
    if voz_edge:
        ruta_edge_wav = os.path.join(CARPETA_TMP, f"{job_id}_edge.wav")
        ruta_rvc_mp3  = os.path.join(CARPETA_TMP, f"{job_id}_rvc.mp3")
        ruta_norm     = os.path.join(CARPETA_TMP, f"{job_id}_final.mp3")
        if generar_edge_tts(texto, voz_edge, ruta_edge_wav) and modelo_rvc:
            if aplicar_rvc(ruta_edge_wav, ruta_rvc_mp3, modelo_rvc):
                normalizar_audio(ruta_rvc_mp3, ruta_norm)
                if os.path.exists(ruta_norm): os.replace(ruta_norm, ruta_rvc_mp3)
                return send_file(ruta_rvc_mp3, mimetype="audio/mpeg")

    ruta_kokoro = os.path.join(CARPETA_TMP, f"{job_id}_kokoro.wav")
    ruta_rvc    = os.path.join(CARPETA_TMP, f"{job_id}_rvc.mp3")
    ruta_norm   = os.path.join(CARPETA_TMP, f"{job_id}_final.mp3")
    
    generar_kokoro_tts(texto, config_voz, ruta_kokoro)
    ok = aplicar_rvc(ruta_kokoro, ruta_rvc, modelo_rvc) if modelo_rvc else False
    try: os.remove(ruta_kokoro)
    except: pass
    
    if ok and os.path.exists(ruta_rvc):
        normalizar_audio(ruta_rvc, ruta_norm)
        if os.path.exists(ruta_norm): os.replace(ruta_norm, ruta_rvc)
        return send_file(ruta_rvc, mimetype="audio/mpeg")
    return jsonify({"error": "Fallo de voz"}), 500

@app.route('/generar_chunk', methods=['POST'])
def generar_chunk():
    data      = request.json
    texto     = data.get("texto", "")
    marca     = data.get("marca", "La Viuda")
    job_id    = data.get("job_id", str(uuid.uuid4())[:8])
    chunk_idx = data.get("chunk_idx", 0)

    if not texto: return jsonify({"error": "Chunk vacío"}), 400
    config_voz = VOCES_KOKORO.get(marca, VOCES_KOKORO["La Viuda"])
    modelo_rvc = MODELOS_RVC.get(marca)
    tag = f"{job_id}_c{chunk_idx:02d}"
    ruta_kokoro = os.path.join(CARPETA_TMP, f"{tag}_kokoro.wav")
    ruta_rvc    = os.path.join(CARPETA_TMP, f"{tag}_rvc.mp3")
    ruta_norm   = os.path.join(CARPETA_TMP, f"{tag}_final.mp3")

    voz_edge = VOCES_EDGE.get(marca)
    if voz_edge:
        ruta_edge_wav = os.path.join(CARPETA_TMP, f"{tag}_edge.wav")
        if generar_edge_tts(texto, voz_edge, ruta_edge_wav) and modelo_rvc:
            if aplicar_rvc(ruta_edge_wav, ruta_rvc, modelo_rvc):
                normalizar_audio(ruta_rvc, ruta_norm)
                if os.path.exists(ruta_norm): os.replace(ruta_norm, ruta_rvc)
                return send_file(ruta_rvc, mimetype="audio/mpeg")

    generar_kokoro_tts(texto, config_voz, ruta_kokoro)
    ok = aplicar_rvc(ruta_kokoro, ruta_rvc, modelo_rvc) if modelo_rvc else False
    try: os.remove(ruta_kokoro)
    except: pass
    
    if ok and os.path.exists(ruta_rvc):
        normalizar_audio(ruta_rvc, ruta_norm)
        if os.path.exists(ruta_norm): os.replace(ruta_norm, ruta_rvc)
        return send_file(ruta_rvc, mimetype="audio/mpeg")
    return jsonify({"error": "Fallo de RVC"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)