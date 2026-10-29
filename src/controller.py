#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada del sistema. Orquesta GPIO, cámara, reconocimiento,
GUI, validación, salida y registro, sin contener lógica propia de
ninguno.

Con interfaz gráfica, la ventana corre en el hilo principal y el ciclo
de acceso en un hilo de trabajo. Sin pantalla, el ciclo corre en el
hilo principal usando los botones físicos.

Orden de identificación: primero el rostro; si no hay cámara, no se
detecta rostro o DeepFace no está instalado, se cae a código y clave.
"""

import threading
import time
import traceback

from config import (
    LONGITUD_CLAVE,
    RECONOCIMIENTO_ACTIVO,
    ROL_ADMINISTRADOR,
    TIEMPO_ESPERA_PRESENCIA,
    TIEMPO_PANTALLA_AUTORIZADO,
    TIEMPO_PANTALLA_DENEGADO,
    TIEMPO_PANTALLA_FALLO,
    TIEMPO_PANTALLA_FALLO_CAMARA,
    TIEMPO_PANTALLA_PREPARANDO,
)
import camera
import enrollment
import face
import gpio_handler
import validator
import exit
import gui
import db

# Segundos que se mantiene cada pantalla de resultado antes de volver a reposo
DURACION_PANTALLA = {
    "autorizado": TIEMPO_PANTALLA_AUTORIZADO,
    "denegado_sin_permiso": TIEMPO_PANTALLA_DENEGADO,
    "denegado_no_reconocido": TIEMPO_PANTALLA_DENEGADO,
    "denegado_rostro_desconocido": TIEMPO_PANTALLA_DENEGADO,
    "error_sistema": TIEMPO_PANTALLA_FALLO,
}

# Se resuelve en main(): la cámara puede no estar presente.
_camara_disponible = False


def procesar_resultado(usuario, resultado, metodo):
    """
    Reacciona al resultado de validación y registra el intento,
    sin importar si vino del rostro, de la GUI o de los botones físicos.
    """
    if resultado == "autorizado":
        gpio_handler.indicar_exito()
        exit.reproducir_audio_exito()
        exit.activar_actuador()
    elif resultado == "error_sistema":
        gpio_handler.indicar_error_sistema()
    else:  # cualquier denegado
        gpio_handler.indicar_error()
        exit.reproducir_audio_error()

    db.registrar_intento(
        usuario_id=usuario["id"] if usuario else None,
        metodo=metodo,
        resultado=resultado
    )


def _mantener_pantalla(inicio, resultado):
    """
    La pantalla de resultado se mantiene su tiempo completo, contando
    lo que tardaron el audio, el actuador y el registro.
    """
    restante = DURACION_PANTALLA[resultado] - (time.monotonic() - inicio)
    if restante > 0:
        time.sleep(restante)


def intento_facial(interfaz):
    """
    Intenta identificar por rostro.

    Devuelve (usuario, resultado) cuando hubo un intento de acceso real,
    o (None, None) cuando no se pudo intentar y hay que caer a la
    identificación manual (sin cámara, sin rostro, sin DeepFace o sin
    poder leer las plantillas).
    """
    interfaz.mostrar_preparando()
    time.sleep(TIEMPO_PANTALLA_PREPARANDO)

    try:
        with camera.sesion_camara():
            interfaz.mostrar_identificando()
            usuario_id, distancia, motivo = face.identificar(
                camera.capturar_muestra_valida
            )
    except camera.CamaraError as error:
        # Un fallo técnico NO es un acceso denegado (NFR-04): se avisa
        # aparte y la persona sigue por código y clave.
        print("Fallo de cámara:", error)
        interfaz.mostrar_fallo_camara("La cámara no responde")
        time.sleep(TIEMPO_PANTALLA_FALLO_CAMARA)
        return None, None

    if motivo == face.NO_DISPONIBLE:
        print("DeepFace no está instalado: se usa identificación manual.")
        return None, None

    if motivo == face.ERROR_BD:
        print("No se pudieron leer las plantillas biométricas.")
        interfaz.mostrar_fallo_camara("Sin conexión con la base de datos")
        time.sleep(TIEMPO_PANTALLA_FALLO_CAMARA)
        return None, None

    if motivo == face.SIN_ROSTRO:
        print("No se detectó ningún rostro.")
        interfaz.mostrar_fallo_camara("No se detectó ningún rostro")
        time.sleep(TIEMPO_PANTALLA_FALLO_CAMARA)
        return None, None

    if motivo == face.DESCONOCIDO:
        cerca = f" (distancia {distancia:.4f})" if distancia is not None else ""
        print("Rostro no reconocido" + cerca)
        return None, "denegado_rostro_desconocido"

    print(f"Rostro reconocido: usuario {usuario_id} (distancia {distancia:.4f})")
    return validator.verificar_rostro(usuario_id)


def es_administrador(usuario):
    """True si el usuario autorizado puede dar de alta a otros."""
    return bool(usuario) and usuario.get("rol") == ROL_ADMINISTRADOR


def gestion_usuarios(interfaz):
    """
    Pantalla de gestión: lista a los usuarios y desde ahí se da de alta
    a los nuevos. La lista se vuelve a leer en cada vuelta para que el
    recién enrolado aparezca de inmediato.
    """
    while True:
        usuarios = db.obtener_usuarios()
        if usuarios == "ERROR_CONEXION":
            interfaz.mostrar_fallo("Sin conexión con la base de datos")
            time.sleep(TIEMPO_PANTALLA_FALLO)
            return

        accion = interfaz.pedir_gestion_usuarios(usuarios)
        if accion != "nuevo":        # "volver", None por inactividad o cierre
            return

        resultado = enrollment.enrolar(interfaz)
        print("Enrolamiento:", resultado)
        # Con cualquier final se regresa a la lista: ahí el administrador
        # ve el resultado y decide si sigue dando de alta.


def sesion_administracion(interfaz, usuario):
    """
    Menú del administrador tras una identificación autorizada.
    Se mantiene abierto hasta que elige salir, se va sin responder o
    cierra la ventana.
    """
    print(f"Modo administración: {usuario['nombre']}")

    while True:
        opcion = interfaz.preguntar_menu_admin(usuario["nombre"])
        if opcion != "gestion":      # "salir", None por inactividad o cierre
            print("Saliendo del modo administración.")
            return

        gestion_usuarios(interfaz)


def ciclo_gui(interfaz):
    """Un ciclo de acceso con interfaz gráfica (reposo -> resultado -> reposo)."""
    interfaz.mostrar_reposo()

    # Esperar presencia mediante el PIR (no autoriza, solo inicia)
    if not gpio_handler.esperar_presencia(timeout=TIEMPO_ESPERA_PRESENCIA):
        print("Sin presencia detectada, reiniciando espera...")
        return

    # ---------------------------- rostro ------------------------------
    if RECONOCIMIENTO_ACTIVO and _camara_disponible and face.disponible():
        usuario, resultado = intento_facial(interfaz)
        if resultado is not None:
            inicio = time.monotonic()
            interfaz.mostrar_resultado(resultado, usuario)
            procesar_resultado(usuario, resultado, "facial")
            _mantener_pantalla(inicio, resultado)
            if resultado == "autorizado" and es_administrador(usuario):
                sesion_administracion(interfaz, usuario)
            interfaz.mostrar_reposo()
            gpio_handler.esperar_fin_presencia()
            print("Esperando un nuevo intento...")
            time.sleep(1)
            return

    # ------------------- código y clave (alternativa) -------------------
    print("Identificación mediante interfaz gráfica.")

    # Activar la lectura de botones durante la identificación.
    gpio_handler.iniciar_lectura_botones(
        interfaz.registrar_boton_fisico
    )

    try:
        datos = interfaz.pedir_identificacion()
    finally:
        # Detener la lectura al validar, cancelar, agotar el tiempo
        # de inactividad o cerrar la ventana.
        gpio_handler.detener_lectura_botones()

    if datos is None:
        print("Identificación cancelada o sin actividad. Volviendo a reposo.")
        interfaz.mostrar_reposo()
        gpio_handler.esperar_fin_presencia()
        return

    usuario_id, secuencia = datos
    interfaz.mostrar_validando()
    usuario, resultado = validator.verificar_usuario(usuario_id, secuencia)

    inicio = time.monotonic()
    interfaz.mostrar_resultado(resultado, usuario)
    procesar_resultado(usuario, resultado, "gui")
    _mantener_pantalla(inicio, resultado)

    # El administrador entra al alta de usuarios desde aquí, después de
    # identificarse con su código y clave.
    if resultado == "autorizado" and es_administrador(usuario):
        sesion_administracion(interfaz, usuario)

    interfaz.mostrar_reposo()
    gpio_handler.esperar_fin_presencia()
    print("Esperando un nuevo intento...")
    time.sleep(1)


def ciclo_botones():
    """Un ciclo de acceso por botones físicos (sin pantalla)."""
    if not gpio_handler.esperar_presencia(timeout=TIEMPO_ESPERA_PRESENCIA):
        print("Sin presencia detectada, reiniciando espera...")
        return

    print("GUI no disponible. Introduce la clave con los botones.")
    secuencia = gpio_handler.esperar_botones(LONGITUD_CLAVE)
    usuario, resultado = validator.verificar_credencial(secuencia)
    procesar_resultado(usuario, resultado, "botones")

    # Volver a un estado estable antes del siguiente ciclo
    gpio_handler.esperar_fin_presencia()
    print("Esperando un nuevo intento...")
    time.sleep(1)


def bucle_principal(interfaz, detener):
    while not detener.is_set():
        print("\n" + "=" * 50)
        print("NUEVO CICLO")
        print("=" * 50)
        if interfaz is not None:
            ciclo_gui(interfaz)
        else:
            ciclo_botones()


def _hilo_de_trabajo(interfaz, detener):
    try:
        bucle_principal(interfaz, detener)
    except Exception:
        traceback.print_exc()
    finally:
        interfaz.cerrar()  # si el ciclo termina, la ventana no debe quedar viva


def main():
    global _camara_disponible

    detener = threading.Event()
    try:
        gpio_handler.inicializar()
        print("Sistema de acceso iniciado.")

        # La cámara es opcional: si falla, la GUI y los botones siguen activos
        _camara_disponible, mensaje_camara = camera.verificar_camara()
        print("Cámara:", mensaje_camara)

        if not _camara_disponible:
            print("El reconocimiento facial no estará disponible.")
        elif not face.disponible():
            print("DeepFace no está instalado: el reconocimiento facial no estará disponible.")
        elif not RECONOCIMIENTO_ACTIVO:
            print("Reconocimiento facial desactivado por configuración.")
        else:
            cargadas = face.cargar_plantillas(forzar=True)
            if cargadas is None:
                print("No se pudieron leer las plantillas biométricas.")
            else:
                print(f"Plantillas biométricas cargadas: {cargadas}")

        interfaz = gui.crear_interfaz() if gui.gui_disponible() else None

        if interfaz is not None:
            hilo = threading.Thread(
                target=_hilo_de_trabajo, args=(interfaz, detener), daemon=True
            )
            hilo.start()
            interfaz.ejecutar()      # bloquea hasta cerrar la ventana
            detener.set()
            hilo.join(timeout=3)
        else:
            print("Sin interfaz gráfica: modo botones.")
            bucle_principal(None, detener)

    except KeyboardInterrupt:
        print("\nSaliendo del programa")

    finally:
        detener.set()
        camera.liberar_camara()
        gpio_handler.limpiar()


if __name__ == "__main__":
    main()