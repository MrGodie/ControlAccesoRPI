#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API HTTP para la aplicación móvil. Corre en un hilo aparte, junto al
ciclo de acceso, y solo orquesta: no decide nada.

    POST /api/login     identifica al usuario                (FR-15)
    GET  /api/presence  ¿el PIR detectó presencia?           (FR-16)
    POST /api/access    solicita acceso y devuelve resultado (FR-17, FR-18)

La decisión la toma validator, igual que para la GUI, los botones y el
rostro (FR-20). La reacción física y el registro los hace la misma
función que usan los demás medios, que el controlador entrega al
arrancar el servidor. Aquí no hay reglas de permisos ni funciones
administrativas (NFR-09).

Usa http.server de la biblioteca estándar: no agrega dependencias a la
Raspberry Pi.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from config import API_HOST, API_PUERTO
import gpio_handler
import validator

# Método con el que quedan registrados los intentos hechos desde la app.
METODO = "app"

# Un cuerpo válido es un JSON de dos campos; lo demás se rechaza sin leerlo.
_CUERPO_MAX = 1024
_PIN_MAX = 32

_servidor = None
_procesar_resultado = None


class _PeticionInvalida(Exception):
    pass


def _leer_credenciales(datos):
    """Devuelve (usuario_id, pin) o lanza _PeticionInvalida."""
    if not isinstance(datos, dict):
        raise _PeticionInvalida("Se esperaba un objeto JSON")

    usuario_id = datos.get("id")
    pin = datos.get("pin")

    # bool es subclase de int: True no es un identificador.
    if isinstance(usuario_id, str) and usuario_id.isdigit():
        usuario_id = int(usuario_id)
    if isinstance(usuario_id, bool) or not isinstance(usuario_id, int) or usuario_id <= 0:
        raise _PeticionInvalida("El campo 'id' debe ser un número entero positivo")

    if not isinstance(pin, str) or not pin.isdigit() or len(pin) > _PIN_MAX:
        raise _PeticionInvalida("El campo 'pin' debe ser una cadena de dígitos")

    return usuario_id, pin


def identificar(datos):
    """
    POST /api/login. Confirma que el código y la clave corresponden a un
    usuario registrado. No abre nada ni registra un intento: eso ocurre
    al solicitar el acceso.

    La respuesta no dice cuál de los dos campos estuvo mal (FR-15), y
    una falla de la base de datos no se reporta como credencial
    inválida (NFR-11).
    """
    usuario_id, pin = _leer_credenciales(datos)
    usuario, resultado = validator.verificar_usuario(usuario_id, pin)

    if resultado == "error_sistema":
        return 503, {"result": resultado}

    return 200, {
        "identified": usuario is not None,
        "name": usuario["nombre"] if usuario else None,
    }


def consultar_presencia():
    """GET /api/presence. La presencia habilita la solicitud; no autoriza."""
    return 200, {"present": gpio_handler.presencia_reciente()}


def solicitar_acceso(datos):
    """
    POST /api/access. Valida con la lógica común y ejecuta la misma
    reacción física y el mismo registro que los demás medios de acceso.
    Devuelve el resultado tal como lo entrega validator, sin traducirlo.
    """
    usuario_id, pin = _leer_credenciales(datos)
    usuario, resultado = validator.verificar_usuario(usuario_id, pin)
    _procesar_resultado(usuario, resultado, METODO)

    return 200, {
        "result": resultado,
        "name": usuario["nombre"] if usuario else None,
    }


class _Manejador(BaseHTTPRequestHandler):
    server_version = "ControlAccesoRPI"

    def do_GET(self):
        if self.path == "/api/presence":
            self._atender(consultar_presencia)
        else:
            self._responder(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        if self.path == "/api/login":
            self._atender(identificar, con_cuerpo=True)
        elif self.path == "/api/access":
            self._atender(solicitar_acceso, con_cuerpo=True)
        else:
            self._responder(404, {"error": "Ruta no encontrada"})

    def _atender(self, operacion, con_cuerpo=False):
        try:
            if con_cuerpo:
                estado, cuerpo = operacion(self._leer_json())
            else:
                estado, cuerpo = operacion()
        except _PeticionInvalida as error:
            estado, cuerpo = 400, {"error": str(error)}
        except Exception as error:
            # Una falla técnica nunca se reporta como acceso denegado.
            print("Error al atender la petición de la app:", repr(error))
            estado, cuerpo = 500, {"result": "error_sistema"}
        self._responder(estado, cuerpo)

    def _leer_json(self):
        try:
            longitud = int(self.headers.get("Content-Length", 0))
        except ValueError:
            raise _PeticionInvalida("Content-Length inválido")
        if longitud <= 0 or longitud > _CUERPO_MAX:
            raise _PeticionInvalida("Cuerpo vacío o demasiado grande")
        try:
            return json.loads(self.rfile.read(longitud).decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise _PeticionInvalida("El cuerpo no es JSON válido")

    def _responder(self, estado, cuerpo):
        contenido = json.dumps(cuerpo).encode("utf-8")
        try:
            self.send_response(estado)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(contenido)))
            self.end_headers()
            self.wfile.write(contenido)
        except OSError:
            # El teléfono cerró la conexión antes de recibir la respuesta.
            pass

    def log_message(self, formato, *args):
        # Una línea por petición en la terminal del sistema. Solo lleva
        # la ruta y el estado: las credenciales viajan en el cuerpo.
        print(f"API {self.address_string()} - {formato % args}")


def iniciar(procesar_resultado, host=None, puerto=None):
    """
    Levanta el servidor en un hilo daemon y regresa de inmediato.

    `procesar_resultado` es la función del controlador que enciende los
    LEDs, reproduce el audio, mueve el servomotor y registra el intento.

    Devuelve True si quedó escuchando. Si no puede levantar (puerto
    ocupado, sin red), avisa y devuelve False: el sistema arranca igual
    y los demás medios de acceso siguen disponibles.
    """
    global _servidor, _procesar_resultado

    if _servidor is not None:
        return True

    host = API_HOST if host is None else host
    puerto = API_PUERTO if puerto is None else puerto

    try:
        servidor = ThreadingHTTPServer((host, puerto), _Manejador)
    except OSError as error:
        print(f"La API de la app móvil no pudo iniciar en {host}:{puerto}: {error}")
        print("El acceso desde la app no estará disponible.")
        return False

    servidor.daemon_threads = True
    _procesar_resultado = procesar_resultado
    _servidor = servidor

    threading.Thread(
        target=servidor.serve_forever, name="ApiAppMovil", daemon=True
    ).start()

    print(f"API de la app móvil escuchando en {host}:{servidor.server_address[1]}")
    return True


def puerto_activo():
    """Puerto en el que escucha el servidor, o None si no está activo."""
    return _servidor.server_address[1] if _servidor is not None else None


def detener():
    """Cierra el servidor si estaba activo."""
    global _servidor

    if _servidor is None:
        return
    _servidor.shutdown()
    _servidor.server_close()
    _servidor = None
