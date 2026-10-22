#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camera acquisition for the facial recognition subsystem.

Responsibilities: open the camera, capture frames, validate image quality
and always release the camera afterwards. It does not detect or recognize
faces. Frames are BGR numpy arrays (the format used by OpenCV and DeepFace).

"""

import argparse
import sys
import threading
from contextlib import contextmanager

try:
    import cv2
    import numpy as np  # noqa: F401  (frames are numpy arrays)
except ImportError:  # the rest of the system must keep working without OpenCV
    cv2 = None

from config import (
    CAMARA_BACKEND,
    CAMARA_FUENTE,
    CAMARA_ANCHO,
    CAMARA_ALTO,
    CAMARA_FOTOGRAMAS_CALENTAMIENTO,
    CAMARA_TIMEOUT_APERTURA,
    CAMARA_INTENTOS_CAPTURA,
    CALIDAD_BRILLO_MIN,
    CALIDAD_BRILLO_MAX,
    CALIDAD_NITIDEZ_MIN,
)


class CamaraError(Exception):
    """The camera could not be opened or read."""


# ------------------------------- backends ---------------------------------

class _OpenCVBackend:
    """USB webcam, or a video file when CAMARA_FUENTE is a path (tests)."""

    def __init__(self):
        self._cap = None

    def abrir(self):
        cap = cv2.VideoCapture(CAMARA_FUENTE)
        if not cap.isOpened():
            cap.release()
            raise CamaraError(f"Camera source {CAMARA_FUENTE!r} could not be opened")
        if isinstance(CAMARA_FUENTE, int):
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMARA_ANCHO)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMARA_ALTO)
        self._cap = cap

    def leer(self):
        ok, fotograma = self._cap.read()
        return fotograma if ok else None

    def cerrar(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class _Picamera2Backend:
    """Raspberry Pi camera module (ribbon connector) through picamera2."""

    def __init__(self):
        self._cam = None

    def abrir(self):
        try:
            from picamera2 import Picamera2
        except ImportError as error:
            raise CamaraError("picamera2 is not installed") from error
        cam = Picamera2()
        try:
            # "RGB888" in picamera2 yields BGR-ordered arrays, as OpenCV expects
            cam.configure(cam.create_video_configuration(
                main={"size": (CAMARA_ANCHO, CAMARA_ALTO), "format": "RGB888"}
            ))
            cam.start()
        except Exception as error:
            cam.close()
            raise CamaraError(f"Pi camera could not be started: {error}") from error
        self._cam = cam

    def leer(self):
        return self._cam.capture_array()

    def cerrar(self):
        if self._cam is not None:
            try:
                self._cam.stop()
            finally:
                self._cam.close()
                self._cam = None


def _crear_backend():
    if CAMARA_BACKEND == "opencv":
        return _OpenCVBackend()
    if CAMARA_BACKEND == "picamera2":
        return _Picamera2Backend()
    raise CamaraError(f"Unknown CAMARA_BACKEND: {CAMARA_BACKEND!r}")


# ------------------------------ camera state ------------------------------

_lock = threading.RLock()
_backend = None


def _abrir_con_limite(backend):
    """Open the backend, giving up after CAMARA_TIMEOUT_APERTURA seconds."""
    resultado = {}
    abandonado = threading.Event()

    def tarea():
        try:
            backend.abrir()
        except Exception as error:
            resultado["error"] = error
            return
        if abandonado.is_set():  # opened too late: nobody will use it
            backend.cerrar()

    hilo = threading.Thread(target=tarea, daemon=True)
    hilo.start()
    hilo.join(CAMARA_TIMEOUT_APERTURA)

    if hilo.is_alive():
        abandonado.set()
        raise CamaraError(f"Camera did not open within {CAMARA_TIMEOUT_APERTURA} s")
    if "error" in resultado:
        error = resultado["error"]
        raise error if isinstance(error, CamaraError) else CamaraError(str(error))


def camara_abierta():
    with _lock:
        return _backend is not None


def abrir_camara():
    """Open the camera and discard the warm-up frames. Safe to call twice."""
    global _backend
    with _lock:
        if _backend is not None:
            return
        if cv2 is None:
            raise CamaraError("OpenCV is not installed")

        backend = _crear_backend()
        _abrir_con_limite(backend)
        _backend = backend

        try:
            for _ in range(CAMARA_FOTOGRAMAS_CALENTAMIENTO):
                backend.leer()
        except Exception as error:
            liberar_camara()
            raise CamaraError(f"Camera failed during warm-up: {error}") from error


def liberar_camara():
    """Release the camera. Safe to call at any time, never raises."""
    global _backend
    with _lock:
        backend, _backend = _backend, None
        if backend is None:
            return
        try:
            backend.cerrar()
        except Exception as error:
            print("Error al liberar la cámara:", error)


@contextmanager
def sesion_camara():
    """Open the camera for one attempt and always release it afterwards."""
    abrir_camara()
    try:
        yield
    finally:
        liberar_camara()


# ------------------------------ frame capture -----------------------------

def capturar_fotograma():
    """Return one BGR frame, or None if the camera gave no image."""
    with _lock:
        if _backend is None:
            raise CamaraError("Camera is not open")
        try:
            return _backend.leer()
        except Exception as error:
            raise CamaraError(f"Camera read failed: {error}") from error


def validar_calidad(fotograma):
    """
    Check that a frame is usable. Returns (valid, reason, metrics) where
    reason is None or one of: "sin_imagen", "muy_oscura", "muy_brillante",
    "borrosa". It does not look for faces.
    """
    if fotograma is None or getattr(fotograma, "size", 0) == 0:
        return False, "sin_imagen", {}

    gris = cv2.cvtColor(fotograma, cv2.COLOR_BGR2GRAY) if fotograma.ndim == 3 else fotograma
    brillo = float(gris.mean())
    nitidez = float(cv2.Laplacian(gris, cv2.CV_64F).var())
    metricas = {"brillo": round(brillo, 1), "nitidez": round(nitidez, 1)}

    if brillo < CALIDAD_BRILLO_MIN:
        return False, "muy_oscura", metricas
    if brillo > CALIDAD_BRILLO_MAX:
        return False, "muy_brillante", metricas
    if nitidez < CALIDAD_NITIDEZ_MIN:
        return False, "borrosa", metricas
    return True, None, metricas


def capturar_muestra_valida(intentos=None):
    """
    Capture frames until one passes the quality check.
    Returns (frame, None) or (None, reason_of_the_last_rejected_frame).
    """
    intentos = intentos or CAMARA_INTENTOS_CAPTURA
    ultimo_motivo = "sin_imagen"
    for _ in range(intentos):
        fotograma = capturar_fotograma()
        valida, motivo, _ = validar_calidad(fotograma)
        if valida:
            return fotograma, None
        ultimo_motivo = motivo
    return None, ultimo_motivo


def verificar_camara():
    """Open, capture one valid frame and release. Returns (ok, message)."""
    try:
        with sesion_camara():
            fotograma, motivo = capturar_muestra_valida()
    except CamaraError as error:
        return False, str(error)
    if fotograma is None:
        return False, f"Camera opened but no valid frame was captured ({motivo})"
    alto, ancho = fotograma.shape[:2]
    return True, f"Camera OK ({ancho}x{alto})"


# -------------------------------- self-test --------------------------------

def _probar():
    parser = argparse.ArgumentParser(description="Camera self-test")
    parser.add_argument("--fotogramas", type=int, default=5, help="frames to check")
    parser.add_argument("--guardar", metavar="ARCHIVO", help="save the last frame (jpg/png)")
    args = parser.parse_args()

    try:
        with sesion_camara():
            print("Camera opened.")
            ultimo = None
            for numero in range(1, args.fotogramas + 1):
                fotograma = capturar_fotograma()
                valida, motivo, metricas = validar_calidad(fotograma)
                print(f"frame {numero}: {'OK' if valida else 'REJECTED (' + motivo + ')'} {metricas}")
                if fotograma is not None:
                    ultimo = fotograma
            if args.guardar and ultimo is not None:
                cv2.imwrite(args.guardar, ultimo)
                print("Last frame saved to", args.guardar)
    except CamaraError as error:
        print("Camera error:", error)
        return 1

    print("Camera released:", not camara_abierta())
    return 0


if __name__ == "__main__":
    sys.exit(_probar())