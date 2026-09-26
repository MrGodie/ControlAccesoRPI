#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manejo directo de GPIO: inicialización, lectura de botones y PIR,
control de LEDs y limpieza. No contiene lógica de validación.
"""

import time
import RPi.GPIO as GPIO

from config import (
    BOTONES, LEDS, LED_VERDE, LED_ROJO, PIR, BOCINA, SERVO,
    TIEMPO_LED, TIEMPO_INDICADOR, TIEMPO_DEBOUNCE
)

pwm_servo = None  # se inicializa dentro de inicializar()


def inicializar():
    global pwm_servo

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Botones conectados entre GPIO y GND
    for num, gpio in BOTONES.items():
        GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    for num, gpio in LEDS.items():
        GPIO.setup(gpio, GPIO.OUT)
        GPIO.output(gpio, GPIO.LOW)

    GPIO.setup(LED_VERDE, GPIO.OUT)
    GPIO.setup(LED_ROJO, GPIO.OUT)
    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_ROJO, GPIO.LOW)

    GPIO.setup(PIR, GPIO.IN)

    GPIO.setup(BOCINA, GPIO.OUT)
    GPIO.output(BOCINA, GPIO.LOW)

    GPIO.setup(SERVO, GPIO.OUT)
    pwm_servo = GPIO.PWM(SERVO, 50)  # 50Hz típico para servos
    pwm_servo.start(0)

    print("Sistema inicializado correctamente")


def encender_led(numero_led, duracion=TIEMPO_LED):
    GPIO.output(LEDS[numero_led], GPIO.HIGH)
    time.sleep(duracion)
    GPIO.output(LEDS[numero_led], GPIO.LOW)


def indicar_exito():
    print("CORRECTO - Acceso concedido")
    GPIO.output(LED_VERDE, GPIO.HIGH)
    time.sleep(TIEMPO_INDICADOR)
    GPIO.output(LED_VERDE, GPIO.LOW)


def indicar_error():
    print("ERROR - Acceso denegado")
    GPIO.output(LED_ROJO, GPIO.HIGH)
    time.sleep(TIEMPO_INDICADOR)
    GPIO.output(LED_ROJO, GPIO.LOW)


def indicar_error_sistema():
    """
    Distinto de indicar_error(): usa un patrón de parpadeo para
    que sea visualmente diferenciable de un rechazo normal (NFR-04).
    """
    print("ERROR DEL SISTEMA - No se pudo validar")
    for _ in range(3):
        GPIO.output(LED_ROJO, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(LED_ROJO, GPIO.LOW)
        time.sleep(0.2)


def esperar_presencia(timeout=None):
    """
    Espera hasta detectar movimiento en el PIR.
    Si se define timeout (segundos), retorna False si no detecta nada.
    """
    print("Esperando presencia...")
    inicio = time.time()

    while GPIO.input(PIR) == GPIO.LOW:
        if timeout and (time.time() - inicio) > timeout:
            return False
        time.sleep(0.1)

    print("Presencia detectada")
    return True


def esperar_botones(longitud_esperada):
    secuencia = []
    print("Esperando botones...")

    while len(secuencia) < longitud_esperada:
        for num, gpio in BOTONES.items():
            # Con PUD_UP, botón presionado = LOW
            if GPIO.input(gpio) == GPIO.LOW:
                secuencia.append(num)
                print(f"Botón {num} presionado")
                print("Secuencia actual:", secuencia)

                encender_led(num)

                # Esperar a que se libere
                while GPIO.input(gpio) == GPIO.LOW:
                    time.sleep(0.01)

                time.sleep(TIEMPO_DEBOUNCE)
                break

        time.sleep(0.01)

    return secuencia


def limpiar():
    print("\nLimpiando GPIO...")
    if pwm_servo:
        pwm_servo.stop()
    GPIO.cleanup()
    print("Programa terminado")