# -*- coding: utf-8 -*-
"""
config_clips.py — Configuración central del SISTEMA DE CLIPS DE VIDEO.

Este sistema es INDEPENDIENTE del sistema de imágenes actual (nodo_xeon).
Aquí se define todo lo configurable: modo de operación, modelos por tarjeta,
resoluciones, posiciones de los clips en modo híbrido, IPs y puertos.

NADA de este archivo afecta al worker de imágenes actual.
"""

# ─────────────────────────────────────────────────────────────────────────────
# VERSIÓN (para confirmar qué versión está cargada, igual que el worker actual)
# ─────────────────────────────────────────────────────────────────────────────
VERSION_CLIPS = "2026-06-23_clips_A"

# ─────────────────────────────────────────────────────────────────────────────
# MODO DE OPERACIÓN — la decisión principal
# ─────────────────────────────────────────────────────────────────────────────
#   "completo" → TODO el video con clips de video (lento: ~2-3 videos largos/día).
#                Para videos estrella de máxima calidad.
#   "hibrido"  → Clips de video SOLO en el hook + N momentos clave; el resto son
#                imágenes (rápido: ~15-25 videos largos/día). RECOMENDADO.
MODO = "hibrido"   # "completo" | "hibrido"

# En modo híbrido: cuántos clips de video y en qué parte del video van.
# El hook inicial es el más importante (retención). Los momentos de impacto
# rompen la sensación de "presentación de fotos".
HIBRIDO_CONFIG = {
    "clip_en_hook_inicial": True,    # los primeros segundos en video real
    "clips_en_momentos": 2,          # cuántos clips de impacto dentro del video
    "duracion_clip_seg": 5,          # duración de cada clip de video
    # el resto de escenas son imágenes (las genera el sistema actual / SD)
}

# ─────────────────────────────────────────────────────────────────────────────
# SERVIDORES DE GENERACIÓN DE CLIPS (uno por tarjeta)
# ─────────────────────────────────────────────────────────────────────────────
# Ambas tarjetas están en la misma PC GPU (192.168.0.215), en puertos distintos.
SERVIDOR_3060 = {
    "ip": "192.168.0.215",
    "puerto": 8600,
    "vram_gb": 12,
    "modelo": "wan2.2_5b",           # modelo que cabe holgado en 12GB
    "resolucion": (768, 768),        # resolución de los clips (ajustable)
    "pasos": 30,                     # más pasos = mejor calidad, más lento
    "fps_clip": 16,                  # fps del clip generado
}
SERVIDOR_3050 = {
    "ip": "192.168.0.215",
    "puerto": 8601,
    "vram_gb": 8,
    "modelo": "wan2.2_5b",           # mismo modelo pero con ajustes más ligeros
    "resolucion": (640, 640),        # menor resolución para caber en 8GB
    "pasos": 25,                     # un poco menos de pasos (más rápido)
    "fps_clip": 16,
}

# ¿Usar ambas tarjetas? Si la 3050 da problemas de VRAM, poner False y solo usa la 3060.
USAR_AMBAS_TARJETAS = True

# ─────────────────────────────────────────────────────────────────────────────
# MÁQUINA DE VOZ (la misma que el sistema actual — se reutiliza tal cual)
# ─────────────────────────────────────────────────────────────────────────────
VOZ = {
    "ip": "192.168.0.251",
    "puerto": 8000,
    # La voz se genera EN PARALELO con los clips (no espera a que terminen).
    "paralelo": True,
}

# ─────────────────────────────────────────────────────────────────────────────
# ENSAMBLAJE
# ─────────────────────────────────────────────────────────────────────────────
ENSAMBLAJE = {
    # Codificar el MP4 final con NVENC en la 3060 (mucho más rápido que el Xeon por CPU).
    "usar_nvenc_3060": True,
    "nvenc_ip": "192.168.0.215",
    # Si NVENC falla, caer a codificación por CPU en el Xeon (libx264) como respaldo.
    "fallback_cpu": True,
}

# ─────────────────────────────────────────────────────────────────────────────
# PROMPTS DE VIDEO POR CANAL (se afinarán como se hizo con las imágenes)
# Por ahora, base. En la Fase 6 se ajustan con pruebas reales.
# Los clips de video describen MOVIMIENTO (no solo la escena), porque eso es lo
# que diferencia un clip de una imagen.
# ─────────────────────────────────────────────────────────────────────────────
ESTILO_VIDEO_POR_CANAL = {
    "la viuda":          "cinematic horror, slow ominous camera movement, drifting shadows, "
                         "subtle fog motion, dread atmosphere, dark, film grain",
    "monkygraff":        "cinematic documentary, slow dramatic push-in, subtle map and data motion, "
                         "serious geopolitical tone, high contrast",
    "filtradomx":        "cinematic drama, intimate slow motion, emotional close-up movement, "
                         "moody lighting, tension",
    "laesquinarandom":   "funny cartoon animation, bouncy lively motion, vibrant colors, "
                         "exaggerated comedic movement, 2D animated",
    "tuialista":         "cinematic tech, smooth dynamic camera movement, glowing interfaces in motion, "
                         "dramatic teal and orange lighting, hyper-realistic, premium",
    "umbral alterno":    "epic cinematic, sweeping camera movement, atmospheric haze drifting, "
                         "documentary scale, contemplative, photorealistic",
}

# ─────────────────────────────────────────────────────────────────────────────
# RUTAS LOCALES (en la PC que corra el worker de clips)
# ─────────────────────────────────────────────────────────────────────────────
RUTAS = {
    "clips_generados": r"C:\NODO_CLIPS\clips",        # clips de video crudos
    "cola_clips":      r"C:\NODO_CLIPS\cola",         # cola de trabajos
    "salida":          r"C:\NODO_CLIPS\salida",       # videos finales ensamblados
}


def resumen():
    """Imprime un resumen de la configuración actual (para confirmar al arrancar)."""
    print("=" * 60)
    print(f"  SISTEMA DE CLIPS — {VERSION_CLIPS}")
    print(f"  MODO: {MODO.upper()}")
    if MODO == "hibrido":
        n = (1 if HIBRIDO_CONFIG['clip_en_hook_inicial'] else 0) + HIBRIDO_CONFIG['clips_en_momentos']
        print(f"  Clips de video por video: {n} (hook + {HIBRIDO_CONFIG['clips_en_momentos']} momentos)")
        print(f"  El resto de escenas: imágenes (sistema actual)")
    else:
        print(f"  TODO el video con clips (modo completo)")
    print(f"  Tarjetas: 3060{' + 3050' if USAR_AMBAS_TARJETAS else ' (sola)'}")
    print(f"  Voz en paralelo: {'sí' if VOZ['paralelo'] else 'no'}")
    print(f"  Ensamblaje NVENC en 3060: {'sí' if ENSAMBLAJE['usar_nvenc_3060'] else 'no'}")
    print("=" * 60)


if __name__ == "__main__":
    resumen()
