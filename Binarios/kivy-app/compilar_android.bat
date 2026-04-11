@echo off
title Music Cloud - Compilador Android

echo.
echo === Music Cloud - Compilador Android ===
echo.

:: Verificar WSL
wsl --status >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] WSL no esta instalado o no esta activo.
    echo Ejecuta en PowerShell como administrador: wsl --install
    pause
    exit /b 1
)

:: Obtener ruta del proyecto
set "WIN_PATH=%~dp0"
if "%WIN_PATH:~-1%"=="\" set "WIN_PATH=%WIN_PATH:~0,-1%"

:: Convertir rutas a formato WSL
for /f "delims=" %%i in ('wsl wslpath -u "%WIN_PATH%"') do set "WSL_PATH=%%i"
for /f "delims=" %%i in ('wsl wslpath -u "%WIN_PATH%\compilar.sh"') do set "WSL_SH=%%i"

echo Proyecto Windows : %WIN_PATH%
echo Proyecto WSL     : %WSL_PATH%
echo.
echo Iniciando compilacion (primera vez: 20-40 min)...
echo.

:: Ejecutar script bash en WSL
wsl bash "%WSL_SH%" "%WSL_PATH%"

if %errorlevel% equ 0 (
    echo.
    echo === Compilacion completada correctamente ===
    echo APK disponible en la carpeta bin\
    echo.
    if exist "%WIN_PATH%\bin\" explorer "%WIN_PATH%\bin"
) else (
    echo.
    echo [ERROR] La compilacion ha fallado.
    echo Revisa los mensajes de error arriba.
    echo.
)

pause
