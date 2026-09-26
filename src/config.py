#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración centralizada del sistema.
Modificar aquí no requiere tocar la lógica de GPIO ni de validación.
"""
BOCINA = 27
SERVO = 26

BOTONES = {
    1: 4,
    2: 5,
    3: 6,
}

LEDS = {
    1: 18,
    2: 19,
    3: 20,
}

LED_VERDE = 12
LED_ROJO = 13

# Nuevos dispositivos v2
PIR = 16
BOCINA = 27
SERVO = 26

CONTRASEÑA = [1, 3, 2]

TIEMPO_LED = 0.5
TIEMPO_INDICADOR = 2
TIEMPO_DEBOUNCE = 0.2