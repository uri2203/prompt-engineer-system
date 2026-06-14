"""TEST AISLADO DEL MÓDULO DE HOOKS — genera video base y le inserta hooks."""
import os, sys, subprocess
sys.path.insert(0, "/home/claude")
import hooks_modulo as hm

CARPETA = "/home/claude/test_env/hooks_test"
os.makedirs(CARPETA, exist_ok=True)
W, H, FPS = 576, 1024, 30

print("="*60)
print("TEST DEL MÓDULO DE HOOKS")
print("="*60)

# 1. Crear un video base con narración (40s, con audio)
print("\n[1] Creando video base de 40s con audio...")
video_base = os.path.join(CARPETA, "base.mp4")
subprocess.run(
    f"ffmpeg -y -f lavfi -i testsrc=s={W}x{H}:d=40:r={FPS} "
    f"-f lavfi -i sine=frequency=300:duration=40 "
    f"-c:v libx264 -pix_fmt yuv420p -c:a aac -shortest {video_base}",
    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
dur_base = hm._dur(video_base)
print(f"    Video base: {dur_base:.1f}s, válido: {hm._clip_valido(video_base)}")

# 2. Crear imágenes de escena de prueba (con detalle)
print("\n[2] Creando imágenes de escena de prueba...")
imagenes = []
for i in range(5):
    img = os.path.join(CARPETA, f"escena_{i}.png")
    subprocess.run(f"ffmpeg -y -f lavfi -i testsrc=s={W}x{H}:d=1 -frames:v 1 {img}",
                   shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    imagenes.append(img)
print(f"    {len(imagenes)} imágenes creadas")

# 3. Frases de hook (como las daría Gemini)
hooks_frases = [
    "Lo que viene te va a perturbar",          # inicial fuerte
    "Pero esto lo cambió todo",                 # re-hook 1
    "Nadie esperaba lo que pasó después",       # re-hook 2
]

# 4. Insertar hooks
print("\n[3] Insertando hooks en el video...")
video_con_hooks = os.path.join(CARPETA, "con_hooks.mp4")
# Verificar PIL
try:
    from PIL import Image
    pil = True
except:
    pil = False
fuentes = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]
fuentes = [f for f in fuentes if os.path.exists(f)]
print(f"    PIL disponible: {pil} | Fuentes: {len(fuentes)}")

ok = hm.insertar_hooks_retencion(
    video_base, video_con_hooks, hooks_frases, imagenes,
    CARPETA, W, H, FPS, pil, fuentes, es_short=False)

# 5. Verificar resultado
print("\n[4] Verificando resultado...")
dur_final = hm._dur(video_con_hooks)
print(f"    Hooks insertados: {ok}")
print(f"    Duración original: {dur_base:.1f}s → con hooks: {dur_final:.1f}s")
print(f"    El video creció (hooks añadidos): {'✅ SÍ' if dur_final > dur_base else '❌ NO'}")
print(f"    Video final válido y reproducible: {'✅ SÍ' if hm._clip_valido(video_con_hooks) else '❌ NO'}")
# Verificar que tiene audio
r = subprocess.run(f"ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 {video_con_hooks}",
                   shell=True, capture_output=True, text=True)
print(f"    Tiene pista de audio: {'✅ SÍ' if 'audio' in r.stdout else '❌ NO'}")

# 6. Probar el caso de fallo (debe devolver el original intacto)
print("\n[5] Prueba de seguridad: si no hay imágenes, NO debe romper...")
video_seguro = os.path.join(CARPETA, "seguro.mp4")
ok2 = hm.insertar_hooks_retencion(video_base, video_seguro, hooks_frases, [],
                                   CARPETA, W, H, FPS, pil, fuentes)
print(f"    Resultado válido aún sin imágenes: {'✅ SÍ' if hm._clip_valido(video_seguro) else '❌ NO'}")

print("\n" + "="*60)
exito = ok and dur_final > dur_base and hm._clip_valido(video_con_hooks) and 'audio' in r.stdout
print("RESULTADO:", "✅ MÓDULO DE HOOKS FUNCIONA" if exito else "❌ REVISAR")
print("="*60)
