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
"""

import camera
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


def _capturar_muestras(interfaz):
    """
    Pide muestras hasta juntar ENROLAMIENTO_MUESTRAS válidas.

    Devuelve (lista_de_embeddings, motivo). Si el administrador cancela
    o la cámara falla, la lista viene vacía y el motivo lo explica.
    """
    muestras = []

    while len(muestras) < ENROLAMIENTO_MUESTRAS:
        interfaz.mostrar_captura(len(muestras) + 1, ENROLAMIENTO_MUESTRAS)

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
            accion = interfaz.preguntar_sin_rostro(
                len(muestras), ENROLAMIENTO_MUESTRAS
            )
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


def enrolar(interfaz):
    """
    Corre el enrolamiento completo de un usuario.
    Devuelve uno de: COMPLETADO, CANCELADO, FALLO_CAMARA, FALLO_BD,
    CLAVE_DUPLICADA.
    """
    if not face.disponible():
        interfaz.mostrar_fallo_camara("DeepFace no está instalado")
        return FALLO_CAMARA

    roles = db.obtener_roles()
    if roles == "ERROR_CONEXION" or not roles:
        interfaz.mostrar_fallo_camara("Sin conexión con la base de datos")
        return FALLO_BD

    # Pantalla 01: nombre, rol y clave.
    datos = interfaz.pedir_datos_usuario(roles)
    if datos is None:
        return CANCELADO

    # Pantalla 02: preparación de la captura.
    if not interfaz.confirmar_captura(datos["nombre"]):
        return CANCELADO

    # Pantallas 03, 04 y 08.
    try:
        with camera.sesion_camara():
            muestras, motivo = _capturar_muestras(interfaz)
    except camera.CamaraError as error:
        # Pantalla 05: fallo técnico, distinto de un rechazo (NFR-04).
        print("Fallo de cámara durante el enrolamiento:", error)
        interfaz.mostrar_fallo_camara("La cámara no responde")
        return FALLO_CAMARA

    if motivo == CANCELADO or not muestras:
        return CANCELADO

    # Pantalla 06: generando la plantilla.
    interfaz.mostrar_generando_plantilla(len(muestras))
    usuario_id, motivo = _guardar(datos, muestras)

    if motivo == CLAVE_DUPLICADA:
        interfaz.mostrar_fallo_camara("Esa clave ya está en uso por otro usuario")
        return CLAVE_DUPLICADA
    if motivo == FALLO_BD:
        interfaz.mostrar_fallo_camara("No se pudo guardar el usuario")
        return FALLO_BD

    # Pantalla 07: enrolamiento completado. Sus dos botones deciden si
    # se sigue enrolando o se vuelve a reposo.
    rol = next((r["nombre"] for r in roles if r["id"] == datos["rol_id"]), "")
    accion = interfaz.mostrar_enrolamiento_completo(
        datos["nombre"], rol, len(muestras)
    )
    print(f"Usuario {usuario_id} enrolado con {len(muestras)} muestras.")
    return OTRO if accion == "otro" else COMPLETADO