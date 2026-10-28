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

# --- Camera (facial recognition subsystem) ---
# "opencv": USB webcam or video file | "picamera2": Raspberry Pi camera module
CAMARA_BACKEND = "opencv"
CAMARA_FUENTE = 0                    # opencv only: device index (0, 1...) or video file path (for tests)
CAMARA_ANCHO = 640
CAMARA_ALTO = 480
CAMARA_FOTOGRAMAS_CALENTAMIENTO = 5  # frames discarded after opening (auto exposure settles)
CAMARA_TIMEOUT_APERTURA = 5          # seconds before giving up opening the camera
CAMARA_INTENTOS_CAPTURA = 10         # frames tried to obtain one valid sample

# Image quality thresholds (starting values: calibrate with the real camera and lighting)
CALIDAD_BRILLO_MIN = 40              # mean gray level (0-255) below this = too dark
CALIDAD_BRILLO_MAX = 220             # above this = too bright
CALIDAD_NITIDEZ_MIN = 60             # variance of the Laplacian below this = blurry

# --- Reconocimiento facial (DeepFace, local) ---
# Activa o desactiva el intento facial sin tocar el código.
RECONOCIMIENTO_ACTIVO = True

# SFace y GhostFaceNet son los ligeros; VGG-Face (el default de DeepFace)
# es demasiado pesado para la Raspberry.
RECONOCIMIENTO_MODELO = "SFace"

# opencv es el detector más ligero; retinaface y mtcnn son mucho más lentos.
RECONOCIMIENTO_DETECTOR = "opencv"

# Distancia coseno máxima para considerar que dos rostros son la misma
# persona. Más bajo = más estricto. 0.593 es el umbral que DeepFace usa
# para SFace con coseno; calibrar con rostros reales del equipo.
RECONOCIMIENTO_UMBRAL = 0.593

# Fotogramas válidos que se intentan antes de darse por vencido.
RECONOCIMIENTO_INTENTOS = 3

# --- Pantallas del flujo facial ---
TIEMPO_PANTALLA_PREPARANDO = 2    # "Colóquese frente a la cámara"
TIEMPO_PANTALLA_FALLO_CAMARA = 4  # "La cámara no responde"