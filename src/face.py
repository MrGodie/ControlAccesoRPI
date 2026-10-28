#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconocimiento facial local con DeepFace.

Responsabilidad: convertir un fotograma en un embedding y compararlo
contra las plantillas guardadas en la base de datos. No abre la cámara
(eso es camera.py) ni decide permisos (eso es validator.py).

Todo corre en el equipo local: DeepFace descarga los pesos del modelo la
primera vez y a partir de ahí no sale a la red (NFR-07). Nunca se guarda
una imagen: solo el embedding (NFR-08).
"""

import threading

import numpy as np

import db
from config import (
    RECONOCIMIENTO_MODELO,
    RECONOCIMIENTO_DETECTOR,
    RECONOCIMIENTO_UMBRAL,
    RECONOCIMIENTO_INTENTOS,
)

# DeepFace es opcional: sin la librería el sistema sigue funcionando por
# botones, igual que hace camera.py con OpenCV.
try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None


# Motivos que puede devolver identificar()
SIN_ROSTRO = "sin_rostro"
DESCONOCIDO = "desconocido"
NO_DISPONIBLE = "no_disponible"
ERROR_BD = "error_bd"

_lock = threading.RLock()
_plantillas = None   # [(usuario_id, vector np.float32)]


def disponible():
    """True si DeepFace está instalado y se puede reconocer."""
    return DeepFace is not None


# --------------------------- serialización -----------------------------

def serializar(vector):
    """Convierte un embedding a bytes para guardarlo en la columna BLOB."""
    return np.asarray(vector, dtype=np.float32).tobytes()


def deserializar(blob):
    """Reconstruye el embedding guardado en la base de datos."""
    return np.frombuffer(blob, dtype=np.float32)


# ---------------------------- plantillas -------------------------------

def cargar_plantillas(forzar=False):
    """
    Lee las plantillas de la base de datos y las deja en memoria.
    Devuelve el número cargado, o None si la base de datos falló.
    """
    global _plantillas
    with _lock:
        if _plantillas is not None and not forzar:
            return len(_plantillas)

        filas = db.obtener_biometria()
        if filas == "ERROR_CONEXION":
            return None

        cargadas = []
        for fila in filas:
            # Solo se comparan plantillas del mismo modelo: los embeddings
            # de modelos distintos no son comparables entre sí.
            if fila.get("modelo") != RECONOCIMIENTO_MODELO:
                continue
            try:
                cargadas.append((fila["usuario_id"], deserializar(fila["embedding"])))
            except (ValueError, TypeError) as error:
                print(f"Plantilla {fila.get('id')} ilegible, se omite:", error)

        _plantillas = cargadas
        return len(_plantillas)


def invalidar_plantillas():
    """Olvida las plantillas en memoria; se recargan en el siguiente uso."""
    global _plantillas
    with _lock:
        _plantillas = None


# ---------------------------- embeddings -------------------------------

def obtener_embedding(fotograma):
    """
    Devuelve el embedding del rostro en el fotograma, o None si DeepFace
    no detectó ninguno. Recibe un arreglo BGR como los que entrega
    camera.capturar_muestra_valida().
    """
    if DeepFace is None:
        return None

    try:
        representaciones = DeepFace.represent(
            img_path=fotograma,
            model_name=RECONOCIMIENTO_MODELO,
            detector_backend=RECONOCIMIENTO_DETECTOR,
            enforce_detection=True,
            align=True,
        )
    except ValueError:
        # DeepFace lanza ValueError cuando no encuentra un rostro.
        return None
    except Exception as error:
        print("Error al calcular el embedding:", error)
        return None

    if not representaciones:
        return None
    return np.asarray(representaciones[0]["embedding"], dtype=np.float32)


def _distancia_coseno(a, b):
    norma = np.linalg.norm(a) * np.linalg.norm(b)
    if norma == 0:
        return 1.0
    return float(1.0 - np.dot(a, b) / norma)


# -------------------------- identificación -----------------------------

def comparar(embedding):
    """
    Compara un embedding contra las plantillas cargadas.
    Devuelve (usuario_id, distancia) o (None, distancia_mas_cercana).
    """
    with _lock:
        plantillas = _plantillas or []

    mejor_id = None
    mejor_distancia = None

    for usuario_id, plantilla in plantillas:
        if plantilla.shape != embedding.shape:
            continue
        distancia = _distancia_coseno(embedding, plantilla)
        if mejor_distancia is None or distancia < mejor_distancia:
            mejor_distancia = distancia
            mejor_id = usuario_id

    if mejor_distancia is None or mejor_distancia > RECONOCIMIENTO_UMBRAL:
        return None, mejor_distancia
    return mejor_id, mejor_distancia


def identificar(capturar, intentos=None):
    """
    Intenta identificar a la persona frente a la cámara.

    `capturar` es una función sin argumentos que devuelve
    (fotograma, motivo), tal como camera.capturar_muestra_valida.

    Devuelve (usuario_id, distancia, motivo):
      - (id, distancia, None)        rostro reconocido
      - (None, distancia, DESCONOCIDO)  hay rostro pero no coincide
      - (None, None, SIN_ROSTRO)     no se detectó rostro en ningún intento
      - (None, None, NO_DISPONIBLE)  DeepFace no está instalado
      - (None, None, ERROR_BD)       no se pudieron leer las plantillas
    """
    if DeepFace is None:
        return None, None, NO_DISPONIBLE

    if cargar_plantillas() is None:
        return None, None, ERROR_BD

    intentos = intentos or RECONOCIMIENTO_INTENTOS
    mejor_distancia = None
    hubo_rostro = False

    for _ in range(intentos):
        fotograma, _motivo = capturar()
        if fotograma is None:
            continue

        embedding = obtener_embedding(fotograma)
        if embedding is None:
            continue

        hubo_rostro = True
        usuario_id, distancia = comparar(embedding)
        if usuario_id is not None:
            return usuario_id, distancia, None
        if distancia is not None and (mejor_distancia is None or distancia < mejor_distancia):
            mejor_distancia = distancia

    if not hubo_rostro:
        return None, None, SIN_ROSTRO
    return None, mejor_distancia, DESCONOCIDO


# -------------------------------- prueba --------------------------------

def _probar():
    """Prueba manual: abre la cámara e intenta identificar una vez."""
    import camera

    if not disponible():
        print("DeepFace no está instalado.")
        return 1

    cargadas = cargar_plantillas(forzar=True)
    if cargadas is None:
        print("No se pudieron leer las plantillas de la base de datos.")
        return 1
    print(f"Plantillas cargadas: {cargadas} (modelo {RECONOCIMIENTO_MODELO})")

    try:
        with camera.sesion_camara():
            usuario_id, distancia, motivo = identificar(camera.capturar_muestra_valida)
    except camera.CamaraError as error:
        print("Error de cámara:", error)
        return 1

    if usuario_id is not None:
        print(f"Reconocido: usuario {usuario_id} (distancia {distancia:.4f})")
    else:
        extra = f" (distancia más cercana {distancia:.4f})" if distancia else ""
        print(f"No reconocido: {motivo}{extra}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_probar())
    