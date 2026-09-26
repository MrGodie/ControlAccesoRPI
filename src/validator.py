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


def verificar_contraseña(secuencia):
    if secuencia == CONTRASEÑA:
        return True
    else:
        print("Esperabas:", CONTRASEÑA)
        print("Presionaste:", secuencia)
        return False