#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk

import validator


def gui_disponible():
    return os.environ.get("DISPLAY") is not None


def iniciar_gui_bloqueante():
    resultado_final = {"usuario": None, "resultado": None}

    def on_submit():
        secuencia = [int(c) for c in entry.get()]
        usuario, resultado = validator.verificar_credencial(secuencia)
        resultado_final["usuario"] = usuario
        resultado_final["resultado"] = resultado
        ventana.destroy()  # cierra la ventana y libera mainloop()

    ventana = tk.Tk()
    ventana.title("Control de Acceso")

    tk.Label(ventana, text="Ingresa tu credencial:").pack()

    entry = tk.Entry(ventana, show="*")
    entry.pack()

    boton = tk.Button(ventana, text="Validar", command=on_submit)
    boton.pack()

    ventana.mainloop()  # bloquea aquí hasta ventana.destroy()

    return resultado_final["usuario"], resultado_final["resultado"]