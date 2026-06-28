# MÓDULO DE CLIPS DE PRODUCTOS (dentro de nodo_clips/)

## QUÉ ES
Un apartado SEPARADO para generar **videos cortos de productos** a partir de
imágenes del producto, dándoles movimiento profesional (rotación, zoom, ángulos,
presentación dinámica). Sirve para promoción de productos (afiliados, tiendas,
reviews), NO para los 6 canales de contenido.

## DIFERENCIA CLAVE CON LOS CLIPS DE CANAL
| Aspecto              | Clips de CANAL (los 6 canales)      | Clips de PRODUCTO                    |
|----------------------|--------------------------------------|--------------------------------------|
| Entrada              | Prompt de texto (la IA inventa)      | IMÁGENES reales del producto         |
| Objetivo             | Contenido (terror, tech, etc.)       | Vender/promocionar un producto        |
| Voz                  | Narración larga del guion            | Opcional (corta o solo música)        |
| Subida a YouTube     | (no se automatiza ninguna)           | NUNCA — el usuario las publica a mano |
| Longitud             | Video largo o short                  | Clip corto (5-30s típico)            |

## DE DÓNDE SALE EL MOVIMIENTO
El producto entra como IMAGEN (foto del producto que tú subes). El sistema le da
movimiento de dos formas posibles:
1. **Movimiento por imagen (rápido, sin IA de video):** zoom, paneo, rotación
   simulada, parallax 2.5D sobre la foto. Es como el zoompan/DepthFlow actual pero
   pensado para lucir el producto. NO necesita WAN ni GPU pesada. RÁPIDO.
2. **Movimiento por IA de video (lento, con WAN):** generar un clip donde el
   producto se mueve de verdad (gira, la cámara orbita). Más impactante, pero lento.
   Usa las mismas tarjetas que los clips de canal.

Empezamos por el (1) porque es rápido, no necesita ComfyUI, y da resultados ya.
El (2) se suma después si quieres más impacto.

## FLUJO DEL MÓDULO DE PRODUCTOS
```
  Tú subes fotos del producto  →  carpeta de entrada
                │
                ▼
  product_clips.py:
    - toma las fotos
    - les aplica movimiento (zoom/paneo/parallax o IA de video)
    - arma un clip corto con transiciones
    - opcional: texto/precio en pantalla, música, voz corta
                │
                ▼
  Clip de producto listo  →  carpeta de salida
                │
                ▼
  TÚ lo publicas manualmente (NO se sube solo a ningún lado)
```

## ESTRUCTURA DE ARCHIVOS (dentro de nodo_clips/)
```
nodo_clips/
├── productos/
│   ├── product_clips.py          ← motor de clips de producto
│   ├── config_productos.py       ← configuración del módulo de productos
│   ├── entrada/                  ← AQUÍ subes las fotos del producto
│   └── salida/                   ← AQUÍ salen los clips listos
```

## PLAN DE IMPLEMENTACIÓN (por partes, sin romper nada)
### FASE P0 — Base (esto se hace ahora)
- [x] Documentación del módulo.
- [ ] config_productos.py (estilos, duración, transiciones, opciones).
- [ ] product_clips.py base (movimiento por imagen, sin IA de video).

### FASE P1 — Clip por movimiento de imagen (rápido, sin ComfyUI)
- [ ] Tomar 1 foto de producto y generar un clip con zoom/paneo profesional.
- [ ] Probar con varias fotos → clip con transiciones entre ángulos.
- [ ] Opcional: texto en pantalla (nombre, precio), música de fondo.

### FASE P2 — Mejoras de presentación
- [ ] Plantillas de presentación (estilo "review", "unboxing", "oferta").
- [ ] Fondos, marcos, efectos de luz sobre el producto.

### FASE P3 — Movimiento por IA de video (opcional, lento)
- [ ] Integrar WAN para que el producto se mueva de verdad (cuando ComfyUI esté).

## REGLAS
- Va dentro de nodo_clips/productos/ — separado de todo lo demás.
- NO automatiza subida a ninguna plataforma. Tú publicas.
- NO toca el sistema de imágenes ni los clips de canal.
- Empieza por movimiento de imagen (rápido) antes que IA de video (lento).
