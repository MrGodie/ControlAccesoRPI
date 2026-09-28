#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conexión a MySQL/MariaDB. Las credenciales de conexión se leen de
variables de entorno; nunca deben quedar escritas en el repositorio.
"""

import os
import mysql.connector
from mysql.connector import Error


def conectar():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "control_acceso_app"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "control_acceso")
    )


def obtener_usuario_por_credencial(credencial):
  
    try:
        conexion = conectar()
    except Error as e:
        print("Error de conexión a BD:", e)
        return "ERROR_CONEXION"

    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT u.id, u.nombre, r.nombre AS rol, r.acceso_permitido "
            "FROM usuarios u JOIN roles r ON u.rol_id = r.id "
            "WHERE u.credencial_hash = SHA2(%s, 256)",
            (credencial,)
        )
        return cursor.fetchone()
    except Error as e:
        print("Error al consultar usuario:", e)
        return "ERROR_CONEXION"
    finally:
        if cursor:
            cursor.close()
        conexion.close()


def registrar_intento(usuario_id, metodo, resultado):
    """
    Inserta un intento de acceso. Si falla, solo se reporta:
    no debe interrumpir el flujo principal.
    """
    try:
        conexion = conectar()
    except Error as e:
        print("No se pudo registrar el intento (fallo de conexión):", e)
        return False

    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO intentos_acceso (usuario_id, metodo, resultado, fecha_hora) "
            "VALUES (%s, %s, %s, NOW())",
            (usuario_id, metodo, resultado)
        )
        conexion.commit()
        return True
    except Error as e:
        print("Error al registrar el intento:", e)
        return False
    finally:
        if cursor:
            cursor.close()
        conexion.close()