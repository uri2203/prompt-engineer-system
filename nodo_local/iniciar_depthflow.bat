@echo off
REM ═══════════════════════════════════════════════════════════
REM  DEPTHFLOW SERVER — Arranque automatico (Sistema Pinpinela)
REM  Doble clic para iniciar el servidor de parallax en el PC GPU
REM ═══════════════════════════════════════════════════════════

title DepthFlow Server - Pinpinela

echo ============================================
echo   INICIANDO DEPTHFLOW SERVER
echo ============================================
echo.

REM Activar el entorno virtual de DepthFlow
call D:\DepthFlow_env\Scripts\activate.bat

REM Arrancar el servidor (ajusta la ruta si guardaste el .py en otro lado)
python D:\depthflow_server.py

REM Si el servidor se cierra o falla, la ventana no se cierra sola
REM (asi puedes leer el error)
echo.
echo ============================================
echo   El servidor se detuvo. Revisa los mensajes arriba.
echo ============================================
pause
