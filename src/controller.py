#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from config import CONTRASEÑA
import gpio_handler
import validator
import exit
import gui
import db


def procesar_resultado(usuario, resultado, metodo):
    """
    Reacciona ante el resultado de validación y registra el intento,
    sin importar si vino de la GUI o de los botones físicos.
    """
    if resultado == "autorizado":
        gpio_handler.indicar_exito()
        exit.reproducir_audio_exito()
        exit.activar_actuador()
    elif resultado == "error_sistema":
        gpio_handler.indicar_error_sistema()
    else:
        gpio_handler.indicar_error()

    usuario_id = usuario["id"] if usuario else None
    db.registrar_intento(
        usuario_id=usuario_id,
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

            # Esperar hasta detectar presencia mediante el PIR
            presencia = gpio_handler.esperar_presencia(timeout=30)

            if not presencia:
                print("Sin presencia detectada, reiniciando espera...")
                continue

            print("Presencia detectada.")

            # Elegir método de identificación disponible
            if gui.gui_disponible():
                print("Usando interfaz gráfica...")
                usuario, resultado = gui.iniciar_gui_bloqueante()
                metodo = "gui"
            else:
                print("GUI no disponible. Introduce la contraseña con los botones.")
                secuencia_usuario = gpio_handler.esperar_botones(len(CONTRASEÑA))
                usuario, resultado = validator.verificar_credencial(secuencia_usuario)
                metodo = "botones"

            procesar_resultado(usuario, resultado, metodo)

            print("Esperando un nuevo intento...")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSaliendo del programa")

    finally:
        gpio_handler.limpiar()


if __name__ == "__main__":
    main()