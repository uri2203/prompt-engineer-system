import os
import subprocess
import uuid
import soundfile as sf
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

# ─── RUTAS APPLIO ────────────────────────────────────────────────────────────
APPLIO        = r"C:\Applio"
PYTHON_APPLIO = r"C:\Applio\env\python.exe"
SCRIPT_APPLIO = os.path.join(APPLIO, "core.py")
CARPETA_TMP   = r"C:\NODO_PINPINELA\audio_tmp"
os.makedirs(CARPETA_TMP, exist_ok=True)

# ─── KOKORO TTS ───────────────────────────────────────────────────────────────
VOCES_KOKORO = {
    "La Viuda":         {"lang": "e", "voice": "em_alex", "speed": 0.65},
    "Monkygraff":       {"lang": "e", "voice": "em_alex", "speed": 0.90},
    "FiltradoMX":       {"lang": "e", "voice": "ef_dora", "speed": 0.85},
    "LaesquinaRandom":  {"lang": "e", "voice": "em_alex", "speed": 1.05},
}

# ─── MODELOS RVC ──────────────────────────────────────────────────────────────
MODELOS_RVC = {
    "La Viuda": {
        "pth":            r"C:\Applio\logs\LaViuda\LaViuda_150e_1800s.pth",
        "index":          r"C:\Applio\logs\LaViuda\LaViuda.index",
        "pitch":          "-10",
        "index_rate":     "0.50",
        "protect":        "0.1",
        "clean_strength": "0.7",
    },
    "Monkygraff": {
        "pth":            r"C:\Applio\logs\MonkyGraff\MonkyGraff_150e_4950s.pth",
        "index":          r"C:\Applio\logs\MonkyGraff\MonkyGraff.index",
        "pitch":          "-1",
        "index_rate":     "0.70",
        "protect":        "0.1",
        "clean_strength": "0.40",
    },
    # Canales pendientes — descomentar cuando tengas el .pth entrenado:
    # "FiltradoMX": {
    #     "pth":            r"C:\Applio\logs\FiltradoMX\FiltradoMX_XXXe_XXXXs.pth",
    #     "index":          r"C:\Applio\logs\FiltradoMX\FiltradoMX.index",
    #     "pitch":          "2",
    #     "index_rate":     "0.60",
    #     "protect":        "0.1",
    #     "clean_strength": "0.5",
    # },
    # "LaesquinaRandom": {
    #     "pth":            r"C:\Applio\logs\LaesquinaRandom\LaesquinaRandom_XXXe_XXXXs.pth",
    #     "index":          r"C:\Applio\logs\LaesquinaRandom\LaesquinaRandom.index",
    #     "pitch":          "-1",
    #     "index_rate":     "0.65",
    #     "protect":        "0.1",
    #     "clean_strength": "0.45",
    # },
}


# ══════════════════════════════════════════════════════════════════════════════
# KOKORO TTS
# ══════════════════════════════════════════════════════════════════════════════

def generar_kokoro_tts(texto, config_voz, ruta_salida_wav):
    from kokoro import KPipeline
    import numpy as np

    pipeline  = KPipeline(lang_code=config_voz["lang"])
    generator = pipeline(
        texto,
        voice=config_voz["voice"],
        speed=config_voz["speed"],
        split_pattern=r'\n+'
    )

    audio_chunks = []
    for _, _, audio in generator:
        audio_chunks.append(audio)

    if not audio_chunks:
        raise RuntimeError("Kokoro no genero audio")

    sf.write(ruta_salida_wav, __import__('numpy').concatenate(audio_chunks), 24000)
    print(f"[KOKORO] Audio generado: {ruta_salida_wav}")


# ══════════════════════════════════════════════════════════════════════════════
# RVC
# ══════════════════════════════════════════════════════════════════════════════

def aplicar_rvc(ruta_entrada, ruta_salida, modelo):
    """
    f0_method=crepe: rmvpe se congela en 'Converting audio' en este setup Windows.
    split_audio=False: FIX DEL DOBLE TRABAJO. Con True Applio hacia 2 pasadas
    completas (partir + procesar + unir). Con False es una sola pasada directa.
    """
    cmd = [
        PYTHON_APPLIO, SCRIPT_APPLIO, "infer",
        f"--pitch={modelo['pitch']}",
        "--index_rate",      modelo["index_rate"],
        "--volume_envelope", "1",
        "--protect",         modelo["protect"],
        "--f0_method",       "crepe",
        "--input_path",      ruta_entrada,
        "--output_path",     ruta_salida,
        "--pth_path",        modelo["pth"],
        "--index_path",      modelo["index"],
        "--export_format",   "MP3",
        "--embedder_model",  "contentvec",
        "--clean_audio",     "True",
        "--clean_strength",  modelo["clean_strength"],
        "--split_audio",     "False",
    ]
    print("[RVC] crepe + split_audio False (una sola pasada)...")
    result = subprocess.run(cmd, cwd=APPLIO)
    if result.returncode != 0:
        print(f"[RVC] Applio codigo: {result.returncode}")
    return result.returncode == 0


