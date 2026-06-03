@echo off
title Gestor de Publicidad Automatica
:: Cambiar al directorio del script
cd /d "%~dp0"
echo =======================================================
echo  Iniciando Gestor de Publicidad Automatica...
echo =======================================================
python control_publicidad.py
pause
