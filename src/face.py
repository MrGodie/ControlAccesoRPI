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
import time

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

# Segundos que se espera a que aparezca un rostro frente a la cámara. El PIR
# se activa cuando la persona aún camina hacia el equipo: sin esta espera, el
# primer fotograma casi nunca tiene rostro y siempre se caería a código y clave.
ESPERA_ROSTRO = 10

_lock = threading.RLock()
_plantillas = None   # [(usuario_id, vector np.float32)]
_modelo_ok = None    # None = aún no probado, True = cargado, False = falló


def disponible():
    """True si DeepFace está instalado y el modelo se pudo cargar."""
    return DeepFace is not None and _modelo_ok is not False


def precargar():
    """
    Carga el modelo y el detector ahora, para que el primer reconocimiento
    real no tarde (y para descubrir pronto si faltan los pesos del modelo).
    Devuelve (ok, mensaje); nunca lanza.
    """
    global _modelo_ok
    if DeepFace is None:
        _modelo_ok = False
        return False, "DeepFace no está instalado"
    try:
        en_blanco = np.zeros((224, 224, 3), dtype=np.uint8)
        DeepFace.represent(
            img_path=en_blanco,
            model_name=RECONOCIMIENTO_MODELO,
            detector_backend=RECONOCIMIENTO_DETECTOR,
            enforce_detection=False,
        )
    except Exception as error:
        _modelo_ok = False
        return False, f"No se pudo cargar el modelo {RECONOCIMIENTO_MODELO}: {error}"
    _modelo_ok = True
    return True, f"Modelo {RECONOCIMIENTO_MODELO} listo"


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

    # Con varios rostros en cuadro se usa el más grande (el más cercano a la
    # cámara), no el primero que devuelva el detector.
    principal = max(
        representaciones,
        key=lambda r: r["facial_area"]["w"] * r["facial_area"]["h"],
    )
    return np.asarray(principal["embedding"], dtype=np.float32)


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


def identificar(capturar, intentos=None, espera=None):
    """
    Intenta identificar a la persona frente a la cámara.

    `capturar` es una función sin argumentos que devuelve
    (fotograma, motivo), tal como camera.capturar_muestra_valida.
    Espera hasta `espera` segundos (ESPERA_ROSTRO por omisión) a que haya
    un rostro, y compara hasta `intentos` rostros antes de declararlo
    desconocido.

    Devuelve (usuario_id, distancia, motivo):
      - (id, distancia, None)        rostro reconocido
      - (None, distancia, DESCONOCIDO)  hay rostro pero no coincide
      - (None, None, SIN_ROSTRO)     no apareció ningún rostro a tiempo
      - (None, None, NO_DISPONIBLE)  DeepFace no está instalado
      - (None, None, ERROR_BD)       no se pudieron leer las plantillas
    """
    if DeepFace is None:
        return None, None, NO_DISPONIBLE

    if cargar_plantillas() is None:
        return None, None, ERROR_BD

    intentos = intentos or RECONOCIMIENTO_INTENTOS
    espera = ESPERA_ROSTRO if espera is None else espera
    limite = time.monotonic() + espera
    mejor_distancia = None
    comparaciones = 0

    while comparaciones < intentos and time.monotonic() < limite:
        fotograma, _motivo = capturar()
        if fotograma is None:
            time.sleep(0.1)
            continue

        embedding = obtener_embedding(fotograma)
        if embedding is None:
            continue

        comparaciones += 1
        usuario_id, distancia = comparar(embedding)
        if usuario_id is not None:
            return usuario_id, distancia, None
        if distancia is not None and (mejor_distancia is None or distancia < mejor_distancia):
            mejor_distancia = distancia

    if comparaciones == 0:
        return None, None, SIN_ROSTRO
    return None, mejor_distancia, DESCONOCIDO


# -------------------------------- prueba --------------------------------

def _probar():
    """Prueba manual: abre la cámara e intenta identificar una vez."""
    import camera

    if DeepFace is None:
        print("DeepFace no está instalado.")
        return 1

    print("Cargando el modelo (la primera vez descarga los pesos)...")
    ok, mensaje = precargar()
    print(mensaje)
    if not ok:
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
    