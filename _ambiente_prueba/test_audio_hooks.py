"""Test: reconstrucción del audio con silencios de hooks."""
import sys, os, subprocess
sys.path.insert(0, "/home/claude")
import hooks_v2 as h

CARPETA = "/home/claude/test_env/audio_test"
os.makedirs(CARPETA, exist_ok=True)
print("="*60); print("TEST: AUDIO CON HOOKS"); print("="*60)

# Audio de narración de 40s
audio_in = os.path.join(CARPETA, "narracion.mp3")
subprocess.run(f"ffmpeg -y -f lavfi -i sine=frequency=300:duration=40 -c:a libmp3lame {audio_in}",
               shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
dur_in = h._dur(audio_in)
print(f"\nNarración original: {dur_in:.2f}s")

# 5 escenas de 8s, hook inicial (2s) + 1 rehook (1.8s) tras escena 2
dur_esc = [8.0]*5
inserciones = [{"despues_de_escena": 2, "frase": "x", "formato": "A", "dur": 1.8}]
audio_out = os.path.join(CARPETA, "narracion_hooks.mp3")
ok = h.construir_audio_con_hooks(audio_in, audio_out, inserciones, dur_esc,
                                  dur_hook_inicial=2.0, carpeta=CARPETA, hook_inicial_presente=True)
dur_out = h._dur(audio_out)
esperado = dur_in + 2.0 + 1.8  # original + hook inicial + 1 rehook
print(f"Audio con hooks: {dur_out:.2f}s (esperado ~{esperado:.2f}s)")
print(f"OK reconstrucción: {ok}")
print(f"✅ Duración correcta: {abs(dur_out - esperado) < 1.0}")
# Verificar que es audio válido
r = subprocess.run(f"ffprobe -v error -show_entries stream=codec_type -of csv=p=0 {audio_out}",
                   shell=True, capture_output=True, text=True)
print(f"✅ Audio válido: {'audio' in r.stdout}")

print("\n" + "="*60)
exito = ok and abs(dur_out - esperado) < 1.0 and 'audio' in r.stdout
print("RESULTADO:", "✅ AUDIO CON HOOKS CORRECTO" if exito else "❌ REVISAR")
print("="*60)
