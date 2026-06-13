@echo off
REM ═══════════════════════════════════════════════════════════════
REM  ARRANQUE AUTOMÁTICO — Sistema Pinpinela (Xeon)
REM  Se ejecuta solo al encender el equipo (carpeta Startup de Windows)
REM  Levanta: Worker + KeepAlive + Orquestador de Lote
REM ═══════════════════════════════════════════════════════════════

cd /d C:\NODO_PINPINELA

REM Esperar 30s a que la red y los otros equipos (GPU, Voz) estén listos
timeout /t 30 /nobreak

REM 1. WORKER — genera los videos. Su salida se guarda en worker_log.txt
REM    (el keep_alive lee ese log para el diagnóstico remoto)
start "WORKER PINPINELA" cmd /k "python worker_cpu.py > worker_log.txt 2>&1"

REM Esperar 5s antes de lanzar los demás
timeout /t 5 /nobreak

REM 2. KEEP-ALIVE — monitor de nodos + cronjob + diagnóstico
start "KEEP-ALIVE" cmd /k "python keep_alive.py"

REM 3. ORQUESTADOR DE LOTE — motor de producción industrial
start "ORQUESTADOR" cmd /k "python orquestador_lote.py"

echo.
echo ════════════════════════════════════════════
echo  SISTEMA PINPINELA INICIADO
echo  - Worker (genera videos, log en worker_log.txt)
echo  - Keep-Alive (nodos + cronjob + diagnostico)
echo  - Orquestador (produccion por lotes)
echo ════════════════════════════════════════════
echo.
echo Esta ventana se puede cerrar. Los 3 procesos siguen corriendo.
timeout /t 10
