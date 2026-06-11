import requests
import uuid
import os
import subprocess

IP_MOTOR_VOZ = "192.168.0.251"
PUERTO_VOZ   = 8000

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE CHUNKS (ESTRICTA V8.5.2 - FIX METADATOS VBR)
# ══════════════════════════════════════════════════════════════
PALABRAS_POR_CHUNK = 120

# F5-TTS necesita chunks más largos para sonar natural
PALABRAS_POR_CHUNK_F5 = 60

CANALES_F5 = {"FiltradoMX"}

def _partir_texto_en_chunks(texto, palabras_por_chunk):
    import re

    # Dividir en oraciones completas respetando puntuación
    oraciones = re.split(r'(?<=[.!?…])\s+', texto.strip())
    oraciones = [o.strip() for o in oraciones if o.strip()]

    chunks    = []
    chunk_actual = []
    palabras_actuales = 0

    for oracion in oraciones:
        palabras_oracion = len(oracion.split())

        if palabras_actuales + palabras_oracion > palabras_por_chunk and chunk_actual:
            chunks.append(" ".join(chunk_actual))
            chunk_actual = [oracion]
            palabras_actuales = palabras_oracion
        else:
            chunk_actual.append(oracion)
            palabras_actuales += palabras_oracion

    if chunk_actual:
        chunks.append(" ".join(chunk_actual))

    return chunks


def _unir_chunks_ffmpeg(rutas_chunks, ruta_final):
    carpeta_temp = os.path.dirname(ruta_final)
    ruta_lista   = os.path.join(carpeta_temp, "chunks_list.txt")

    with open(ruta_lista, "w", encoding="utf-8") as f:
        for ruta in rutas_chunks:
            safe = ruta.replace("\\", "/")
            f.write(f"file '{safe}'\n")

    # ⚠️ CIRUGÍA CORPORATE TECH: RE-CODIFICACIÓN OBLIGATORIA
    # En lugar de "-c copy", forzamos "-c:a libmp3lame".
    # Esto reconstruye el índice de tiempo del MP3 desde cero, garantizando 
    # que ffprobe lea la duración exacta en el worker_cpu.py.
    resultado = subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", ruta_lista,
        "-c:a", "libmp3lame", "-b:a", "192k", 
        ruta_final
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        os.remove(ruta_lista)
    except Exception:
        pass

    return resultado.returncode == 0


def generar_audio_local(texto, marca, ruta_salida):
    job_id       = str(uuid.uuid4())[:8]
    num_palabras = len(texto.split())
    base_url     = f"http://{IP_MOTOR_VOZ}:{PUERTO_VOZ}"

    print(f"[VOICE LOCAL] Canal: {marca} | Palabras Totales: {num_palabras} | Job: {job_id}")
    print(f"[VOICE LOCAL] Modo CHUNKS (Reconstrucción de Metadatos Activa)")
    
    # F5-TTS funciona mejor con chunks más largos
    ppchunk = PALABRAS_POR_CHUNK_F5 if marca in CANALES_F5 else PALABRAS_POR_CHUNK
    chunks = _partir_texto_en_chunks(texto, ppchunk)
    print(f"[VOICE LOCAL] Texto partido en {len(chunks)} chunks de máximo {ppchunk} palabras.")

    carpeta_temp  = os.path.dirname(ruta_salida)
    rutas_chunks  = []

    for idx, chunk in enumerate(chunks):
        print(f"[VOICE LOCAL] Procesando chunk {idx+1}/{len(chunks)} ({len(chunk.split())} palabras)...")

        ruta_chunk = os.path.join(carpeta_temp, f"chunk_{job_id}_{idx:02d}.mp3")
        exito      = False

        MAX_INTENTOS  = 4
        ESPERAS       = [5, 15, 30, 60]  # espera progresiva entre intentos (segundos)

        for intento in range(MAX_INTENTOS):
            try:
                res = requests.post(
                    f"{base_url}/generar_chunk",
                    json={
                        "texto":     chunk,
                        "marca":     marca,
                        "job_id":    job_id,
                        "chunk_idx": idx
                    },
                    timeout=1800
                )
                if res.status_code == 200:
                    with open(ruta_chunk, "wb") as f:
                        f.write(res.content)
                    tam = os.path.getsize(ruta_chunk)
                    if tam < 1000:
                        print(f"[VOICE LOCAL] Chunk {idx+1} intento {intento+1} — archivo sospechoso ({tam} bytes), reintentando...")
                        os.remove(ruta_chunk)
                        espera = ESPERAS[min(intento, len(ESPERAS)-1)]
                        print(f"[VOICE LOCAL] Esperando {espera}s antes de reintentar...")
                        import time; time.sleep(espera)
                        continue
                    print(f"[VOICE LOCAL] Chunk {idx+1} OK — {tam} bytes")
                    rutas_chunks.append(ruta_chunk)
                    exito = True
                    break
                else:
                    espera = ESPERAS[min(intento, len(ESPERAS)-1)]
                    print(f"[VOICE LOCAL] Chunk {idx+1} intento {intento+1}/{MAX_INTENTOS} — HTTP {res.status_code} — esperando {espera}s...")
                    import time; time.sleep(espera)
            except Exception as e:
                espera = ESPERAS[min(intento, len(ESPERAS)-1)]
                print(f"[VOICE LOCAL] Chunk {idx+1} intento {intento+1}/{MAX_INTENTOS} — Error: {e} — esperando {espera}s...")
                import time; time.sleep(espera)

        # DOCTRINA DE FALLO CATASTRÓFICO
        if not exito:
            print(f"[VOICE LOCAL] ❌ FATAL: Chunk {idx+1} falló tras {MAX_INTENTOS} intentos.")
            print(f"[VOICE LOCAL] ❌ Abortando ensamblaje para evitar falso positivo. Destruyendo temporales...")
            for ruta_chunk_borrar in rutas_chunks:
                try:
                    os.remove(ruta_chunk_borrar)
                except Exception:
                    pass
            return None

    ruta_mp3 = ruta_salida if ruta_salida.endswith(".mp3") else ruta_salida.replace(".wav", ".mp3")
    print(f"[VOICE LOCAL] Uniendo y recodificando {len(rutas_chunks)} chunks con FFmpeg...")
    ok_union = _unir_chunks_ffmpeg(rutas_chunks, ruta_mp3)

    for ruta_chunk in rutas_chunks:
        try:
            os.remove(ruta_chunk)
        except Exception:
            pass

    if ok_union and os.path.exists(ruta_mp3):
        print(f"[VOICE LOCAL] ✅ Audio ensamblado y sincronizado al 100%: {ruta_mp3}")
        return ruta_mp3
    else:
        print("[VOICE LOCAL] ❌ Falló la unión de chunks con FFmpeg.")
        return None