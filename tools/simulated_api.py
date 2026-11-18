"""
Run the mobile app API on a PC, without the Raspberry Pi.

It serves the real src/api_server.py, so the routes, the JSON and the
status codes are exactly the ones the app gets from the Raspberry Pi.
Only what needs the device is replaced:

    gpio_handler  the PIR sensor is a switch toggled from this terminal
    validator     a fixed list of test users instead of the MySQL database
    db            the event log (src/bitacora.py) is printed, not stored
    reaction      LEDs, speaker and servo are printed instead of moved

The decision rules are the same as in src/validator.py: an unknown code or
a wrong key is "denegado_no_reconocido", a user without access is
"denegado_sin_permiso", and a database failure is "error_sistema".

Test users:

    code  key  name                 access
    1     123  Usuario Prueba       yes
    2     456  Usuario Sin Permiso  no

Usage (from the repository root):
    python tools/simulated_api.py [--port 8000] [--present]

Then, in the first view of the app, tap "Conexión" and type:
    10.0.2.2:8000       from the Android Studio emulator
    <PC address>:8000   from a phone on the same Wi-Fi (allow the port in
                        the Windows firewall)

Commands while it runs (type the letter and press Enter):
    p   toggle the presence of the PIR sensor
    e   toggle a simulated database failure
    q   stop

For the PC only: it never touches GPIO, the database or the access log.
"""

import argparse
import os
import sys
import threading
import types

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "src")

# code: (key, name, access allowed)
USERS = {
    1: ("123", "Usuario Prueba", True),
    2: ("456", "Usuario Sin Permiso", False),
}

_state = {"present": False, "db_failure": False}
_lock = threading.Lock()


def _get(key):
    with _lock:
        return _state[key]


def _toggle(key):
    with _lock:
        _state[key] = not _state[key]
        return _state[key]


def recent_presence(ventana=None):
    """Stands in for gpio_handler.presencia_reciente()."""
    return _get("present")


def verify_user(usuario_id, secuencia=None):
    """
    Stands in for validator.verificar_usuario(): same arguments, same
    (user_or_None, result) answer, with the test users instead of MySQL.
    """
    if _get("db_failure"):
        return None, "error_sistema"

    credential = None if secuencia is None else "".join(map(str, secuencia))
    entry = USERS.get(usuario_id)
    if entry is None or (credential is not None and credential != entry[0]):
        return None, "denegado_no_reconocido"

    _key, name, allowed = entry
    user = {"id": usuario_id, "nombre": name, "acceso_permitido": allowed}
    return user, ("autorizado" if allowed else "denegado_sin_permiso")


def show_reaction(usuario, resultado, metodo):
    """Stands in for controller.procesar_resultado()."""
    name = usuario["nombre"] if usuario else "-"
    reaction = {
        "autorizado": "green LED, exito.wav, servo opens and closes",
        "denegado_sin_permiso": "red LED, error.wav, servo stays closed",
        "denegado_no_reconocido": "red LED, error.wav, servo stays closed",
        "error_sistema": "red LED blinks, fallo.wav, servo stays closed",
    }.get(resultado, "unknown result")
    print(f"[simulated] {metodo} | {name} | {resultado} -> {reaction}")

    # Same log entry as controller.procesar_resultado().
    import bitacora
    bitacora.registrar(bitacora.ACCESO, metodo,
                       usuario_id=usuario["id"] if usuario else None,
                       resultado=resultado)


def store_event(evento):
    """Stands in for db.registrar_evento(): the event is already printed."""
    return True


def _load_api_server():
    """Import src/api_server.py with the simulated modules in place."""
    gpio_handler = types.ModuleType("gpio_handler")
    gpio_handler.presencia_reciente = recent_presence

    validator = types.ModuleType("validator")
    validator.verificar_usuario = verify_user

    db = types.ModuleType("db")
    db.registrar_evento = store_event

    sys.modules["gpio_handler"] = gpio_handler
    sys.modules["validator"] = validator
    sys.modules["db"] = db
    sys.path.insert(0, os.path.abspath(SRC))

    import api_server
    import bitacora
    bitacora.iniciar()
    return api_server


def _status():
    presence = "ON" if _get("present") else "off"
    database = "FAILING" if _get("db_failure") else "ok"
    return f"presence {presence} | database {database}"


def main():
    parser = argparse.ArgumentParser(description="Run the mobile app API on a PC, without the Raspberry Pi.")
    parser.add_argument("--port", type=int, default=8000, help="port to listen on (default 8000)")
    parser.add_argument("--present", action="store_true", help="start with presence detected")
    args = parser.parse_args()

    _state["present"] = args.present
    api_server = _load_api_server()

    if not api_server.iniciar(show_reaction, host="0.0.0.0", puerto=args.port):
        sys.exit(1)

    print("Test users: code 1 / key 123 (access), code 2 / key 456 (no access)")
    print("Commands: p = toggle presence, e = toggle database failure, q = quit")
    print(_status())

    try:
        for line in sys.stdin:
            command = line.strip().lower()
            if command == "p":
                _toggle("present")
            elif command == "e":
                _toggle("db_failure")
            elif command == "q":
                break
            elif command:
                print("Unknown command. p = presence, e = database failure, q = quit")
                continue
            print(_status())
    except KeyboardInterrupt:
        pass
    finally:
        api_server.detener()


if __name__ == "__main__":
    main()
