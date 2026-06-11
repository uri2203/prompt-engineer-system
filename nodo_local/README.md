# Nodo Local — Respaldo de archivos (Sistema Pinpinela)

Estos archivos NO corren en Render. Corren en las máquinas locales del nodo.
Este directorio es solo **respaldo/versionado**. La operación real usa las copias en cada PC.

## Mapa de archivos

| Archivo | Máquina | IP | Descripción |
|---|---|---|---|
| `worker_cpu.py` (en raíz del repo) | Xeon | 192.168.0.64 | Worker principal: polling, generación, ensamblaje |
| `pexels_engine.py` | Xeon | 192.168.0.64 | Motor de búsqueda de clips Pexels con filtro de relevancia |
| `voice_local.py` | Xeon | 192.168.0.64 | Cliente de voz (parte texto en chunks, llama al motor de voz) |
| `keep_alive.py` | Xeon | 192.168.0.64 | Mantiene Render despierto (ping cada 10 min) |
| `motor_voz.py` | PC GPU | 192.168.0.251 | Servidor de voz (Kokoro/Edge/F5 + RVC/Applio), puerto 8000 |
| `depthflow_server.py` | PC GPU | 192.168.0.215 | Servidor de parallax 2.5D (DepthFlow), puerto 8500 |
| `iniciar_depthflow.bat` | PC GPU | 192.168.0.215 | Arranque automático del servidor DepthFlow |

## Notas
- El worker en el Xeon trabaja de forma LOCAL (no hace git pull). Para actualizarlo, copiar manualmente.
- DepthFlow corre en entorno aislado `D:\DepthFlow_env` (Python 3.10).
- El motor de voz usa Applio en `C:\Applio` para RVC.
- FiltradoMX usa F5-TTS; los demás canales Kokoro o Edge TTS + RVC.
