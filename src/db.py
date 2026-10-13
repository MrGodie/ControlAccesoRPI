#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conexión a MySQL/MariaDB. Las credenciales de conexión se leen de
variables de entorno; nunca deben quedar escritas en el repositorio.
"""

import os
import mysql.connector
from mysql.connector import Error

from config import TIEMPO_ESPERA_BD

_SELECT_USUARIO = (
    "SELECT u.id, u.nombre, r.nombre AS rol, r.acceso_permitido "
    "FROM usuarios u JOIN roles r ON u.rol_id = r.id "
)


def conectar():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "control_acceso_app"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "control_acceso"),
        connection_timeout=TIEMPO_ESPERA_BD,
    )


def _consultar_usuario(condicion, parametros):
    """
    Ejecuta la consulta de usuario con la condición dada. Devuelve el
    diccionario del usuario, None si no existe, o "ERROR_CONEXION" si
    la base de datos no responde (nunca debe confundirse con un rechazo).
    """
    try:
        conexion = conectar()
    except Error as e:
        print("Error de conexión a BD:", e)
        return "ERROR_CONEXION"

    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(_SELECT_USUARIO + condicion, parametros)
        return cursor.fetchone()
    except Error as e:
        print("Error al consultar usuario:", e)
        return "ERROR_CONEXION"
    finally:
        if cursor:
            cursor.close()
        conexion.close()


def obtener_usuario_por_credencial(credencial):
    """Flujo de botones: la clave identifica al usuario."""
    return _consultar_usuario(
        "WHERE u.credencial_hash = SHA2(%s, 256)", (credencial,)
    )


def obtener_usuario_por_id(usuario_id, credencial=None):
    """
    Flujo de la GUI: se busca por ID. Si se entrega una credencial,
    su hash también debe coincidir con el del usuario.
    """
    if credencial is None:
        return _consultar_usuario("WHERE u.id = %s", (usuario_id,))
    return _consultar_usuario(
        "WHERE u.id = %s AND u.credencial_hash = SHA2(%s, 256)",
        (usuario_id, credencial),
    )


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


def guardar_biometria(usuario_id, embedding, modelo, tipo="facial"):
    """Guarda una muestra biométrica (bytes) de un usuario."""
    try:
        conexion = conectar()
    except Error as e:
        print("No se pudo guardar la biometría (fallo de conexión):", e)
        return False

    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO datos_biometricos (usuario_id, tipo, embedding, modelo) "
            "VALUES (%s, %s, %s, %s)",
            (usuario_id, tipo, embedding, modelo)
        )
        conexion.commit()
        return True
    except Error as e:
        print("Error al guardar la biometría:", e)
        return False
    finally:
        if cursor:
            cursor.close()
        conexion.close()


def obtener_biometria(usuario_id=None):
    """
    Devuelve una lista de dicts (id, usuario_id, embedding, modelo).
    Sin usuario_id devuelve todas (para comparar al reconocer).
    Devuelve "ERROR_CONEXION" si la base de datos falla.
    """
    try:
        conexion = conectar()
    except Error as e:
        print("Error de conexión a BD:", e)
        return "ERROR_CONEXION"

    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        sql = "SELECT id, usuario_id, embedding, modelo FROM datos_biometricos"
        if usuario_id is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql + " WHERE usuario_id = %s", (usuario_id,))
        return cursor.fetchall()
    except Error as e:
        print("Error al leer la biometría:", e)
        return "ERROR_CONEXION"
    finally:
        if cursor:
            cursor.close()
        conexion.close()


def eliminar_biometria(usuario_id):
    """Borra todas las muestras biométricas de un usuario."""
    try:
        conexion = conectar()
    except Error as e:
        print("No se pudo borrar la biometría (fallo de conexión):", e)
        return False

    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "DELETE FROM datos_biometricos WHERE usuario_id = %s", (usuario_id,)
        )
        conexion.commit()
        return True
    except Error as e:
        print("Error al borrar la biometría:", e)
        return False
    finally:
        if cursor:
            cursor.close()
        conexion.close()