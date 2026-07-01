@echo off
REM Avvio "un clic" del Consulente Legale: esegue install.ps1 aggirando la policy di
REM esecuzione degli script, cosi' l'utente non tecnico deve solo fare doppio clic.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
echo Premi un tasto per chiudere questa finestra.
pause >nul
