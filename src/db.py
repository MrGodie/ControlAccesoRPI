#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


def obtener_usuario_por_credencial(identificador, credencial_hash):
    """
    Retorna un dict con {id, nombre, rol} si la credencial es válida,
    None si no se reconoce, o "ERROR_CONEXION" si falla la conexión/consulta.
    """
    try:
        conexion = conectar()
    except Error as e:
        print("Error de conexión a BD:", e)
        return "ERROR_CONEXION"

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT u.id, u.nombre, r.nombre AS rol "
            "FROM usuarios u JOIN roles r ON u.rol_id = r.id "
            "WHERE u.identificador = %s AND u.credencial_hash = %s AND u.activo = TRUE",
            (identificador, credencial_hash)
        )
        usuario = cursor.fetchone()
        return usuario  # None si no existe
    except Error as e:
        print("Error al consultar usuario:", e)
        return "ERROR_CONEXION"
    finally:
        cursor.close()
        conexion.close()


def registrar_intento(usuario_id, metodo, resultado, detalle=None):
    """
    Inserta un intento de acceso. No debe interrumpir el flujo
    principal si falla — solo se reporta el problema.
    """
    try:
        conexion = conectar()
    except Error as e:
        print("No se pudo registrar el intento (fallo de conexión):", e)
        return False

    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO intentos_acceso (usuario_id, metodo, resultado, detalle) "
            "VALUES (%s, %s, %s, %s)",
            (usuario_id, metodo, resultado, detalle)
        )
        conexion.commit()
        return True
    except Error as e:
        print("Error al registrar el intento:", e)
        return False
    finally:
        cursor.close()
        conexion.close()