#!/bin/bash
set -e

echo ""
echo "==========================================="
echo "   === Music Cloud - Compilador Android ==="
echo "==========================================="
echo ""

# -----------------------------
# CONFIG
# -----------------------------
VENV=~/buildozer-env
PROJECT="$1"

if [ -z "$PROJECT" ]; then
    echo "Uso:"
    echo "./compile_android.sh /ruta/al/proyecto"
    exit 1
fi

# -----------------------------
# [1/5] DEPENDENCIAS DEL SISTEMA
# -----------------------------
echo "-------------------------------------------"
echo " [1/5] Instalando dependencias sistema"
echo "-------------------------------------------"

sudo apt update

sudo apt install -y \
openjdk-17-jdk \
unzip zip \
libffi-dev libssl-dev \
build-essential \
ccache \
autoconf automake libtool pkg-config \
python3 python3-venv python3-dev \
git

echo " Dependencias listas."

# -----------------------------
# [2/5] ENTORNO VIRTUAL
# -----------------------------
echo ""
echo "-------------------------------------------"
echo " [2/5] Preparando entorno virtual"
echo "-------------------------------------------"

if [ ! -d "$VENV" ]; then
    echo " Creando entorno virtual en $VENV ..."
    python3 -m venv $VENV
else
    echo " Entorno virtual ya existe."
fi

source $VENV/bin/activate

echo " Instalando herramientas Python compatibles..."

pip install --upgrade pip setuptools wheel
pip install "cython==0.29.37"
pip install "buildozer==1.5.0"

# -----------------------------
# [3/5] BUILD SPEC AUTOMATICO
# -----------------------------
echo ""
echo "-------------------------------------------"
echo " [3/5] Generando buildozer.spec"
echo "-------------------------------------------"

cd "$PROJECT"

cat > buildozer.spec << 'SPEC'
[app]
title = Music Cloud
package.name = musiccloud
package.domain = org.tfg.musiccloud

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1

requirements = python3,kivy==2.3.0,requests

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

android.api = 33
android.minapi = 21

# IMPORTANTE para BlueStacks
android.archs = armeabi-v7a

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
SPEC

echo " buildozer.spec creado."

# -----------------------------
# [4/5] LIMPIEZA PREVIA
# -----------------------------
echo ""
echo "-------------------------------------------"
echo " [4/5] Limpiando builds antiguos"
echo "-------------------------------------------"

rm -rf .buildozer
rm -rf bin

# -----------------------------
# [5/5] COMPILACION APK
# -----------------------------
echo ""
echo "-------------------------------------------"
echo " [5/5] Compilando APK (20-40 min primera vez)"
echo "-------------------------------------------"

buildozer android debug

echo ""
echo "-------------------------------------------"
echo " APK generado:"
echo "-------------------------------------------"

APK=$(ls bin/*.apk 2>/dev/null | head -1)

if [ -n "$APK" ]; then
    echo ""
    echo " APK listo:"
    echo " $APK"
    echo ""
else
    echo " No se encontró el APK."
    exit 1
fi