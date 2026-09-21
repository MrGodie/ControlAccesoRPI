#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time

# =========================
# CONFIGURACIÓN
# =========================

BOTONES = {
    1: 4,
    2: 5,
    3: 6,
    4: 17,
    5: 22
}

LEDS = {
    1: 18,
    2: 19,
    3: 20,
    4: 21,
    5: 24
}

LED_VERDE = 12
LED_ROJO = 13

CONTRASEÑA = [1, 3, 5, 2, 4]

TIEMPO_LED = 0.5
TIEMPO_INDICADOR = 2
TIEMPO_DEBOUNCE = 0.2


# =========================
# INICIALIZACIÓN
# =========================

def inicializar():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Botones conectados entre GPIO y GND
    for num, gpio in BOTONES.items():
        GPIO.setup(
            gpio,
            GPIO.IN,
            pull_up_down=GPIO.PUD_UP
        )

    for num, gpio in LEDS.items():
        GPIO.setup(gpio, GPIO.OUT)
        GPIO.output(gpio, GPIO.LOW)

    GPIO.setup(LED_VERDE, GPIO.OUT)
    GPIO.setup(LED_ROJO, GPIO.OUT)

    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_ROJO, GPIO.LOW)

    print("Sistema inicializado correctamente")
    print("Contraseña actual:", CONTRASEÑA)
    print("Presiona los botones en el orden correcto...")


# =========================
# FUNCIONES
# =========================

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


def esperar_botones():
    secuencia = []

    print("Esperando botones...")

    while len(secuencia) < len(CONTRASEÑA):

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


def verificar_contraseña(secuencia):

    if secuencia == CONTRASEÑA:

        indicar_exito()

        return True

    else:

        print("Esperabas:", CONTRASEÑA)
        print("Presionaste:", secuencia)

        indicar_error()

        return False


def limpiar():

    print("\nLimpiando GPIO...")

    GPIO.cleanup()

    print("Programa terminado")


# =========================
# PROGRAMA PRINCIPAL
# =========================

def main():

    try:

        inicializar()

        while True:

            print("\n" + "=" * 50)
            print("NUEVO INTENTO")
            print("=" * 50)

            secuencia_usuario = esperar_botones()

            verificar_contraseña(secuencia_usuario)

            print("Esperando un nuevo intento...")

            time.sleep(1)

    except KeyboardInterrupt:

        print("\nSaliendo del programa")

    finally:

        limpiar()


if __name__ == "__main__":
    main()