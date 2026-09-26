#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada del sistema. Orquesta GPIO y validación,
sin contener lógica propia de ninguno de los dos.
"""

import time

from config import CONTRASEÑA
import gpio_handler
import validador


def main():
    try:
        gpio_handler.inicializar()
        print("Contraseña actual:", CONTRASEÑA)
        print("Sistema de acceso iniciado.")

        while True:
            print("\n" + "=" * 50)
            print("NUEVO INTENTO")
            print("=" * 50)

            # Esperar hasta detectar presencia mediante el PIR
            gpio_handler.esperar_presencia()

            # Solicitar la contraseña mediante los botones
            print("Presencia detectada. Introduce la contraseña.")
            secuencia_usuario = gpio_handler.esperar_botones(
                len(CONTRASEÑA)
            )

            # Validar la secuencia introducida
            if validador.verificar_contraseña(secuencia_usuario):
                gpio_handler.indicar_exito()
            else:
                gpio_handler.indicar_error()

            print("Esperando un nuevo intento...")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSaliendo del programa")

    finally:
        gpio_handler.limpiar()


if __name__ == "__main__":
    main()