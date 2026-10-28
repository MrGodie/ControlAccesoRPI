#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validación de credenciales. Ambos flujos (GUI y botones) devuelven
(usuario_o_None, resultado), donde resultado es uno de:
"autorizado", "denegado_sin_permiso",
"denegado_no_reconocido", "error_sistema".
"""

import threading

import db
from config import TIEMPO_ESPERA_BD


def _con_limite_de_tiempo(funcion, *args):
    salida = {}

    def tarea():
        salida["valor"] = funcion(*args)

    hilo = threading.Thread(target=tarea, daemon=True)
    hilo.start()
    hilo.join(TIEMPO_ESPERA_BD)

    if hilo.is_alive() or "valor" not in salida:
        return "ERROR_CONEXION"
    return salida["valor"]


def _clasificar(usuario):
    if usuario == "ERROR_CONEXION":
        return None, "error_sistema"

    if not usuario:
        return None, "denegado_no_reconocido"

    if not usuario["acceso_permitido"]:
        return usuario, "denegado_sin_permiso"

    return usuario, "autorizado"


def verificar_credencial(secuencia):
    """Flujo de botones: la clave identifica al usuario."""
    credencial = "".join(map(str, secuencia))
    usuario = _con_limite_de_tiempo(db.obtener_usuario_por_credencial, credencial)
    return _clasificar(usuario)


def verificar_usuario(usuario_id, secuencia=None):
    credencial = None if secuencia is None else "".join(map(str, secuencia))
    usuario = _con_limite_de_tiempo(db.obtener_usuario_por_id, usuario_id, credencial)
    return _clasificar(usuario)

def verificar_rostro(usuario_id):
    """
    Flujo facial: el rostro ya identificó a la persona, aquí solo se
    consultan su rol y sus permisos. No se revisa credencial, porque la
    identidad la dio la biometría.
    """
    usuario = _con_limite_de_tiempo(db.obtener_usuario_por_id, usuario_id)
    return _clasificar(usuario)