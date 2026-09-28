#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada del sistema. Orquesta GPIO, GUI, validación,
salida y registro, sin contener lógica propia de ninguno.
"""

import time

from config import LONGITUD_CLAVE
import gpio_handler
import validator
import exit
import gui
import db


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


def main():
    try:
        gpio_handler.inicializar()
        print("Sistema de acceso iniciado.")

        while True:
            print("\n" + "=" * 50)
            print("NUEVO CICLO")
            print("=" * 50)

            # Esperar presencia mediante el PIR (no autoriza, solo inicia)
            if not gpio_handler.esperar_presencia(timeout=30):
                print("Sin presencia detectada, reiniciando espera...")
                continue

            # Elegir la vía de identificación disponible
            if gui.gui_disponible():
                print("Identificación mediante interfaz gráfica.")
                usuario, resultado = gui.iniciar_gui_bloqueante()
                metodo = "gui"

                if resultado is None:
                    print("Ventana cerrada sin validar. Volviendo a espera.")
                    gpio_handler.esperar_fin_presencia()
                    continue
            else:
                print("GUI no disponible. Introduce la clave con los botones.")
                secuencia = gpio_handler.esperar_botones(LONGITUD_CLAVE)
                usuario, resultado = validator.verificar_credencial(secuencia)
                metodo = "botones"

            procesar_resultado(usuario, resultado, metodo)

            # Volver a un estado estable antes del siguiente ciclo
            gpio_handler.esperar_fin_presencia()
            print("Esperando un nuevo intento...")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSaliendo del programa")

    finally:
        gpio_handler.limpiar()


if __name__ == "__main__":
    main()