#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz gráfica del control de acceso (wireframes PI2, monitor 1280x720).

Tkinter no es seguro entre hilos: la ventana corre en el hilo principal
(ejecutar) y el controlador, en un hilo de trabajo, le envía órdenes por
una cola. La GUI no consulta la base de datos: solo muestra pantallas y
entrega lo que el usuario escribió.
"""

import os
import queue
import tkinter as tk
from tkinter import ttk

from config import (
    BOTONES,
    LONGITUD_CLAVE,
    GUI_REQUIERE_CLAVE,
    GUI_ID_MAX_DIGITOS,
    GUI_PANTALLA_COMPLETA,
    PUNTO_ACCESO,
    TEXTO_REPOSO,
    TIEMPO_INACTIVIDAD_GUI,
)

FONDO = "#ffffff"
TEXTO = "#111111"
GRIS = "#666666"
CAJA = "#f2f2f2"
BORDE = "#cccccc"

FUENTE_ENCABEZADO = ("Helvetica", 11)
FUENTE_TITULO = ("Helvetica", 44, "bold")
FUENTE_SUBTITULO = ("Helvetica", 20)
FUENTE_CAJA = ("Helvetica", 18)
FUENTE_ETIQUETA = ("Helvetica", 12)
FUENTE_CAMPO = ("Helvetica", 22)
FUENTE_BOTON = ("Helvetica", 16, "bold")


def gui_disponible():
    return os.environ.get("DISPLAY") is not None


def crear_interfaz():
    """Devuelve la interfaz o None si no se pudo abrir la ventana."""
    try:
        return InterfazAcceso()
    except tk.TclError as error:
        print("No se pudo abrir la interfaz gráfica:", error)
        return None


class InterfazAcceso:
    # -------------------- API pública (cualquier hilo) --------------------

    def mostrar_reposo(self):
        self._enviar(self._ui_reposo)

    def pedir_identificacion(self):
        """
        Muestra la pantalla de identificación y espera al usuario.
        Devuelve (id, secuencia_de_clave_o_None), o None si cancela,
        pasan TIEMPO_INACTIVIDAD_GUI segundos sin actividad o se cierra
        la ventana.
        """
        while not self._respuestas.empty():
            self._respuestas.get_nowait()
        self._enviar(self._ui_identificacion)
        return self._respuestas.get()

    def mostrar_validando(self):
        self._enviar(self._ui_validando)

    def mostrar_resultado(self, resultado, usuario):
        self._enviar(self._ui_resultado, resultado, usuario)

    def cerrar(self):
        self._enviar(self._destruir)

    def ejecutar(self):
        """Bucle de la ventana; bloquea el hilo principal hasta cerrarla."""
        self.raiz.after(50, self._procesar_ordenes)
        self.raiz.mainloop()

    # ------------------------- construcción base --------------------------

    def __init__(self):
        self._ordenes = queue.Queue()      # controlador -> ventana
        self._respuestas = queue.Queue()   # ventana -> controlador
        self._activa = True
        self._temporizador = None

        self.raiz = tk.Tk()
        self.raiz.title("Control de Acceso")
        self.raiz.configure(bg=FONDO)
        if GUI_PANTALLA_COMPLETA:
            self.raiz.attributes("-fullscreen", True)
        else:
            self.raiz.geometry("1280x720")
        self.raiz.protocol("WM_DELETE_WINDOW", self._destruir)

        encabezado = tk.Frame(self.raiz, bg=FONDO)
        encabezado.pack(fill="x", padx=40, pady=(28, 0))
        tk.Label(
            encabezado, text=f"CONTROL DE ACCESO · {PUNTO_ACCESO}",
            font=FUENTE_ENCABEZADO, bg=FONDO, fg=GRIS,
        ).pack(side="left")
        self._estado = tk.Label(
            encabezado, text="", font=FUENTE_ENCABEZADO, bg=FONDO, fg=GRIS
        )
        self._estado.pack(side="right")

        self._contenido = tk.Frame(self.raiz, bg=FONDO)
        self._contenido.pack(fill="both", expand=True, padx=80, pady=20)

    def _enviar(self, funcion, *args):
        self._ordenes.put(lambda: funcion(*args))

    def _procesar_ordenes(self):
        if not self._activa:
            return
        try:
            while True:
                self._ordenes.get_nowait()()
        except queue.Empty:
            pass
        except Exception as error:  # una pantalla fallida no debe congelar la GUI
            print("Error en la interfaz gráfica:", error)
        if self._activa:
            self.raiz.after(50, self._procesar_ordenes)

    def _destruir(self):
        if not self._activa:
            return
        self._activa = False
        self._detener_inactividad()
        self._respuestas.put(None)  # libera al controlador si esperaba datos
        self.raiz.destroy()

    def _nueva_pantalla(self, estado):
        self._detener_inactividad()
        for widget in self._contenido.winfo_children():
            widget.destroy()
        self._estado.config(text=f"ESTADO: {estado}")
        bloque = tk.Frame(self._contenido, bg=FONDO)
        bloque.pack(expand=True, fill="x")
        return bloque

    @staticmethod
    def _titulo(bloque, texto, subtitulo=None, anchor="w"):
        tk.Label(
            bloque, text=texto, font=FUENTE_TITULO, bg=FONDO, fg=TEXTO,
        ).pack(anchor=anchor)
        if subtitulo:
            tk.Label(
                bloque, text=subtitulo, font=FUENTE_SUBTITULO, bg=FONDO, fg=GRIS,
            ).pack(anchor=anchor, pady=(6, 18))

    @staticmethod
    def _caja(bloque, texto):
        tk.Label(
            bloque, text=texto, font=FUENTE_CAJA, bg=CAJA, fg=TEXTO,
            anchor="w", padx=14, pady=10,
        ).pack(fill="x", pady=(0, 10))

    # ----------------------------- pantallas ------------------------------

    def _ui_reposo(self):
        bloque = self._nueva_pantalla("REPOSO")
        self._titulo(bloque, TEXTO_REPOSO, anchor="center")

    def _ui_validando(self):
        bloque = self._nueva_pantalla("VALIDANDO")
        self._titulo(bloque, "Validando…", "Consultando la base de datos", anchor="center")
        barra = ttk.Progressbar(bloque, mode="indeterminate", length=420)
        barra.pack()
        barra.start(12)

    def _ui_resultado(self, resultado, usuario):
        if resultado == "autorizado":
            bloque = self._nueva_pantalla("AUTORIZADO")
            self._titulo(bloque, "ACCESO AUTORIZADO", self._nombre_y_rol(usuario))
        elif resultado == "denegado_sin_permiso":
            bloque = self._nueva_pantalla("DENEGADO")
            self._titulo(bloque, "ACCESO DENEGADO", self._nombre_y_rol(usuario))
        elif resultado == "denegado_no_reconocido":
            bloque = self._nueva_pantalla("DENEGADO")
            self._titulo(bloque, "ACCESO DENEGADO", "No fue posible verificar la identidad")
        else:  # error_sistema
            bloque = self._nueva_pantalla("FALLO DEL SISTEMA")
            self._titulo(bloque, "NO SE PUDO COMPLETAR", "Sin conexión con la base de datos")
            self._caja(bloque, "Esto NO es un acceso denegado")
            self._caja(bloque, "Reintente o utilice los botones físicos")

    @staticmethod
    def _nombre_y_rol(usuario):
        return f"{usuario['nombre']} · Rol: {usuario['rol']}"

    # ------------------------- pantalla de identificación -----------------

    def _ui_identificacion(self):
        bloque = self._nueva_pantalla("IDENTIFICACIÓN")
        self._titulo(bloque, "Identifíquese")

        self._campo_etiqueta(bloque, "CÓDIGO DE USUARIO (ID)")
        self._entrada_id = tk.Entry(bloque, font=FUENTE_CAMPO, relief="solid", bd=1)
        self._entrada_id.pack(fill="x", ipady=6, pady=(2, 14))

        self._entrada_clave = None
        if GUI_REQUIERE_CLAVE:
            self._campo_etiqueta(bloque, "CLAVE")
            self._entrada_clave = tk.Entry(
                bloque, font=FUENTE_CAMPO, show="*", relief="solid", bd=1
            )
            self._entrada_clave.pack(fill="x", ipady=6, pady=(2, 14))

        self._mensaje = tk.Label(bloque, text="", font=FUENTE_ETIQUETA, bg=FONDO, fg="#b00020")
        self._mensaje.pack(anchor="w")

        botones = tk.Frame(bloque, bg=FONDO)
        botones.pack(anchor="w", pady=(8, 0))
        tk.Button(
            botones, text="Validar", font=FUENTE_BOTON, bg=TEXTO, fg="#ffffff",
            activebackground="#333333", activeforeground="#ffffff",
            padx=22, pady=8, command=self._enviar_identificacion,
        ).pack(side="left")
        tk.Button(
            botones, text="Cancelar", font=FUENTE_BOTON, bg=FONDO, fg=TEXTO,
            padx=22, pady=8, command=self._cancelar,
        ).pack(side="left", padx=(12, 0))

        self._entrada_id.bind("<Return>", self._tras_id)
        if self._entrada_clave is not None:
            self._entrada_clave.bind("<Return>", lambda _e: self._enviar_identificacion())
        self._entrada_id.focus_set()
        self._reiniciar_inactividad()
        self.raiz.bind("<Key>", self._reiniciar_inactividad)
        self.raiz.bind("<ButtonPress>", self._reiniciar_inactividad)

    @staticmethod
    def _campo_etiqueta(bloque, texto):
        tk.Label(bloque, text=texto, font=FUENTE_ETIQUETA, bg=FONDO, fg=GRIS).pack(anchor="w")

    def _tras_id(self, _evento=None):
        if self._entrada_clave is not None:
            self._entrada_clave.focus_set()
        else:
            self._enviar_identificacion()

    def _enviar_identificacion(self):
        texto_id = self._entrada_id.get().strip()
        if not (texto_id.isascii() and texto_id.isdigit()) or len(texto_id) > GUI_ID_MAX_DIGITOS:
            self._mensaje.config(text=f"Ingresa tu ID (solo dígitos, máximo {GUI_ID_MAX_DIGITOS})")
            self._entrada_id.delete(0, tk.END)
            self._entrada_id.focus_set()
            return

        secuencia = None
        if self._entrada_clave is not None:
            digitos_validos = "".join(str(n) for n in BOTONES)
            texto = self._entrada_clave.get()
            if len(texto) != LONGITUD_CLAVE or any(c not in digitos_validos for c in texto):
                self._mensaje.config(
                    text=f"La clave son {LONGITUD_CLAVE} dígitos ({digitos_validos[0]}-{digitos_validos[-1]})"
                )
                self._entrada_clave.delete(0, tk.END)
                self._entrada_clave.focus_set()
                return
            secuencia = [int(c) for c in texto]

        self._detener_inactividad()
        self._respuestas.put((int(texto_id), secuencia))

    def _cancelar(self):
        self._detener_inactividad()
        self._respuestas.put(None)

    # --------------------------- inactividad ------------------------------

    def _reiniciar_inactividad(self, _evento=None):
        if self._temporizador is not None:
            self.raiz.after_cancel(self._temporizador)
        self._temporizador = self.raiz.after(
            int(TIEMPO_INACTIVIDAD_GUI * 1000), self._cancelar
        )

    def _detener_inactividad(self):
        if self._temporizador is not None:
            self.raiz.after_cancel(self._temporizador)
            self._temporizador = None
        self.raiz.unbind("<Key>")
        self.raiz.unbind("<ButtonPress>")