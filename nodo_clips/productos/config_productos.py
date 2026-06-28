# -*- coding: utf-8 -*-
"""
config_productos.py - Configuracion del MODULO DE VIDEOS PUBLICITARIOS (image-to-video).

Genera un COMERCIAL del producto a partir de UNA foto de referencia, usando WAN
(image-to-video) local en la RTX 3060, con un PIPELINE DE CALIDAD para que la IA
NO deforme el producto (etiquetas, texto, bordes se mantienen).

Basado en investigacion tecnica real (ComfyUI/WAN 2026). Ver MODULO_PRODUCTOS.md.
IMPORTANTE: este modulo NUNCA sube nada a ninguna plataforma. Tu publicas a mano.
"""

VERSION_PRODUCTOS = "2026-06-23_prod_C_calidad"

# =============================================================================
# PIPELINE DE CALIDAD (el orden importa, cada paso reduce las fallas de la IA)
# =============================================================================
# 1. PREPARAR foto: limpiar/sharpen sutil + escalar a resolucion nativa de WAN.
# 2. GENERAR con WAN 2.2 14B (NO 5B) a resolucion nativa, prompt SIMPLE de accion,
#    movimiento CONTROLADO (motion bajo = menos deformacion), batch 4n+1.
# 3. VALIDAR: generar varias tomas (seeds distintas) y quedarse con la mejor.
# 4. UPSCALE CONSERVADOR con SeedVR2: preserva etiquetas/texto/bordes del producto
#    sin inventar detalles (es la clave para que el producto se vea fiel).
# 5. ENSAMBLAR: texto/precio/musica.

# -----------------------------------------------------------------------------
# 1. MODELO DE GENERACION (WAN 2.2 14B image-to-video, local en la 3060)
# -----------------------------------------------------------------------------
WAN_I2V = {
    "ip": "192.168.0.215",
    "puerto": 8600,
    # MODELO: 14B fp8 (cabe en 12GB y da CALIDAD). La investigacion es explicita:
    # "Never use the Wan 5B variant" — el 5B da peor calidad. Para producto = 14B.
    "modelo": "wan2.2_i2v_14B_fp8_scaled",
    # RESOLUCION NATIVA de WAN (clave para no introducir deformaciones).
    # Verticales nativas: 720x1264. Cuadrada: 960x960. Para producto vertical:
    "resolucion": (720, 1264),
    "duracion_clip_seg": 5,
    "fps": 16,                      # fps nativo de WAN (luego se interpola a 30)
    # PASOS: 20-30 es el rango bueno. Con LoRA Lightning se puede bajar a 4-8.
    "pasos": 28,
    "sampler": "uni_pc",            # sampler recomendado para WAN
    # MOVIMIENTO CONTROLADO: bajo = el producto se deforma MENOS. La causa #1 de
    # "smearing/warping" es demasiado movimiento. Para producto, movimiento sutil.
    "motion_strength": 0.45,        # 0.3-0.5 = sutil y seguro para productos
    # BATCH 4n+1 (5,9,13,17...) elimina el parpadeo entre frames (consistencia).
    "batch_size": 13,
    # VRAM: optimizaciones para que el 14B quepa en 12GB.
    "block_swap": True,             # intercambia bloques GPU<->RAM (cabe el 14B)
    "vae_tiled": True,              # VAE en mosaicos (menos pico de memoria)
    # Generar N tomas con seeds distintas y quedarse con la mejor (iterar).
    "intentos_por_escena": 3,
}

# LoRAs de aceleracion (opcionales; reducen MUCHO el tiempo de render).
# Si se activan, bajar 'pasos' a 4-8.
LORAS_ACELERACION = {
    "usar": False,                  # activar cuando esten descargadas
    "lightning": {"usar": False, "strength": 1.0},   # generacion en 4 pasos
    "lightx2v":  {"usar": False, "strength": 0.5},
    "causvid":   {"usar": False, "strength": 0.4},
}

# -----------------------------------------------------------------------------
# 1b. PREPARACION DE LA FOTO (antes de generar) — reduce deformaciones
# -----------------------------------------------------------------------------
PREP_FOTO = {
    # Subir resolucion de la foto ANTES y generar a resolucion menor preserva
    # detalle reduciendo VRAM (truco PRO de la investigacion).
    "upscale_previo": True,
    "sharpen_sutil": True,          # un sharpen leve ayuda a mantener bordes nitidos
    "fondo_limpio_recomendado": True,  # aviso: mejor foto con fondo limpio
}

