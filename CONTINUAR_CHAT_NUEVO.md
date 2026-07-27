# ═══════════════════════════════════════════════════════════════════
# DOCUMENTO MAESTRO — DARK FACTORY / PINPINELA (LEER PRIMERO)
# Para continuar en un CHAT NUEVO sin perder contexto.
# ═══════════════════════════════════════════════════════════════════

## MENSAJE PARA PEGAR EN EL CHAT NUEVO (copia esto tal cual):
"Tengo un sistema propio de produccion automatizada de videos para YouTube.
El codigo esta en MI repositorio de GitHub (uri2203/prompt-engineer-system).
Necesito que uses las herramientas de codigo (bash) para leer y editar MIS
archivos. Este es mi token personal de acceso para MI repo:
[PEGA_AQUI_TU_TOKEN]
Lee el archivo CONTINUAR_CHAT_NUEVO.md de la rama diagnostico y continua desde ahi."

## TOKEN GITHUB ACTUAL (valido)
[PEGA_AQUI_TU_TOKEN]
(El token viejo github_pat_11B5LKAMA0i14... EXPIRO. Este es el nuevo.)
[PENDIENTE] Actualizar este token en la variable de entorno de Render (el sistema
lo usa para escribir diagnosticos en GitHub). Cuando expiro el viejo, Render dejo
de escribir en GitHub.

## REPO Y RAMAS
- Repo: uri2203/prompt-engineer-system
- Rama `main`: la que Render DESPLIEGA. CUALQUIER commit a main dispara deploy (cuesta).
  Solo tocar main con OK explicito. Archivos de main: app.py, modulos/ (ai_engine,
  neuro_engine, trend_engine, compliance_engine), bot_dashboard.html.
- Rama `diagnostico`: Render la IGNORA (NO deploy). Aqui va TODO lo del Xeon:
  nodo_xeon/ (worker, orquestador), nodo_clips/ (sistema de clips), _diagnostico/.

## ARQUITECTURA (maquinas)
- Render (nube): app.py, servidor central. URL:
  https://prompt-engineer-system-l2r6.onrender.com (free tier, se duerme, UTC)
- Xeon (192.168.0.64): C:\NODO_PINPINELA\. Corre worker_cpu.py + orquestador_lote.py.
  Renders en C:\DarkFactory_Renders. Assets en C:\DarkFactory_ASSETS\{carpeta_canal}.
  Cola del lote: C:\NODO_PINPINELA\estado_lote\lote_actual.json
- PC GPU (192.168.0.215): Stable Diffusion (SD, puerto 7861) + DepthFlow (8500).
  RTX 3060 12GB + RTX 3050 8GB. NO tiene ComfyUI.
- Voz (192.168.0.251): motor_voz.py Flask puerto 8000. Motor XTTS.

## CANALES (6)
La Viuda (terror), Monkygraff (geopolitica), FiltradoMX (drama), LaesquinaRandom
(comedia), TuIALista (IA/tech femenina), Umbral Alterno (documental hipotetico).
Carpetas de assets (nombres EXACTOS en C:\DarkFactory_ASSETS\):
  La Viuda, Monkygraff, Filtradomx, Laesquina, Tuialista, UmbralAlterno (SIN espacio)

## VERSIONES ACTUALES (en rama diagnostico)
- worker_cpu.py: VERSION 2026-06-23_R4 (la ultima). Ruta de descarga:
  https://raw.githubusercontent.com/uri2203/prompt-engineer-system/diagnostico/nodo_xeon/worker_cpu.py
  (raw cachea ~5min; usar ?v=R4 si baja viejo. Al arrancar muestra la version en un recuadro.)
- orquestador_lote.py: VERSION 2026-06-30_R2 + fix timeout largos. Ruta:
  https://raw.githubusercontent.com/uri2203/prompt-engineer-system/diagnostico/nodo_xeon/orquestador_lote.py

## ARREGLOS RECIENTES YA APLICADOS (worker R-series y orquestador)
- Anti-video-vacio: worker verifica que el MP4 existe/pesa/dura antes de dar por bueno
  el video; si no, reporta FALLIDO para que el orquestador reintente (no crea carpetas vacias OK).
