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

LONGITUD_CLAVE = 3

TIEMPO_LED = 0.5
TIEMPO_INDICADOR = 2
TIEMPO_DEBOUNCE = 0.2

# --- Interfaz gráfica (wireframes PI2, pantalla de 1280x720) ---
GUI_PANTALLA_COMPLETA = False   # True en la Raspberry Pi para ocupar todo el monitor
GUI_REQUIERE_CLAVE = True       # False = la GUI pide solo el ID (sin clave)
GUI_ID_MAX_DIGITOS = 8
PUNTO_ACCESO = "PUNTO 01"
TEXTO_REPOSO = "Laboratorio Sistema activo"

# --- Tiempos del flujo, en segundos (según los wireframes) ---
TIEMPO_ESPERA_PRESENCIA = 30    # espera del PIR antes de reiniciar el ciclo
TIEMPO_INACTIVIDAD_GUI = 30     # identificación sin actividad -> vuelve a reposo
TIEMPO_ESPERA_BD = 5            # sin respuesta de la BD -> error del sistema
TIEMPO_PANTALLA_AUTORIZADO = 5
TIEMPO_PANTALLA_DENEGADO = 4
TIEMPO_PANTALLA_FALLO = 4