# -----------------------------------------------------------------------------
# 4. UPSCALER CONSERVADOR (SeedVR2) — LA CLAVE para fidelidad del producto
# -----------------------------------------------------------------------------
# SeedVR2 es el upscaler que PRESERVA etiquetas, texto y bordes del producto sin
# inventar detalles. La investigacion: "conservative upscaling models are
# necessary for product images". Apache 2.0, gratis, corre en 12GB con block swap.
UPSCALER = {
    "usar": True,
    "modelo": "seedvr2_ema_3b_fp16",   # 3B fp16 va bien en 12GB (mejor que fp8 aqui)
    "resolucion_objetivo": 1080,       # altura objetivo tras el upscale
    "batch_size": 13,                  # 4n+1 para consistencia temporal
    "block_swap": 32,                  # para caber en 12GB
    "vae_tiled": True,
    # Truco SeedVR2: bajar la imagen a 0.35 megapixeles antes da mejor resultado.
    "downscale_previo_mp": 0.35,
    "pasadas_max": 2,                  # max 2 pasadas (4x); mas introduce artefactos
}

# -----------------------------------------------------------------------------
# ESCENAS PUBLICITARIAS — prompts SIMPLES y de ACCION (no recargados)
# La investigacion: prompts simples y centrados en la accion deforman menos.
# Cada escena: una accion de camara clara + ambiente breve.
# -----------------------------------------------------------------------------
ESCENAS_COMERCIAL = {
    "giro_estudio":     "the product slowly rotates on a clean studio background, soft professional lighting",
    "acercamiento":     "the camera slowly pushes in toward the product, warm elegant lighting, shallow depth of field",
    "mesa_premium":     "the product sits on a marble surface, the camera slowly orbits around it, premium lighting",
    "revelado_luz":     "soft light gradually reveals the product on a dark background, slow camera movement, dramatic",
    "ambiente_calido":  "the product in a warm cozy setting, gentle camera drift, natural daylight",
    "elevacion":        "the product floats and slowly turns, clean minimal background, premium commercial lighting",
}
ESCENA_DEFAULT = "acercamiento"
ESCENAS_POR_COMERCIAL = 2

# PROMPT que refuerza MANTENER el producto (simple, va junto a la escena).
PROMPT_MANTENER_PRODUCTO = "keep the exact same product, same shape, same color, same labels, photorealistic, "
# Negative anti-deformacion (lo que NO queremos).
NEGATIVE_PRODUCTO = (
    "deformed, distorted, warped, melting, morphing, changed product, different product, "
    "garbled text, distorted label, blurry, low quality, extra objects, duplicated product, "
    "smearing, flickering, artifacts, ugly, bad quality"
)

# -----------------------------------------------------------------------------
# FORMATO DEL COMERCIAL FINAL
# -----------------------------------------------------------------------------
FORMATO = {
    "orientacion": "vertical",
    "resolucion_vertical": (1080, 1920),
    "resolucion_horizontal": (1920, 1080),
    "fps": 30,                      # se interpola desde los 16fps de WAN
    "interpolar_a_30": True,        # interpolacion de frames para fluidez
    "duracion_total_max_seg": 20,
}

# -----------------------------------------------------------------------------
# PRESENTACION (texto, precio, musica) - se agrega DESPUES del pipeline IA
# -----------------------------------------------------------------------------
PRESENTACION = {
    "mostrar_texto": True,
    "posicion_texto": "inferior",
    "musica_fondo": True,
    "carpeta_musica": r"C:\NODO_CLIPS\productos\musica",
    "voz_corta": False,
    "logo_marca": False,
}
PLANTILLAS = {
    "oferta":   {"color_acento": "#FF3B30", "energia": "alta",  "texto_grande": True},
    "review":   {"color_acento": "#007AFF", "energia": "media", "texto_grande": False},
    "elegante": {"color_acento": "#C9A227", "energia": "baja",  "texto_grande": False},
    "lujo":     {"color_acento": "#1C1C1E", "energia": "baja",  "texto_grande": False},
}
PLANTILLA_DEFAULT = "elegante"

# -----------------------------------------------------------------------------
# RUTAS
# -----------------------------------------------------------------------------
RUTAS = {
    "referencia": r"C:\NODO_CLIPS\productos\referencia",
    "salida":     r"C:\NODO_CLIPS\productos\salida",
    "temp":       r"C:\NODO_CLIPS\productos\temp",
}

SUBIR_AUTOMATICO = False


def resumen():
    print("=" * 64)
    print(f"  MODULO PRODUCTOS (I2V de CALIDAD) - {VERSION_PRODUCTOS}")
    print(f"  Modelo: WAN 2.2 14B fp8 (calidad, NO el 5B)")
    print(f"  Resolucion nativa: {WAN_I2V['resolucion']} | movimiento: {WAN_I2V['motion_strength']} (sutil)")
    print(f"  Batch 4n+1: {WAN_I2V['batch_size']} (sin parpadeo) | intentos: {WAN_I2V['intentos_por_escena']}")
    print(f"  Upscaler conservador SeedVR2: {'SI' if UPSCALER['usar'] else 'no'} (preserva etiquetas/texto)")
    print(f"  Pipeline: preparar foto -> generar -> validar -> upscale -> ensamblar")
    print(f"  Subida automatica: {'SI' if SUBIR_AUTOMATICO else 'NO (tu publicas)'}")
    print("=" * 64)


if __name__ == "__main__":
    resumen()
