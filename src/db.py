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

def obtener_roles():
    """
    Devuelve [{id, nombre, descripcion, acceso_permitido}] para llenar el
    selector de rol del alta. "ERROR_CONEXION" si la base de datos falla.
    """
    try:
        conexion = conectar()
    except Error as e:
        print("Error de conexión a BD:", e)
        return "ERROR_CONEXION"

    cursor = None
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, nombre, descripcion, acceso_permitido "
            "FROM roles ORDER BY nombre"
        )
        return cursor.fetchall()
    except Error as e:
        print("Error al leer los roles:", e)
        return "ERROR_CONEXION"
    finally:
        if cursor:
            cursor.close()
        conexion.close()


def crear_usuario(nombre, credencial, rol_id):
    """
    Da de alta un usuario. La credencial se guarda hasheada con SHA2,
    igual que la compara _SELECT_USUARIO.

    Devuelve el id del usuario nuevo, "CLAVE_DUPLICADA" si esa clave ya
    la tiene alguien (credencial_hash es UNIQUE) o "ERROR_CONEXION".
    """
    try:
        conexion = conectar()
    except Error as e:
        print("No se pudo crear el usuario (fallo de conexión):", e)
        return "ERROR_CONEXION"

    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nombre, credencial_hash, rol_id) "
            "VALUES (%s, SHA2(%s, 256), %s)",
            (nombre, credencial, rol_id)
        )
        conexion.commit()
        return cursor.lastrowid
    except Error as e:
        # 1062 = Duplicate entry para una clave única.
        if getattr(e, "errno", None) == 1062:
            print("La clave ya está en uso por otro usuario.")
            return "CLAVE_DUPLICADA"
        print("Error al crear el usuario:", e)
        return "ERROR_CONEXION"
    finally:
        if cursor:
            cursor.close()
        conexion.close()


def eliminar_usuario(usuario_id):
    """
    Borra un usuario. Sus datos biométricos se van con él por el
    ON DELETE CASCADE de datos_biometricos (FR-14).

    Se usa para deshacer un alta a medias: si el usuario ya se creó y
    después falla el guardado de las plantillas, no debe quedar un
    usuario sin rostro que además ocupa una clave.
    """
    try:
        conexion = conectar()
    except Error as e:
        print("No se pudo eliminar el usuario (fallo de conexión):", e)
        return False

    cursor = None
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
        conexion.commit()
        return True
    except Error as e:
        print("Error al eliminar el usuario:", e)
        return False
    finally:
        if cursor:
            cursor.close()
        conexion.close()