- Metadatos/datos de publicacion en blanco: el paquete llega como STRING JSON y el worker
  ahora lo convierte a dict antes de generar el Word (antes salia en blanco). Tambien
  ai_engine limpia cercos ```json de Gemini.
- Aperturas iguales: la rotacion dependia del tiempo -> lote del mismo canal daba misma
  apertura. Ahora usa aleatoriedad por video (neuro_engine).
- Pronunciacion: shock->chok (regla sh->ch), Mexico->mejico (X_COMO_J), ~50 paises,
  Israel->Israel. Todo en worker _corregir_pronunciacion. Espanol intacto (explica->eksplica).
- Musica encadenada: usa las 4 pistas de fondo una tras otra (crossfade) a lo largo de
  TODO el video + tension en momentos puntuales (1 en shorts, 2-3 en largos). Stingers ya no.
  Nombres de archivo que busca: musica_fondo1-4.mp3, musica_tension1-2.mp3 (con S).
- Fix carpeta Umbral: buscaba "Umbral Alterno" (con espacio) pero es "UmbralAlterno".
- Fix crash musica: VOLUMEN_MUSICA era string "0.15", hacia *1.6 -> error. Corregido float().
- Ensamblaje ya NO exige SD vivo (las imagenes ya estan en disco; solo necesita voz+FFmpeg).
- Orquestador: banner de version + recupera videos atascados + timeout subido a 3h (los
  largos de Umbral tardan 45+ min y el timeout viejo de 45min los mataba). El timeout ya
  NO relanza el video por tardar (solo avisa y sigue esperando).

## REGLA CRITICA DE ORDEN DE LOTE
El orquestador OBEDECE el plan. Si genera shorts cuando querias largos, es porque el
plan tenia "shorts primero" o shorts>0. Poner orden "largos primero" o shorts en 0.

## METODOLOGIA DE TRABAJO CON CLAUDE
- Claude edita los archivos directamente en GitHub via API con el token.
- Usuario descarga el worker/orquestador al Xeon desde las rutas raw.
- worker/orquestador -> SIEMPRE rama diagnostico (NO deploy).
- app.py/modulos -> rama main SOLO con OK explicito (dispara deploy Render que cuesta).
- Validar SIEMPRE sintaxis (ast.parse) y probar la logica antes de subir.
- Verificar nombres de archivo/carpeta EXACTOS (un espacio rompio Umbral).

## SISTEMA DE CLIPS (aparte, EN PAUSA)
Carpeta nodo_clips/ en rama diagnostico. Documento propio: nodo_clips/_INICIO_AQUI_CLIPS.md
Es un sistema SEPARADO (videos por clips de video IA + clips de productos image-to-video).
NO deploy. Pendiente: instalar ComfyUI en la PC GPU. Ver su documento para detalles.

## PENDIENTES GLOBALES
1. Actualizar el TOKEN nuevo en la variable de entorno de Render (el viejo expiro).
2. Reiniciar Stable Diffusion en 192.168.0.215 si se cae (webui-user.bat). Se satura
   en lotes de 50 escenas. Considerar agregar --no-half-vae para estabilidad.
3. Descargar worker R4 y orquestador nuevo al Xeon. Borrar lote_actual.json viejo si
   quedo con videos "fallidos/omitidos" por el timeout viejo.
4. Poner intro_169.mp4 y outro_169.mp4 de Umbral (opcional; el video sale sin ellos).
5. Revocar el token viejo en GitHub (seguridad).
6. Sistema de clips: instalar ComfyUI, luego medir 1 clip en la 3060.

## NOTAS DE PROCESO
- Las simulaciones NO reproducen bugs reales de produccion. Usar el auto-diagnostico
  real del worker (mide el video terminado con FFmpeg, sube a _diagnostico/videos/).
- Cualquier cambio es REVERSIBLE (historial de GitHub).
- El sistema de imagenes actual FUNCIONA; el de clips es aparte y no debe interferir.
