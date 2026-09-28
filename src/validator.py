#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import db


def verificar_credencial(secuencia):
    """
    Retorna (usuario_o_None, resultado), donde resultado es uno de:
    "autorizado", "denegado_sin_permiso",
    "denegado_no_reconocido", "error_sistema".
    """
    credencial = "".join(map(str, secuencia))
    usuario = db.obtener_usuario_por_credencial(credencial)

    if usuario == "ERROR_CONEXION":
        return None, "error_sistema"

    if not usuario:
        return None, "denegado_no_reconocido"

    if not usuario["acceso_permitido"]:
        return usuario, "denegado_sin_permiso"

    return usuario, "autorizado"
    