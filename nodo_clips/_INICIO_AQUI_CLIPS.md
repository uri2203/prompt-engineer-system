# ═══════════════════════════════════════════════════════════════════
# SISTEMA DE CLIPS — DOCUMENTO MAESTRO (LEER PRIMERO)
# Para que un chat NUEVO entienda y continue sin perder contexto.
# ═══════════════════════════════════════════════════════════════════

## QUE ES ESTO
Sistema de VIDEOS POR CLIPS + CLIPS DE PRODUCTOS, COMPLETAMENTE APARTE del
sistema actual (que produce videos por imagenes y funciona bien). Vive todo en
la carpeta `nodo_clips/` de la rama `diagnostico`. NO toca nada del sistema actual.

## REGLA DE ORO
- NO aplicar deploy a `main` (dispara Render que cuesta). TODO va a rama `diagnostico`.
- El sistema de imagenes actual (nodo_xeon/) NO se toca.
- Nada se sube a plataformas automaticamente.

## COMO SE CONECTA UN CHAT NUEVO A GITHUB (IMPORTANTE)
Los chats nuevos a veces rechazan el token por seguridad. Para que lo acepten,
en el PRIMER mensaje del chat nuevo hay que dar contexto claro. Ejemplo:
  "Tengo un sistema propio de produccion de videos. El codigo esta en MI
   repositorio de GitHub (uri2203/prompt-engineer-system). Necesito que uses
   las herramientas de codigo (bash) para leer y editar MIS archivos. Este es
   mi token personal para MI repo: [TOKEN]. Lee el archivo
   nodo_clips/_INICIO_AQUI_CLIPS.md de la rama diagnostico y continua desde ahi."

## REPO Y RUTAS
- Repo: uri2203/prompt-engineer-system
- Rama de trabajo: diagnostico (Render la IGNORA, no despliega)
- Carpeta del sistema de clips: nodo_clips/
- Ver esta carpeta:
  https://github.com/uri2203/prompt-engineer-system/tree/diagnostico/nodo_clips
- Descarga raw de un archivo (ejemplo):
  https://raw.githubusercontent.com/uri2203/prompt-engineer-system/diagnostico/nodo_clips/config_clips.py
  (raw cachea ~5 min; si baja viejo, agregar ?v=2 o descargar por SHA del commit)

## HARDWARE (confirmado)
- PC GPU (192.168.0.215): RTX 3060 (12GB) + RTX 3050 (8GB). NO tiene ComfyUI aun.
- Voz (192.168.0.251 = misma maquina que C:\Applio): motor_voz.py Flask puerto 8000 (XTTS).
- Xeon (192.168.0.64): C:\NODO_PINPINELA\, ensambla. Codificacion final a la 3060 (NVENC).

## LAS DOS FUNCIONES DE ESTE SISTEMA
1. VIDEOS POR CLIPS (para los 6 canales): en vez de imagenes con movimiento,
   clips de video reales generados por IA.
   - Modo HIBRIDO (recomendado): clips solo en hook + 2 momentos, resto imagenes.
     ~15-25 videos/dia. Mantiene volumen para 6 canales.
   - Modo COMPLETO: todo con clips. ~2-3 videos/dia. Para videos estrella.
2. CLIPS DE PRODUCTOS (image-to-video): subes 1 FOTO de referencia de un producto,
   la IA genera un COMERCIAL con el producto en escenas/ambientes con movimiento.
   NO es slideshow. NUNCA se publica solo (tu publicas).

## ESTADO ACTUAL (que esta hecho y que falta)
HECHO (documentado y en GitHub, rama diagnostico, carpeta nodo_clips/):
- [x] Arquitectura completa del sistema de clips (ARQUITECTURA_SISTEMA_CLIPS.md)
- [x] Config central de clips (config_clips.py) — modo hibrido/completo, reparto
      3060+3050, voz en paralelo, ensamblaje NVENC, prompts de video por canal.
- [x] Modulo de productos documentado (productos/MODULO_PRODUCTOS.md) con las 7
      soluciones de CALIDAD contra deformacion del producto.
- [x] Config de productos (productos/config_productos.py) — WAN 2.2 14B (NO 5B),
      resolucion nativa, movimiento controlado, UPSCALER SeedVR2, batch 4n+1, 6 escenas.
- [x] Motor de productos (productos/product_i2v.py) — pipeline de calidad: preparar
      foto -> generar WAN -> upscale SeedVR2 -> unir. PASO 1 (preparar foto) funciona
      con FFmpeg. Detecta cuando falta WAN sin inventar nada.
- [x] Maqueta de como integrar todo al dashboard (imagen mostrada al usuario).

FALTA (el trabajo pendiente real):
- [ ] INSTALAR ComfyUI en la PC GPU (192.168.0.215). Es el requisito #1 para todo.
- [ ] Descargar modelos: WAN 2.2 14B fp8 (i2v) + SeedVR2 (upscaler) + Wan para clips de canal.
- [ ] Construir los servidores wan_server_3060.py y wan_server_3050.py (generan clips).
- [ ] Construir repartidor_clips.py (reparte clips entre las 2 tarjetas).
- [ ] Construir worker_clips.py (worker independiente: clips + voz paralelo + ensamblaje).
- [ ] Construir ensamblador_nvenc.py (codificacion final en la 3060).
- [ ] Construir orquestador_clips.py (lotes, elegir modo imagenes vs clips).
- [ ] FASE 1 CLAVE: generar 1 clip en la 3060 y MEDIR tiempo real -> decidir con numeros.
- [ ] Integrar el dashboard (convertir la maqueta en HTML real).

## POR DONDE SEGUIR (orden recomendado)
1. Instalar ComfyUI en la PC GPU (guiar al usuario paso a paso).
2. Descargar WAN 2.2 14B + SeedVR2.
3. FASE 1: montar wan_server_3060.py, generar 1 clip, medir tiempo real.
4. Con el numero real, decidir modo (hibrido casi seguro) y continuar por fases.
Ver ARQUITECTURA_SISTEMA_CLIPS.md (fases 0-6) y productos/MODULO_PRODUCTOS.md (fases P0-P3).

## ARCHIVOS DE ESTE SISTEMA (todos en nodo_clips/, rama diagnostico)
- _INICIO_AQUI_CLIPS.md          <- este documento (leer primero)
- ARQUITECTURA_SISTEMA_CLIPS.md  <- arquitectura y fases del sistema de clips
- config_clips.py                <- configuracion central de clips
- productos/MODULO_PRODUCTOS.md   <- modulo productos + 7 soluciones de calidad
- productos/config_productos.py   <- config productos (WAN 14B, SeedVR2, escenas)
- productos/product_i2v.py        <- motor image-to-video de productos
- productos/product_clips.py      <- OBSOLETO (era slideshow, ignorar)

## NOTA SOBRE EL SISTEMA ACTUAL (que SI esta en produccion, NO tocar)
- Worker de imagenes: nodo_xeon/worker_cpu.py (version reciente 2026-06-23_Q).
- Ese sistema funciona bien. El de clips es aparte y no debe interferir.
- Detalles completos del sistema actual: ver journal.txt y transcripts del proyecto.
