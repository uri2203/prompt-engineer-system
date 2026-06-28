# -*- coding: utf-8 -*-
"""
config_productos.py - Configuracion del MODULO DE VIDEOS PUBLICITARIOS (image-to-video).

Genera un COMERCIAL del producto a partir de UNA foto de referencia, usando WAN
(image-to-video) local en la RTX 3060. La foto es la referencia; la IA genera el
video manteniendo el producto y poniendolo en escenas publicitarias con movimiento.

IMPORTANTE: este modulo NUNCA sube nada a ninguna plataforma. Tu publicas a mano.
"""

VERSION_PRODUCTOS = "2026-06-23_prod_B_i2v"

# -----------------------------------------------------------------------------
# MOTOR DE GENERACION (WAN image-to-video, local en la 3060)
# -----------------------------------------------------------------------------
WAN_I2V = {
    "ip": "192.168.0.215",          # PC GPU
    "puerto": 8600,                 # servidor de WAN (ComfyUI / API)
    "modelo": "wan_i2v",            # modelo image-to-video que quepa en 12GB
    "resolucion": (768, 768),       # resolucion del video generado
    "duracion_clip_seg": 5,         # cada generacion de WAN (clips cortos)
    "fps": 16,                      # fps del video generado por WAN
    "pasos": 30,                    # calidad (mas pasos = mejor, mas lento)
    "intentos_por_escena": 2,       # generar N tomas y quedarse con la mejor
}

# -----------------------------------------------------------------------------
# ESCENAS PUBLICITARIAS (el producto aparece en estos ambientes)
# Cada escena es un prompt de movimiento+ambiente. La IA mantiene el producto
# de la foto y lo coloca en estas escenas. Se eligen 1 o varias por comercial.
# -----------------------------------------------------------------------------
ESCENAS_COMERCIAL = {
    "premium_mesa":     "the product on a luxurious marble table, warm dramatic lighting, "
                        "slow cinematic dolly-in, premium commercial, shallow depth of field, "
                        "elegant atmosphere, soft bokeh background",
    "estudio_limpio":   "the product on a clean studio background, professional product lighting, "
                        "smooth slow camera orbit around the product, crisp and sharp, "
                        "high-end commercial look, subtle reflections",
    "ambiente_uso":     "the product in a real-life lifestyle setting being showcased, "
                        "natural warm light, gentle camera movement, aspirational mood, "
                        "cinematic commercial, depth and atmosphere",
    "dramatico_oscuro": "the product highlighted with dramatic spotlight on a dark background, "
                        "glowing rim light, slow reveal camera movement, luxury commercial, "
                        "high contrast, premium and exclusive feel",
    "dinamico_energia": "the product with dynamic energy, particles and light around it, "
                        "fast engaging camera movement, vibrant colors, modern commercial, "
                        "exciting and bold, eye-catching",
    "naturaleza_fresco":"the product in a fresh natural environment with soft daylight, "
                        "clean and organic mood, gentle floating camera, wholesome commercial, "
                        "natural textures and light",
}

# Escena por defecto y cuantas escenas distintas combinar en un comercial
ESCENA_DEFAULT = "premium_mesa"
ESCENAS_POR_COMERCIAL = 2          # combina N escenas distintas en el comercial final

# -----------------------------------------------------------------------------
# PROMPT BASE (se antepone para reforzar que MANTENGA el producto)
# Clave para que la IA no deforme el producto de la foto.
# -----------------------------------------------------------------------------
PROMPT_MANTENER_PRODUCTO = (
    "keep the exact same product from the reference image, same shape, same color, "
    "same details, do not change the product, photorealistic, high quality, "
)
# Lo que NO queremos que pase
NEGATIVE_PRODUCTO = (
    "deformed product, distorted product, changed product, different product, "
    "morphing, melting, warped, blurry, low quality, extra objects, "
    "garbled text, distorted logo, ugly, artifacts"
)

# -----------------------------------------------------------------------------
# FORMATO DEL COMERCIAL FINAL
# -----------------------------------------------------------------------------
FORMATO = {
    "orientacion": "vertical",      # "vertical" (9:16) | "horizontal" (16:9)
    "resolucion_vertical": (1080, 1920),
    "resolucion_horizontal": (1920, 1080),
    "fps": 30,                      # fps del comercial final (se interpola desde WAN)
    "duracion_total_max_seg": 20,   # tope del comercial final
}

# -----------------------------------------------------------------------------
# PRESENTACION (texto, precio, musica) - se agrega DESPUES de generar el video IA
# -----------------------------------------------------------------------------
PRESENTACION = {
    "mostrar_texto": True,
    "posicion_texto": "inferior",
    "musica_fondo": True,
    "carpeta_musica": r"C:\NODO_CLIPS\productos\musica",
    "voz_corta": False,             # narracion corta opcional (maquina de voz 251)
    "logo_marca": False,
}

PLANTILLAS = {
    "oferta":    {"color_acento": "#FF3B30", "energia": "alta",  "texto_grande": True},
    "review":    {"color_acento": "#007AFF", "energia": "media", "texto_grande": False},
    "elegante":  {"color_acento": "#C9A227", "energia": "baja",  "texto_grande": False},
    "lujo":      {"color_acento": "#1C1C1E", "energia": "baja",  "texto_grande": False},
}
PLANTILLA_DEFAULT = "elegante"

# -----------------------------------------------------------------------------
# RUTAS
# -----------------------------------------------------------------------------
RUTAS = {
    "referencia": r"C:\NODO_CLIPS\productos\referencia",  # AQUI subes la foto del producto
    "salida":     r"C:\NODO_CLIPS\productos\salida",      # AQUI sale el comercial
    "temp":       r"C:\NODO_CLIPS\productos\temp",
}

# NUNCA subir a plataformas. El usuario publica manualmente.
SUBIR_AUTOMATICO = False


def resumen():
    print("=" * 62)
    print(f"  MODULO DE PRODUCTOS (image-to-video) - {VERSION_PRODUCTOS}")
    print(f"  Motor: WAN I2V local en la 3060 (la foto es referencia)")
    print(f"  La IA genera un COMERCIAL del producto en escenas/ambientes")
    print(f"  Escenas por comercial: {ESCENAS_POR_COMERCIAL} (de {len(ESCENAS_COMERCIAL)} disponibles)")
    print(f"  Formato: {FORMATO['orientacion']} @ {FORMATO['fps']}fps")
    print(f"  Texto/precio: {'si' if PRESENTACION['mostrar_texto'] else 'no'} | "
          f"Musica: {'si' if PRESENTACION['musica_fondo'] else 'no'}")
    print(f"  Subida automatica: {'SI' if SUBIR_AUTOMATICO else 'NO (tu publicas)'}")
    print("=" * 62)


if __name__ == "__main__":
    resumen()
