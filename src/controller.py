#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Contraseña con Raspberry Pi
5 Botones + 5 LEDs + Indicadores Verde/Rojo
"""

import RPi.GPIO as GPIO
import time

# ============ CONFIGURACIÓN DE GPIOs ============

# BOTONES (ENTRADA) - 5 BOTONES
BOTONES = {
    1: 4,      # Botón 1 → GPIO 4
    2: 5,      # Botón 2 → GPIO 5
    3: 6,      # Botón 3 → GPIO 6
    4: 17,     # Botón 4 → GPIO 17
    5: 22,     # Botón 5 → GPIO 22
}

# LEDs FEEDBACK (SALIDA) - 5 LEDs
LEDS = {
    1: 18,     # LED 1 → GPIO 18
    2: 19,     # LED 2 → GPIO 19
    3: 20,     # LED 3 → GPIO 20
    4: 21,     # LED 4 → GPIO 21
    5: 24,     # LED 5 → GPIO 24
}

# LEDs INDICADORES (SALIDA)
LED_VERDE = 12    # GPIO 12 (OK)
LED_ROJO = 13     # GPIO 13 (ERROR)

# CONTRASEÑA (edita según quieras)
CONTRASEÑA = [1, 3, 5, 2, 4]  # Ejemplo: presiona botones en este orden

# TIEMPOS
TIEMPO_LED = 0.5       # Cuánto tiempo brilla el LED (segundos)
TIEMPO_INDICADOR = 2   # Cuánto tiempo brilla indicador (segundos)
TIEMPO_DEBOUNCE = 0.2  # Tiempo para evitar rebotes

# ============ INICIALIZACIÓN ============

def inicializar():|
    """Configura los GPIOs"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Configurar BOTONES como entrada con pull-down
    for num, gpio in BOTONES.items():
        GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    # Configurar LEDS como salida
    for num, gpio in LEDS.items():
        GPIO.setup(gpio, GPIO.OUT)
        GPIO.output(gpio, GPIO.LOW)  # Apagar al inicio
    
    # Configurar INDICADORES como salida
    GPIO.setup(LED_VERDE, GPIO.OUT)
    GPIO.setup(LED_ROJO, GPIO.OUT)
    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_ROJO, GPIO.LOW)
    
    print("✓ Sistema inicializado correctamente")
    print(f"✓ Contraseña actual: {CONTRASEÑA}")
    print(f"✓ Presiona los botones en el orden correcto...\n")

# ============ FUNCIONES ============

def encender_led(numero_led, duracion=TIEMPO_LED):
    """Enciende un LED de feedback"""
    GPIO.output(LEDS[numero_led], GPIO.HIGH)
    time.sleep(duracion)
    GPIO.output(LEDS[numero_led], GPIO.LOW)

def indicar_exito():
    """Enciende LED verde (contraseña correcta)"""
    print("✓ ¡CORRECTO! Acceso concedido")
    GPIO.output(LED_VERDE, GPIO.HIGH)
    time.sleep(TIEMPO_INDICADOR)
    GPIO.output(LED_VERDE, GPIO.LOW)

def indicar_error():
    """Enciende LED rojo (contraseña incorrecta)"""
    print("✗ ERROR. Intenta de nuevo")
    GPIO.output(LED_ROJO, GPIO.HIGH)
    time.sleep(TIEMPO_INDICADOR)
    GPIO.output(LED_ROJO, GPIO.LOW)

def esperar_botones():
    """Lee la secuencia de botones del usuario"""
    secuencia = []
    print("Esperando botones...")
    
    while len(secuencia) < len(CONTRASEÑA):
        # Revisar cada botón
        for num, gpio in BOTONES.items():
            if GPIO.input(gpio) == GPIO.HIGH:  # Botón presionado
                secuencia.append(num)
                print(f"  → Botón {num} presionado")
                
                # Encender el LED correspondiente
                encender_led(num)
                
                # Esperar a que se suelte el botón
                time.sleep(TIEMPO_DEBOUNCE)
                while GPIO.input(gpio) == GPIO.HIGH:
                    time.sleep(0.05)
                time.sleep(TIEMPO_DEBOUNCE)
                break
        
        time.sleep(0.05)
    
    return secuencia

def verificar_contraseña(secuencia):
    """Verifica si la secuencia es correcta"""
    if secuencia == CONTRASEÑA:
        indicar_exito()
        return True
    else:
        print(f"Esperabas: {CONTRASEÑA}")
        print(f"Presionaste: {secuencia}")
        indicar_error()
        return False

def limpiar():
    """Limpia los GPIOs"""
    print("\nLimpiando...")
    GPIO.cleanup()
    print("✓ Apagado correctamente")

# ============ LOOP PRINCIPAL ============

def main():
    """Loop principal del programa"""
    try:
        inicializar()
        
        while True:
            print("\n" + "="*50)
            print("NUEVO INTENTO")
            print("="*50)
            
            # Leer botones del usuario
            secuencia_usuario = esperar_botones()
            
            # Verificar contraseña
            verificar_contraseña(secuencia_usuario)
            
            print("\nPresiona Ctrl+C para salir")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n¡Saliendo del programa!")
        limpiar()

# ============ EJECUTAR ============

if __name__ == "__main__":
    main()