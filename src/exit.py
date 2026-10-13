#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import RPi.GPIO as GPIO

from config import BOCINA
import gpio_handler


def reproducir_audio_exito():
    GPIO.output(BOCINA, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(BOCINA, GPIO.LOW)


def activar_actuador():
    servo = gpio_handler.pwm_servo

    servo.ChangeDutyCycle(7)    # posición abierta
    time.sleep(2)
    servo.ChangeDutyCycle(2)    # posición cerrada
    time.sleep(0.5)             # dar tiempo a llegar a la posición
    servo.ChangeDutyCycle(0)    # dejar de enviar pulsos: evita vibración