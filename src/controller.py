#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada del sistema. Orquesta GPIO, GUI, validación,
salida y registro, sin contener lógica propia de ninguno.

Con interfaz gráfica, la ventana corre en el hilo principal y el ciclo
de acceso en un hilo de trabajo. Sin pantalla, el ciclo corre en el
hilo principal usando los botones físicos.
"""

import threading
import time
import traceback

from config import (
    LONGITUD_CLAVE,
    TIEMPO_ESPERA_PRESENCIA,
    TIEMPO_PANTALLA_AUTORIZADO,
    TIEMPO_PANTALLA_DENEGADO,
    TIEMPO_PANTALLA_FALLO,
)
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
    "error_sistema": TIEMPO_PANTALLA_FALLO,
}


def procesar_resultado(usuario, resultado, metodo):
    """
    Reacciona al resultado de validación y registra el intento,
    sin importar si vino de la GUI o de los botones físicos.
    """
    if resultado == "autorizado":
        gpio_handler.indicar_exito()
        exit.reproducir_audio_exito()
        exit.activar_actuador()
    elif resultado == "error_sistema":
        gpio_handler.indicar_error_sistema()
    else:  # denegado_sin_permiso / denegado_no_reconocido
        gpio_handler.indicar_error()

    db.registrar_intento(
        usuario_id=usuario["id"] if usuario else None,
        metodo=metodo,
        resultado=resultado
    )


def ciclo_gui(interfaz):
    """Un ciclo de acceso con interfaz gráfica (reposo -> resultado -> reposo)."""
    interfaz.mostrar_reposo()

    # Esperar presencia mediante el PIR (no autoriza, solo inicia)
    if not gpio_handler.esperar_presencia(timeout=TIEMPO_ESPERA_PRESENCIA):
        print("Sin presencia detectada, reiniciando espera...")
        return

    print("Identificación mediante interfaz gráfica.")
    datos = interfaz.pedir_identificacion()

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

    # La pantalla de resultado se mantiene su tiempo completo, contando
    # lo que tardaron el audio, el actuador y el registro.
    restante = DURACION_PANTALLA[resultado] - (time.monotonic() - inicio)
    if restante > 0:
        time.sleep(restante)

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
    detener = threading.Event()
    try:
        gpio_handler.inicializar()
        print("Sistema de acceso iniciado.")

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
        gpio_handler.limpiar()


if __name__ == "__main__":
    main()