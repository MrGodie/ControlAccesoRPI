#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Respuesta física a un acceso: audio por la bocina USB (Jabra Link 370)
con aplay, y apertura del servo.

Prueba del audio en la Raspberry:  python3 src/exit.py exito|error
"""
import os
import subprocess
import sys
import time

from config import AUDIO_EXITO, AUDIO_ERROR, AUDIO_DEVICE
import gpio_handler


def _reproducir(archivo):
    """
    Reproduce un .wav con aplay. Si falla solo se reporta: el audio
    nunca debe interrumpir el flujo de acceso.
    """
    if not os.path.exists(archivo):
        print("Archivo de audio no encontrado:", archivo)
        return False
    try:
        subprocess.run(
            ["aplay", "-q", "-D", AUDIO_DEVICE, archivo],
            check=True,
            timeout=10,
        )
        return True
    except (OSError, subprocess.SubprocessError) as e:
        print("Error al reproducir el audio:", e)
        return False


def reproducir_audio_exito():
    return _reproducir(AUDIO_EXITO)


def reproducir_audio_error():
    return _reproducir(AUDIO_ERROR)


def activar_actuador():
    servo = gpio_handler.pwm_servo

    servo.ChangeDutyCycle(7)    # posición abierta
    time.sleep(2)
    servo.ChangeDutyCycle(2)    # posición cerrada
    time.sleep(0.5)             # dar tiempo a llegar a la posición
    servo.ChangeDutyCycle(0)    # dejar de enviar pulsos: evita vibración


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "exito":
        reproducir_audio_exito()
    elif len(sys.argv) > 1 and sys.argv[1] == "error":
        reproducir_audio_error()
    else:
        print("Uso: python3 src/exit.py exito|error")
