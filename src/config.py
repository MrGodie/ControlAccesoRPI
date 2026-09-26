#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración centralizada del sistema.
Modificar aquí no requiere tocar la lógica de GPIO ni de validación.
"""

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