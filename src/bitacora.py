#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bitácora completa del sistema (FR-23): todo lo que pasa, no solo los
intentos de acceso. Accesos por cualquier medio, identificaciones,
entradas y salidas de administración, altas y enrolamientos, fallos
técnicos, arranque y apagado.

registrar() no bloquea: pone el evento en una cola y un hilo aparte lo
escribe en la tabla eventos. Así un acceso nunca espera a la base de
datos, y si la base no responde el evento no se pierde: se queda en la
cola y se reintenta. Cada evento lleva un identificador propio
(evento_uid), así que un reintento nunca lo guarda dos veces.

La tabla intentos_acceso (FR-09) se sigue llenando igual que antes; esta
bitácora no la reemplaza.

Límite conocido: la cola vive en memoria. Si la Raspberry se apaga con la
base de datos caída, los eventos que no alcanzaron a guardarse se pierden
(se avisa en la terminal al apagar).
"""

import collections
import datetime
import threading
import uuid

import db

# --- Tipos de evento --------------------------------------------------
ACCESO = "acceso"                         # intento de acceso con su resultado
IDENTIFICACION = "identificacion"         # identificarse sin pedir acceso (app), cancelar, sin rostro
PRESENCIA = "presencia"                   # el PIR inició un ciclo de acceso
ADMIN_INICIO = "admin_inicio"             # entró al menú de administración
ADMIN_FIN = "admin_fin"                   # salió del menú de administración
CONSULTA_USUARIOS = "consulta_usuarios"   # abrió la lista de usuarios
ALTA_USUARIO = "alta_usuario"             # dio de alta a un usuario nuevo
ENROLAMIENTO = "enrolamiento"             # registró el rostro de un usuario existente
ACCION_RECHAZADA = "accion_rechazada"     # pidió algo que su rol no permite
PETICION_RECHAZADA = "peticion_rechazada" # la API recibió una petición inválida
FALLO_TECNICO = "fallo_tecnico"           # cámara, base de datos, error inesperado
SISTEMA_INICIO = "sistema_inicio"
SISTEMA_FIN = "sistema_fin"

# --- Orígenes que no son un medio de acceso ----------------------------
ORIGEN_SISTEMA = "sistema"

# Largos de las columnas de la tabla eventos.
_LARGO = {"tipo": 40, "origen": 20, "resultado": 30, "detalle": 255, "dispositivo": 64}

# Eventos que se guardan en memoria mientras la base no responde. Con la
# cola llena se descarta el más viejo, y se avisa.
PENDIENTES_MAX = 1000

# Segundos entre reintentos cuando la base no responde.
ESPERA_REINTENTO = 10

_pendientes = collections.deque()
_condicion = threading.Condition()
_hilo = None
_detenerse = False


def _recortar(campo, valor):
    if valor is None:
        return None
    texto = str(valor)
    largo = _LARGO[campo]
    return texto if len(texto) <= largo else texto[: largo - 1] + "…"


def nuevo_evento(tipo, origen, usuario_id=None, afectado_id=None,
                 resultado=None, detalle=None, fecha_hora=None,
                 sin_conexion=False, dispositivo=None, evento_uid=None):
    """Arma el evento con las columnas de la tabla eventos."""
    return {
        "evento_uid": evento_uid or str(uuid.uuid4()),
        "fecha_hora": fecha_hora or datetime.datetime.now().replace(microsecond=0),
        "tipo": _recortar("tipo", tipo),
        "origen": _recortar("origen", origen),
        "usuario_id": usuario_id,
        "afectado_id": afectado_id,
        "resultado": _recortar("resultado", resultado),
        "detalle": _recortar("detalle", detalle),
        "sin_conexion": bool(sin_conexion),
        "dispositivo": _recortar("dispositivo", dispositivo),
    }


def _describir(evento):
    partes = [f"Bitácora: {evento['tipo']} ({evento['origen']})"]
    if evento["usuario_id"] is not None:
        partes.append(f"usuario {evento['usuario_id']}")
    if evento["afectado_id"] is not None:
        partes.append(f"sobre {evento['afectado_id']}")
    if evento["resultado"]:
        partes.append(evento["resultado"])
    if evento["detalle"]:
        partes.append(evento["detalle"])
    return " | ".join(partes)


def registrar(tipo, origen, **datos):
    """
    Registra un evento sin bloquear. Devuelve su evento_uid.

    `datos` acepta usuario_id, afectado_id, resultado, detalle, fecha_hora,
    sin_conexion, dispositivo y evento_uid (ver nuevo_evento).
    """
    evento = nuevo_evento(tipo, origen, **datos)
    print(_describir(evento))

    with _condicion:
        if len(_pendientes) >= PENDIENTES_MAX:
            descartado = _pendientes.popleft()
            print("Bitácora llena sin base de datos; se descarta el evento",
                  descartado["evento_uid"])
        _pendientes.append(evento)
        _condicion.notify()
    return evento["evento_uid"]


def _escribir(evento):
    """
    Escribe un evento. True si quedó guardado (o ya lo estaba), False si
    la base no respondió y hay que reintentar.
    """
    respuesta = db.registrar_evento(evento)

    if respuesta == "USUARIO_INEXISTENTE":
        # El usuario ya no existe: se guarda sin la referencia, pero el
        # número queda en el detalle para no perder a quién correspondía.
        nota = f"usuario {evento['usuario_id']}, afectado {evento['afectado_id']} (no existen)"
        detalle = f"{evento['detalle']} | {nota}" if evento["detalle"] else nota
        evento = dict(evento, usuario_id=None, afectado_id=None,
                      detalle=_recortar("detalle", detalle))
        respuesta = db.registrar_evento(evento)

    return respuesta is True


def _trabajar():
    while True:
        with _condicion:
            while not _pendientes and not _detenerse:
                _condicion.wait()
            if not _pendientes:
                return
            evento = _pendientes.popleft()

        if _escribir(evento):
            continue

        # La base no respondió: el evento vuelve al frente de la cola,
        # para no cambiar el orden, y se espera antes de reintentar.
        with _condicion:
            _pendientes.appendleft(evento)
            if _detenerse:
                return
            _condicion.wait(ESPERA_REINTENTO)


def iniciar():
    """Arranca el hilo que escribe la bitácora. Se puede llamar varias veces."""
    global _hilo, _detenerse

    with _condicion:
        if _hilo is not None and _hilo.is_alive():
            return
        _detenerse = False
        _hilo = threading.Thread(target=_trabajar, name="Bitacora", daemon=True)
        _hilo.start()


def detener(espera=5):
    """
    Termina de escribir lo pendiente (hasta `espera` segundos) y detiene
    el hilo. Lo que no alcanzó a guardarse se avisa en la terminal.
    """
    global _hilo, _detenerse

    with _condicion:
        _detenerse = True
        _condicion.notify_all()
    if _hilo is not None:
        _hilo.join(espera)
        _hilo = None

    with _condicion:
        restantes = len(_pendientes)
    if restantes:
        print(f"Bitácora: {restantes} eventos no se guardaron (base de datos sin respuesta).")


def pendientes():
    """Cuántos eventos esperan a ser escritos."""
    with _condicion:
        return len(_pendientes)
