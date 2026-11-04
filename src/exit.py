#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Respuesta física a un acceso: audio por la bocina USB (Jabra Link 370)
con aplay, y apertura del servo.

Prueba del audio en la Raspberry:  python3 src/exit.py exito|error|fallo
"""
import os
import re
import subprocess
import sys
import time

from config import (
    AUDIO_EXITO, AUDIO_ERROR, AUDIO_FALLO, AUDIO_DEVICE, AUDIO_TARJETA,
)
import gpio_handler

# Lista de tarjetas de sonido del kernel. Cada tarjeta empieza con una
# línea como " 3 [Link370        ]: USB-Audio - Jabra Link 370".
_TARJETAS = "/proc/asound/cards"
_LINEA_TARJETA = re.compile(r"^\s*\d+\s+\[(\S+)\s*\]:")


def _buscar_tarjeta(nombre):
    """
    Devuelve el id ALSA de la primera tarjeta cuyo nombre contiene
    `nombre` (sin importar mayúsculas), o None si no aparece.
    """
    try:
        with open(_TARJETAS, encoding="utf-8", errors="replace") as f:
            lineas = f.read().splitlines()
    except OSError:
        return None
    # Cada tarjeta ocupa dos líneas (encabezado y descripción larga): el
    # nombre puede venir en cualquiera de las dos.
    actual = None
    for linea in lineas:
        coincidencia = _LINEA_TARJETA.match(linea)
        if coincidencia:
            actual = coincidencia.group(1)
        if actual and nombre.lower() in linea.lower():
            return actual
    return None


def dispositivos_audio():
    """
    Dispositivos ALSA que se prueban, en orden: el de AUDIO_DEVICE, o la
    tarjeta encontrada por AUDIO_TARJETA, y al final "default". Se arma
    en cada reproducción porque la bocina puede conectarse después.
    """
    candidatos = []
    if AUDIO_DEVICE:
        candidatos.append(AUDIO_DEVICE)
    else:
        tarjeta = _buscar_tarjeta(AUDIO_TARJETA)
        if tarjeta:
            candidatos.append(f"plughw:CARD={tarjeta},DEV=0")
        else:
            print(f"No se encontró la bocina {AUDIO_TARJETA!r} en {_TARJETAS}; "
                  "se usa la salida de audio por omisión.")
    # "default" pasa por el servidor de sonido del sistema: suena aunque
    # la tarjeta esté ocupada por él o se llame distinto.
    if "default" not in candidatos:
        candidatos.append("default")
    return candidatos


def _reproducir(archivo):
    """
    Reproduce un .wav con aplay. Si falla solo se reporta: el audio
    nunca debe interrumpir el flujo de acceso. Devuelve True si sonó.
    """
    if not os.path.exists(archivo):
        print("Archivo de audio no encontrado:", archivo)
        return False

    for dispositivo in dispositivos_audio():
        try:
            subprocess.run(
                ["aplay", "-q", "-D", dispositivo, archivo],
                check=True,
                timeout=10,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            # El motivo real (tarjeta inexistente, dispositivo ocupado...)
            # viene en stderr; sin él el log no dice nada útil.
            detalle = (e.stderr or "").strip() or f"código de salida {e.returncode}"
            print(f"Error al reproducir el audio en {dispositivo}: {detalle}")
        except subprocess.TimeoutExpired:
            print(f"Error al reproducir el audio en {dispositivo}: aplay no terminó a tiempo")
        except OSError as e:
            # aplay no está instalado: ningún otro dispositivo va a servir.
            print("Error al reproducir el audio:", e)
            return False
    return False


def reproducir_audio_exito():
    return _reproducir(AUDIO_EXITO)


def reproducir_audio_error():
    return _reproducir(AUDIO_ERROR)

def reproducir_audio_fallo():
    return _reproducir(AUDIO_FALLO)

def activar_actuador():
    servo = gpio_handler.pwm_servo

    servo.ChangeDutyCycle(7)    # posición abierta
    time.sleep(2)
    servo.ChangeDutyCycle(2)    # posición cerrada
    time.sleep(0.5)             # dar tiempo a llegar a la posición
    servo.ChangeDutyCycle(0)    # dejar de enviar pulsos: evita vibración


if __name__ == "__main__":
    sonidos = {
        "exito": reproducir_audio_exito,
        "error": reproducir_audio_error,
        "fallo": reproducir_audio_fallo,
    }
    if len(sys.argv) > 1 and sys.argv[1] in sonidos:
        print("Dispositivos a probar:", ", ".join(dispositivos_audio()))
        sono = sonidos[sys.argv[1]]()
        print("Reproducido correctamente." if sono else "No se pudo reproducir el audio.")
        sys.exit(0 if sono else 1)
    print("Uso: python3 src/exit.py exito|error|fallo")
    sys.exit(2)
