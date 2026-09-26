#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lógica de validación, independiente de GPIO.
Esta separación permite que en el futuro la GUI invoque
exactamente la misma función que el flujo de botones (NFR-05).
Nota: la comparación aquí sigue siendo contra CONTRASEÑA fija;
la migración a consulta MySQL es el Issue de "Connect validation
logic to the MySQL database".
"""

from config import CONTRASEÑA

import db

def verificar_credencial(secuencia):
    credencial = "".join(map(str, secuencia))
    resultado_db = db.obtener_usuario_por_credencial(credencial, credencial)

    if resultado_db == "ERROR_CONEXION":
        return None, "error_sistema"
    elif resultado_db:
        return resultado_db, "autorizado"
    else:
        return None, "denegado_no_reconocido"
    