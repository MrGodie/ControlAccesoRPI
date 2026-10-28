#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enrolamiento facial guiado (wireframes PI3, lámina Interface_2).

Orquesta el alta de un usuario nuevo: datos, captura de varias muestras,
generación de las plantillas y confirmación. No dibuja pantallas (eso es
gui.py) ni habla con la cámara o el modelo directamente más allá de
pedirles lo que necesita.

El usuario se crea en la base de datos hasta el final, cuando ya hay
muestras válidas: si el administrador cancela a medias, no queda nadie
dado de alta ni una clave ocupada.

Todo fallo se muestra en una pantalla que ESPERA al administrador
(Reintentar / Salir). Antes los avisos se pintaban y se reemplazaban al
instante por el menú, así que parecía que el botón "Nuevo usuario" no
hacía nada.
"""

import time

import camera
import config
import db
import face
from config import (
    ENROLAMIENTO_MUESTRAS,
    ENROLAMIENTO_INTENTOS_POR_MUESTRA,
    RECONOCIMIENTO_MODELO,
)

# Resultados de enrolar()
COMPLETADO = "completado"
OTRO = "otro"              # completado, y el administrador quiere enrolar a alguien más
CANCELADO = "cancelado"
FALLO_CAMARA = "fallo_camara"
FALLO_BD = "fallo_bd"
CLAVE_DUPLICADA = "clave_duplicada"

# Segundos entre una muestra y la siguiente, para que la persona cambie de
# pose: cinco muestras idénticas no mejoran el reconocimiento.
PAUSA_ENTRE_MUESTRAS = getattr(config, "ENROLAMIENTO_PAUSA_MUESTRAS", 1.2)

# Instrucción que se muestra en cada muestra (wireframe 03).
INSTRUCCIONES = [
    "Mire al frente",
    "Gire ligeramente la cabeza hacia la derecha",
    "Gire ligeramente la cabeza hacia la izquierda",
    "Levante ligeramente el mentón",
    "Baje ligeramente el mentón",
]


def _fallo(interfaz, detalle, motivo, reintentable=True):
    """
    Muestra el fallo y espera. Devuelve True si el administrador pide
    reintentar. Queda en la terminal el motivo exacto.
    """
    print(f"Enrolamiento: {detalle} [{motivo}]")
    return interfaz.mostrar_fallo_enrolamiento(detalle, reintentable) == "reintentar"


def _capturar_muestras(interfaz):
    """
    Pide muestras hasta juntar ENROLAMIENTO_MUESTRAS válidas.

    Devuelve (lista_de_embeddings, motivo). Si el administrador cancela,
    la lista viene vacía y el motivo es CANCELADO.
    """
    muestras = []

    while len(muestras) < ENROLAMIENTO_MUESTRAS:
        numero = len(muestras)
        interfaz.mostrar_captura(
            numero + 1, ENROLAMIENTO_MUESTRAS,
            INSTRUCCIONES[numero % len(INSTRUCCIONES)],
        )
        if numero > 0:
            time.sleep(PAUSA_ENTRE_MUESTRAS)  # tiempo para cambiar de pose

        embedding = None
        for _ in range(ENROLAMIENTO_INTENTOS_POR_MUESTRA):
            fotograma, _motivo = camera.capturar_muestra_valida()
            if fotograma is None:
                continue
            embedding = face.obtener_embedding(fotograma)
            if embedding is not None:
                break

        if embedding is None:
            # Pantalla 04 del wireframe: no se detecta ningún rostro.
            accion = interfaz.preguntar_sin_rostro(len(muestras), ENROLAMIENTO_MUESTRAS)
            if accion != "reintentar":
                # Pantalla 08: confirmar que se descarta lo capturado.
                if interfaz.confirmar_descarte(len(muestras), ENROLAMIENTO_MUESTRAS):
                    return [], CANCELADO
            continue

        muestras.append(embedding)

    return muestras, None


def _guardar(datos, muestras):
    """
    Crea el usuario y guarda sus plantillas. Devuelve (usuario_id, motivo).
    Si algo falla después de crear al usuario, lo borra para no dejar un
    alta a medias.
    """
    usuario_id = db.crear_usuario(
        nombre=datos["nombre"],
        credencial=datos["clave"],
        rol_id=datos["rol_id"],
    )

    if usuario_id == "CLAVE_DUPLICADA":
        return None, CLAVE_DUPLICADA
    if usuario_id == "ERROR_CONEXION" or usuario_id is None:
        return None, FALLO_BD

    for embedding in muestras:
        guardado = db.guardar_biometria(
            usuario_id=usuario_id,
            embedding=face.serializar(embedding),
            modelo=RECONOCIMIENTO_MODELO,
        )
        if not guardado:
            # Un usuario sin plantillas no sirve y además ocupa la clave.
            print("Falló el guardado de una plantilla; se deshace el alta.")
            db.eliminar_usuario(usuario_id)
            return None, FALLO_BD

    # Las plantillas en memoria quedaron viejas: que se recarguen.
    face.invalidar_plantillas()
    return usuario_id, None


def _pedir_datos(interfaz, roles):
    """
    Pantalla 01. Devuelve los datos del formulario, None si se cancela o
    FALLO_BD. La clave se comprueba aquí, no hasta el final: así el
    administrador no captura cinco muestras para enterarse de que la
    clave ya estaba ocupada.
    """
    valores, error = None, None
    while True:
        datos = interfaz.pedir_datos_usuario(roles, valores, error)
        if datos is None:
            return None

        valores = (datos["nombre"], datos["rol_id"])
        ocupante = db.obtener_usuario_por_credencial(datos["clave"])
        if ocupante == "ERROR_CONEXION":
            if not _fallo(interfaz, "Sin conexión con la base de datos", FALLO_BD):
                return FALLO_BD
            error = None
            continue
        if ocupante:
            error = "Esa clave ya está en uso. Elija otra."
            continue
        return datos


def enrolar(interfaz):
    """
    Corre el enrolamiento completo de un usuario.
    Devuelve uno de: COMPLETADO, OTRO, CANCELADO, FALLO_CAMARA, FALLO_BD,
    CLAVE_DUPLICADA.
    """
    if not face.disponible():
        _fallo(interfaz, "El reconocimiento facial no está disponible",
               FALLO_CAMARA, reintentable=False)
        return FALLO_CAMARA

    while True:
        roles = db.obtener_roles()
        if roles != "ERROR_CONEXION" and roles:
            break
        if not _fallo(interfaz, "Sin conexión con la base de datos", FALLO_BD):
            return FALLO_BD

    # Pantalla 01: nombre, rol y clave.
    datos = _pedir_datos(interfaz, roles)
    if datos is None:
        return CANCELADO
    if datos == FALLO_BD:
        return FALLO_BD

    # Pantalla 02: preparación de la captura.
    if not interfaz.confirmar_captura(datos["nombre"]):
        return CANCELADO

    # Pantallas 03, 04 y 08.
    while True:
        try:
            with camera.sesion_camara():
                muestras, motivo = _capturar_muestras(interfaz)
            break
        except camera.CamaraError as error:
            # Pantalla 05: fallo técnico, distinto de un rechazo (NFR-04).
            print("Fallo de cámara durante el enrolamiento:", error)
            if not _fallo(interfaz, "Sin acceso a la cámara", FALLO_CAMARA):
                return FALLO_CAMARA

    if motivo == CANCELADO or not muestras:
        return CANCELADO

    # Pantalla 06: generando la plantilla.
    interfaz.mostrar_generando_plantilla(len(muestras))
    while True:
        usuario_id, motivo = _guardar(datos, muestras)
        if motivo is None:
            break
        if motivo == CLAVE_DUPLICADA:
            _fallo(interfaz, "Esa clave ya está en uso por otro usuario",
                   CLAVE_DUPLICADA, reintentable=False)
            return CLAVE_DUPLICADA
        if not _fallo(interfaz, "No se pudo guardar el usuario", FALLO_BD):
            return FALLO_BD
        interfaz.mostrar_generando_plantilla(len(muestras))

    # Pantalla 07: enrolamiento completado. Muestra el código de usuario,
    # que la persona necesita para identificarse por código y clave.
    rol = next((r["nombre"] for r in roles if r["id"] == datos["rol_id"]), "")
    accion = interfaz.mostrar_enrolamiento_completo(
        datos["nombre"], rol, len(muestras), usuario_id
    )
    print(f"Usuario {usuario_id} enrolado con {len(muestras)} muestras.")
    return OTRO if accion == "otro" else COMPLETADO