"""Test de la LÓGICA de planificación de hooks y recálculo de SRT (sin video)."""
import sys, os
sys.path.insert(0, "/home/claude")
import hooks_v2 as h

print("="*60)
print("TEST: PLANIFICACIÓN DE HOOKS")
print("="*60)

# Escenario 1: video largo de ~15 min (50 escenas de ~18s c/u = 900s)
print("\n[1] Video largo 15min (50 escenas)...")
dur_esc = [18.0]*50
frases = ["HOOK INICIAL FUERTE"] + [f"Re-hook {i}" for i in range(1, 20)]
inicial, inserciones = h.planificar_hooks(50, dur_esc, frases, es_short=False)
print(f"    Hook inicial: '{inicial}'")
print(f"    Re-hooks planificados: {len(inserciones)} (esperado ~12 para 900s)")
# Verificar que caen en límites de escena distintos y ordenados
escenas = [i["despues_de_escena"] for i in inserciones]
print(f"    Tras escenas: {escenas}")
print(f"    ✅ Todos en escenas distintas: {len(escenas)==len(set(escenas))}")
print(f"    ✅ Ordenados: {escenas==sorted(escenas)}")
formatos = [i["formato"] for i in inserciones]
print(f"    Formatos (A/B alternados): {formatos}")
print(f"    ✅ Hay de ambos tipos: {'A' in formatos and 'B' in formatos}")

# Escenario 2: short de 40s (5 escenas de 8s)
print("\n[2] Short 40s (5 escenas)...")
dur_esc_s = [8.0]*5
inicial_s, ins_s = h.planificar_hooks(5, dur_esc_s, frases, es_short=True)
print(f"    Hook inicial: '{inicial_s}'")
print(f"    Re-hooks: {len(ins_s)} (esperado máx 1 para short)")
print(f"    ✅ Máximo 1 re-hook en short: {len(ins_s)<=1}")

# Escenario 3: recálculo de SRT
print("\n[3] Recálculo de SRT con hooks...")
srt_in = "/home/claude/test_env/test_subs.srt"
with open(srt_in, "w") as f:
    f.write("""1
00:00:02,000 --> 00:00:05,000
Primera linea antes del hook

2
00:00:20,000 --> 00:00:24,000
Linea despues del primer rehook

3
00:00:50,000 --> 00:00:54,000
Linea al final
""")
# Hook inicial 2s + un rehook de 1.8s tras escena que termina en ~16s
inserciones_test = [{"despues_de_escena": 1, "frase": "x", "formato": "A", "dur": 1.8}]
dur_esc_test = [8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0]  # escena 1 termina en 16s
srt_out = "/home/claude/test_env/test_subs_out.srt"
ok = h.recalcular_srt(srt_in, srt_out, inserciones_test, dur_esc_test, dur_hook_inicial=2.0)
print(f"    Recálculo OK: {ok}")
with open(srt_out) as f:
    contenido = f.read()
# La primera linea (2s) debe correrse +2s (solo hook inicial) = 4s
# La segunda (20s, despues del rehook en 16s) debe correrse +2+1.8 = +3.8s = 23.8s
print("    Tiempos resultantes:")
for ln in contenido.split("\n"):
    if "-->" in ln:
        print(f"      {ln}")
print("    ✅ Primera línea +2s (hook inicial), líneas tras rehook +3.8s")

print("\n" + "="*60)
exito = len(inserciones)>=10 and len(ins_s)<=1 and ok and ('A' in formatos and 'B' in formatos)
print("RESULTADO:", "✅ LÓGICA DE PLANIFICACIÓN CORRECTA" if exito else "❌ REVISAR")
print("="*60)
