# -*- coding: utf-8 -*-
"""
config_productos.py — Configuración del MÓDULO DE CLIPS DE PRODUCTOS.

Genera videos cortos de productos a partir de FOTOS del producto, dándoles
movimiento profesional. Separado de los clips de canal y del sistema de imágenes.

IMPORTANTE: este módulo NUNCA sube nada a ninguna plataforma. Tú publicas a mano.
"""

VERSION_PRODUCTOS = "2026-06-23_prod_A"

# ─────────────────────────────────────────────────────────────────────────────
# MODO DE MOVIMIENTO
# ─────────────────────────────────────────────────────────────────────────────
#   "imagen" → movimiento simulado sobre la foto (zoom, paneo, parallax). RÁPIDO,
#              no necesita ComfyUI ni GPU pesada. RECOMENDADO para empezar.
#   "ia_video" → genera movimiento real con WAN (el producto gira, cámara orbita).
#                Más impactante pero LENTO. Requiere ComfyUI instalado.
MODO_MOVIMIENTO = "imagen"   # "imagen" | "ia_video"

# ─────────────────────────────────────────────────────────────────────────────
# FORMATO DEL CLIP
# ─────────────────────────────────────────────────────────────────────────────
FORMATO = {
    "orientacion": "vertical",      # "vertical" (9:16, para shorts/reels) | "horizontal" (16:9)
    "resolucion_vertical": (1080, 1920),
    "resolucion_horizontal": (1920, 1080),
    "fps": 30,
    "duracion_por_foto_seg": 3.0,   # cuánto dura cada foto en pantalla
    "duracion_total_max_seg": 30,   # tope de duración del clip
}

# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTO POR IMAGEN (modo "imagen")
# Cada foto recibe uno de estos movimientos, rotando para dar variedad.
# ─────────────────────────────────────────────────────────────────────────────
MOVIMIENTOS_IMAGEN = [
    "zoom_in_lento",        # acercamiento suave
    "zoom_out_lento",       # alejamiento suave
    "paneo_izq_der",        # paneo horizontal
    "paneo_arriba_abajo",   # paneo vertical
    "zoom_in_diagonal",     # acercamiento con leve desplazamiento
    "parallax_suave",       # efecto 2.5D de profundidad (si la foto lo permite)
]

# Transición entre fotos
TRANSICIONES = ["fade", "slide", "zoom"]   # se alternan para variedad

# ─────────────────────────────────────────────────────────────────────────────
# PRESENTACIÓN (texto, precio, música) — todo OPCIONAL
# ─────────────────────────────────────────────────────────────────────────────
PRESENTACION = {
    "mostrar_texto": True,          # poner texto en pantalla (nombre/precio)
    "posicion_texto": "inferior",   # "inferior" | "superior"
    "musica_fondo": True,           # poner música (carpeta de música)
    "carpeta_musica": r"C:\NODO_CLIPS\productos\musica",
    "voz_corta": False,             # narración corta opcional (usa la máquina de voz)
    "logo_marca": False,            # poner un logo/marca de agua del usuario
}

# Plantillas de estilo de presentación (se elige una al generar)
PLANTILLAS = {
    "oferta":    {"color_acento": "#FF3B30", "energia": "alta",  "texto_grande": True},
    "review":    {"color_acento": "#007AFF", "energia": "media", "texto_grande": False},
    "elegante":  {"color_acento": "#C9A227", "energia": "baja",  "texto_grande": False},
    "unboxing":  {"color_acento": "#34C759", "energia": "alta",  "texto_grande": True},
}
PLANTILLA_DEFAULT = "oferta"

# ─────────────────────────────────────────────────────────────────────────────
# MOVIMIENTO POR IA DE VIDEO (modo "ia_video") — usa las tarjetas como los clips de canal
# ─────────────────────────────────────────────────────────────────────────────
IA_VIDEO = {
    "ip": "192.168.0.215",
    "puerto": 8600,                 # mismo servidor de clips (3060)
    "duracion_clip_seg": 5,
    "estilo": "professional product video, smooth orbiting camera, studio lighting, "
              "clean background, premium commercial look, sharp focus",
}

# ─────────────────────────────────────────────────────────────────────────────
# RUTAS
# ─────────────────────────────────────────────────────────────────────────────
RUTAS = {
    "entrada":  r"C:\NODO_CLIPS\productos\entrada",   # AQUÍ subes las fotos del producto
    "salida":   r"C:\NODO_CLIPS\productos\salida",    # AQUÍ salen los clips listos
    "temp":     r"C:\NODO_CLIPS\productos\temp",
}

# NUNCA subir a plataformas. El usuario publica manualmente.
SUBIR_AUTOMATICO = False   # debe quedarse SIEMPRE en False


def resumen():
    print("=" * 60)
    print(f"  MÓDULO DE PRODUCTOS — {VERSION_PRODUCTOS}")
    print(f"  Movimiento: {MODO_MOVIMIENTO.upper()}", end="")
    print("  (rápido, sin ComfyUI)" if MODO_MOVIMIENTO == "imagen" else "  (lento, con WAN)")
    print(f"  Formato: {FORMATO['orientacion']} @ {FORMATO['fps']}fps")
    print(f"  Texto en pantalla: {'sí' if PRESENTACION['mostrar_texto'] else 'no'}")
    print(f"  Música: {'sí' if PRESENTACION['musica_fondo'] else 'no'}")
    print(f"  Plantilla: {PLANTILLA_DEFAULT}")
    print(f"  Subida automática: {'SÍ' if SUBIR_AUTOMATICO else 'NO (tú publicas)'}")
    print("=" * 60)


if __name__ == "__main__":
    resumen()
