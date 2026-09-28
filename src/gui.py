#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz gráfica de identificación. Usa la misma
validator.verificar_credencial() que el flujo de botones.
"""

import os
import tkinter as tk

from config import LONGITUD_CLAVE, BOTONES
import validator


def gui_disponible():
    return os.environ.get("DISPLAY") is not None


def iniciar_gui_bloqueante():
    resultado_final = {"usuario": None, "resultado": None}
    digitos_validos = "".join(str(n) for n in BOTONES)

    def on_submit():
        texto = entry.get()
        if len(texto) != LONGITUD_CLAVE or any(c not in digitos_validos for c in texto):
            mensaje.config(
                text=f"Ingresa {LONGITUD_CLAVE} dígitos ({digitos_validos[0]}-{digitos_validos[-1]})"
            )
            entry.delete(0, tk.END)
            return  # la ventana sigue abierta

        secuencia = [int(c) for c in texto]
        usuario, resultado = validator.verificar_credencial(secuencia)
        resultado_final["usuario"] = usuario
        resultado_final["resultado"] = resultado
        ventana.destroy()

    ventana = tk.Tk()
    ventana.title("Control de Acceso")

    tk.Label(ventana, text="Ingresa tu clave:").pack(padx=20, pady=(15, 5))

    entry = tk.Entry(ventana, show="*")
    entry.pack(padx=20)
    entry.focus_set()
    entry.bind("<Return>", lambda event: on_submit())

    mensaje = tk.Label(ventana, text="", fg="red")
    mensaje.pack()

    tk.Button(ventana, text="Validar", command=on_submit).pack(pady=(5, 15))

    ventana.mainloop()  # bloquea hasta ventana.destroy() o cierre manual

    return resultado_final["usuario"], resultado_final["resultado"]