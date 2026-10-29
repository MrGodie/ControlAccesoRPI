#!/bin/bash
# Genera los archivos de audio en sounds/ (requiere sox: sudo apt install sox).
# Los .wav ya vienen en el repositorio; esto solo sirve para regenerarlos.

cd "$(dirname "$0")" || exit 1
mkdir -p sounds

echo "Generando audio de éxito..."
sox -n sounds/exito.wav synth 2 sine 800 sine 1200 gain -3

echo "Generando audio de error..."
sox -n sounds/error.wav synth 2 sine 400 gain -3

echo "Archivos de audio creados"
ls -la sounds/
