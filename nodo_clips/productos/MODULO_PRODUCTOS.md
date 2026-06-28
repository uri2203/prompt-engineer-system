# MODULO DE VIDEOS PUBLICITARIOS DE PRODUCTOS (image-to-video de CALIDAD)

## QUE ES
Subes UNA foto de referencia del producto. La IA mantiene el producto identico y
GENERA un comercial donde el producto aparece en escenas/ambientes con movimiento
real. La foto es la REFERENCIA; el video lo crea la IA.

## EL PROBLEMA QUE RESUELVE: que la IA NO deforme el producto
Las IA de video deforman detalles finos (etiquetas, texto, logos, bordes). Tras
investigacion tecnica a fondo (ComfyUI/WAN 2026), este modulo implementa las
soluciones REALES que evitan eso. NO son parches: son las tecnicas que de verdad
funcionan en produccion.

## LAS 7 SOLUCIONES IMPLEMENTADAS (de la investigacion)

### 1. MODELO CORRECTO: WAN 2.2 14B (NO el 5B)
La investigacion es explicita: "Never use the Wan 5B variant". El 5B da peor
calidad. El 14B en fp8 cabe en 12GB (con block swap) y da calidad de produccion.

### 2. RESOLUCION NATIVA de WAN (720x1264 vertical, 960x960 cuadrado)
Generar en la resolucion nativa del modelo evita que WAN reescale internamente e
introduzca deformaciones. Truco PRO: subir la foto de resolucion ANTES y generar a
resolucion nativa preserva detalle.

### 3. PROMPTS SIMPLES Y DE ACCION
"the camera slowly pushes in toward the product". NO prompts recargados. Los
prompts complejos confunden al modelo y aumentan la deformacion.

### 4. MOVIMIENTO CONTROLADO (motion_strength bajo: 0.45)
La causa #1 del "smearing/warping" (deformacion) es demasiado movimiento. Para
productos, movimiento sutil = el producto se mantiene fiel.

### 5. UPSCALER CONSERVADOR SeedVR2 (LA CLAVE)
SeedVR2 es un upscaler conservador que PRESERVA etiquetas, texto y bordes del
producto SIN inventar detalles. La investigacion: "conservative upscaling models
are necessary for product images". Apache 2.0, gratis, corre en 12GB.
Pipeline: generar (baja res, rapido) -> SeedVR2 sube a 1080p preservando todo.

### 6. BATCH 4n+1 (5, 9, 13, 17...) = SIN PARPADEO
Procesar los frames en lotes de 4n+1 elimina el parpadeo/flickering entre frames
(consistencia temporal). batch alto = mas estable.

### 7. VARIAS TOMAS + elegir la mejor
Se generan 3 tomas con seeds distintas por escena. Si una sale con deformacion,
otra seed suele salir bien. Se itera (es lo que hacen los profesionales).

## PIPELINE DE CALIDAD (orden de los pasos)
  Foto del producto
       |
       v
  1. PREPARAR: sharpen sutil + escalar a resolucion nativa de WAN
       |
       v
  2. GENERAR con WAN 2.2 14B: prompt simple, movimiento sutil, batch 4n+1,
     3 tomas con seeds distintas -> elegir la mejor
       |
       v
  3. UPSCALE CONSERVADOR con SeedVR2: sube a 1080p preservando etiquetas/texto/bordes
       |
       v
  4. ENSAMBLAR: texto/precio/musica
       |
       v
  Comercial de calidad -> TU lo publicas (NUNCA se sube solo)

## ACELERACION OPCIONAL (LoRAs)
Lightning (4 pasos), CausVid, Lightx2v reducen MUCHO el tiempo de render. Estan en
el config (LORAS_ACELERACION), desactivadas; se activan cuando se descarguen y se
bajan los pasos a 4-8.

## REQUISITOS (instalar en la PC GPU)
1. ComfyUI.
2. Modelo WAN 2.2 14B fp8 i2v (wan2.2_i2v_14B_fp8_scaled).
3. SeedVR2 (upscaler conservador, nodo de ComfyUI, modelo 3B fp16).
4. Foto de buena calidad del producto: fondo limpio, bien visible, buena resolucion.

## ARCHIVOS (nodo_clips/productos/)
- product_i2v.py        -> motor del pipeline de calidad
- config_productos.py   -> toda la configuracion de calidad
- (product_clips.py)    -> OBSOLETO (slideshow viejo)

## NOTA DE TIEMPO (honesto)
- Generar a baja resolucion + upscalar es mas rapido y da MEJOR calidad que generar
  directo a alta resolucion.
- Aun asi, I2V de calidad en una 3060 toma varios minutos por escena.
- Para productos no necesitas volumen: generas el comercial de un producto cuando
  lo necesites, con calidad.

## REGLAS
- Dentro de nodo_clips/productos/ - separado de todo lo demas.
- NUNCA sube a plataformas. Tu publicas.
- NO toca el sistema de imagenes ni los clips de canal.
