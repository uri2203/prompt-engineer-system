# MÓDULO DE VIDEOS PUBLICITARIOS DE PRODUCTOS (image-to-video)

## QUÉ ES (enfoque CORRECTO)
Subes UNA foto de referencia del producto. La IA "mira" esa foto, mantiene el
producto idéntico, y GENERA un video publicitario nuevo (comercial completo)
donde el producto aparece en escenas/ambientes con movimiento real.

**La foto NO se convierte en slideshow.** La foto es solo la REFERENCIA para que
la IA sepa qué producto mostrar. El video (escenas, movimiento, cámara) lo crea
la IA desde cero, manteniendo el producto consistente.

## TIPO DE VIDEO ELEGIDO
Comercial completo: el producto aparece en escenas/ambientes publicitarios
(no solo cámara orbitando un fondo vacío). Ej: el producto sobre una mesa elegante
con luz dramática, en uso, en un ambiente que vende el producto.

## CÓMO FUNCIONA (image-to-video / I2V)
La foto del producto es el "ancla" (primer fotograma de referencia). La IA genera
el resto del video manteniendo el producto igual (sin "visual drift": los detalles,
color, forma del producto se conservan), y le añade el movimiento y la escena que
tú describas en el prompt.

  Foto de referencia del producto  +  prompt del comercial
  (fondo limpio idealmente)            ("el producto en una mesa de marmol,
                |                        luz calida, camara que se acerca lento")
                v
  WAN (image-to-video) en la RTX 3060
                |
                v
  Video del producto en esa escena, con movimiento real
                |
                v
  Se le agrega texto/precio/musica (opcional)
                |
                v
  Comercial listo  ->  TU lo publicas (NUNCA se sube solo)

## MOTOR: WAN LOCAL (gratis, en tu RTX 3060)
- WAN es el modelo de I2V que corre LOCAL (los buenos de nube -Kling, Seedance,
  Veo- son de pago). WAN es gratis pero requiere ComfyUI instalado.
- Tu le das: la foto + un prompt de movimiento/escena. WAN genera el video.
- Es LENTO (varios minutos por clip de 5s en la 3060), pero para productos no
  necesitas volumen: generas el comercial de un producto cuando lo necesites.

## REQUISITOS
1. ComfyUI instalado en la PC GPU (192.168.0.215) - aun NO esta. Primer paso.
2. Modelo WAN I2V descargado en ComfyUI (el que quepa en 12GB).
3. Foto de buena calidad del producto: fondo limpio, producto bien visible,
   sin texto encima, buena resolucion. Mejor foto = mejor mantiene el producto.

## LO QUE LA IA HACE BIEN Y LO QUE NO (honesto)
BIEN:
- Mantiene el producto consistente (forma, color) gracias a la referencia.
- Genera movimiento de camara y escenas atractivas.
- Varias variaciones del mismo producto en distintos ambientes.

MAL (limitaciones reales de 2026):
- Detalles MUY finos pueden distorsionarse: etiquetas, texto en el producto,
  logos pequenos, telas con patron complejo, liquidos. La IA a veces los deforma.
- Por eso conviene generar varias tomas y elegir la mejor (iterar).
- Productos con texto/marca muy visible son los mas dificiles de mantener perfectos.

## ESTRUCTURA DE ARCHIVOS (nodo_clips/productos/)
nodo_clips/productos/
├── product_i2v.py             <- motor image-to-video (genera el comercial con WAN)
├── config_productos.py        <- configuracion (escenas, movimientos, presentacion)
├── ensamblar_comercial.py     <- agrega texto/precio/musica al video generado
├── referencia/                <- AQUI subes la foto del producto
└── salida/                    <- AQUI sale el comercial generado

## PLAN POR FASES
### FASE P0 - Base (ahora, sin generar todavia)
- [x] Documentacion con el enfoque correcto (I2V).
- [ ] config_productos.py reenfocado a I2V (escenas, prompts de comercial).
- [ ] product_i2v.py base (estructura del flujo, listo para cuando WAN este).

### FASE P1 - Instalar WAN (requiere ComfyUI)
- [ ] Instalar ComfyUI en la PC GPU.
- [ ] Descargar el modelo WAN I2V que quepa en 12GB.
- [ ] Probar generar 1 video desde 1 foto de producto. Medir tiempo y calidad.

### FASE P2 - Comercial completo
- [ ] Generar el video I2V + agregar texto/precio/musica.
- [ ] Plantillas de escena (producto en mesa, en uso, ambiente premium...).
- [ ] Generar varias variaciones y elegir la mejor.

### FASE P3 - Afinar
- [ ] Ajustar prompts de escena por tipo de producto.
- [ ] Mejorar la consistencia del producto (mejores fotos de referencia, seeds).

## REGLAS
- Dentro de nodo_clips/productos/ - separado de todo lo demas.
- NUNCA sube a plataformas. Tu publicas.
- NO toca el sistema de imagenes ni los clips de canal.
- Es LENTO (I2V con WAN): para productos puntuales, no para volumen.

## NOTA
El motor de slideshow anterior (product_clips.py) queda OBSOLETO - esto lo
reemplaza con el enfoque correcto (I2V). Si en algun momento quieres un slideshow
rapido como respaldo, ese codigo sigue en el historial de git.