def normalizar_audio(ruta_entrada, ruta_salida):
    subprocess.run([
        "ffmpeg", "-y", "-i", ruta_entrada,
        "-ar", "44100", "-ac", "1", "-b:a", "128k", ruta_salida
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.exists(ruta_salida)


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT /generar_audio — shorts y videos cortos
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/generar_audio', methods=['POST'])
def generar_audio():
    data   = request.json
    texto  = data.get("texto", "")
    marca  = data.get("marca", "La Viuda")
    job_id = data.get("job_id", str(uuid.uuid4())[:8])

    if not texto:
        return jsonify({"error": "No enviaste texto"}), 400

    config_voz = VOCES_KOKORO.get(marca, VOCES_KOKORO["La Viuda"])
    modelo_rvc = MODELOS_RVC.get(marca)

    ruta_kokoro = os.path.join(CARPETA_TMP, f"{job_id}_kokoro.wav")
    ruta_rvc    = os.path.join(CARPETA_TMP, f"{job_id}_rvc.mp3")
    ruta_norm   = os.path.join(CARPETA_TMP, f"{job_id}_final.mp3")

    print(f"\n{'='*44}")
    print(f"[MOTOR VOZ] 1/2 Kokoro TTS ({marca}) | job: {job_id}")
    generar_kokoro_tts(texto, config_voz, ruta_kokoro)

    if not modelo_rvc:
        print(f"[MOTOR VOZ] Sin RVC para '{marca}'. Kokoro directo.")
        print(f"{'='*44}\n")
        return send_file(ruta_kokoro, mimetype="audio/wav")

    if not os.path.exists(modelo_rvc["pth"]):
        return jsonify({"error": f"Falta PTH: {modelo_rvc['pth']}"}), 500

    print(f"[MOTOR VOZ] 2/2 RVC {marca}...")
    ok = aplicar_rvc(ruta_kokoro, ruta_rvc, modelo_rvc)
    try: os.remove(ruta_kokoro)
    except: pass

    if ok and os.path.exists(ruta_rvc):
        normalizar_audio(ruta_rvc, ruta_norm)
        if os.path.exists(ruta_norm):
            os.replace(ruta_norm, ruta_rvc)
        print(f"[MOTOR VOZ] EXITO.")
        print(f"{'='*44}\n")
        return send_file(ruta_rvc, mimetype="audio/mpeg")
    else:
        print("[MOTOR VOZ] RVC fallo.")
        return jsonify({"error": "RVC fallo"}), 500


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINT /generar_chunk — videos largos, un bloque a la vez
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/generar_chunk', methods=['POST'])
def generar_chunk():
    data      = request.json
    texto     = data.get("texto", "")
    marca     = data.get("marca", "La Viuda")
    job_id    = data.get("job_id", str(uuid.uuid4())[:8])
    chunk_idx = data.get("chunk_idx", 0)

    if not texto:
        return jsonify({"error": "Chunk vacio"}), 400

    config_voz  = VOCES_KOKORO.get(marca, VOCES_KOKORO["La Viuda"])
    modelo_rvc  = MODELOS_RVC.get(marca)
    tag         = f"{job_id}_c{chunk_idx:02d}"
    ruta_kokoro = os.path.join(CARPETA_TMP, f"{tag}_kokoro.wav")
    ruta_rvc    = os.path.join(CARPETA_TMP, f"{tag}_rvc.mp3")
    ruta_norm   = os.path.join(CARPETA_TMP, f"{tag}_final.mp3")

    print(f"[CHUNK {chunk_idx}] Kokoro ({marca})...")
    generar_kokoro_tts(texto, config_voz, ruta_kokoro)

    if not modelo_rvc or not os.path.exists(modelo_rvc["pth"]):
        print(f"[CHUNK {chunk_idx}] Sin RVC — Kokoro directo.")
        return send_file(ruta_kokoro, mimetype="audio/wav")

    print(f"[CHUNK {chunk_idx}] RVC {marca}...")
    ok = aplicar_rvc(ruta_kokoro, ruta_rvc, modelo_rvc)
    try: os.remove(ruta_kokoro)
    except: pass

    if ok and os.path.exists(ruta_rvc):
        normalizar_audio(ruta_rvc, ruta_norm)
        if os.path.exists(ruta_norm):
            os.replace(ruta_norm, ruta_rvc)
        print(f"[CHUNK {chunk_idx}] EXITO.")
        return send_file(ruta_rvc, mimetype="audio/mpeg")
    else:
        print(f"[CHUNK {chunk_idx}] RVC fallo.")
        return jsonify({"error": f"RVC fallo chunk {chunk_idx}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
