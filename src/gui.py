#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz gráfica del control de acceso (wireframes PI2 y PI3, monitor 1280x720).

Tkinter no es seguro entre hilos: la ventana corre en el hilo principal
(ejecutar) y el controlador, en un hilo de trabajo, le envía órdenes por
una cola. La GUI no consulta la base de datos ni reconoce rostros: solo
muestra pantallas y entrega lo que el usuario escribió.
"""

import os
import queue
import traceback
import tkinter as tk
from tkinter import ttk

from config import (
    BOTONES,
    LONGITUD_CLAVE,
    ENROLAMIENTO_NOMBRE_MAX,
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
FUENTE_MARCADOR = ("Helvetica", 14)


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

    def mostrar_preparando(self):
        """Pantalla 02: pide a la persona colocarse frente a la cámara."""
        self._enviar(self._ui_preparando)

    def mostrar_identificando(self):
        """Pantalla 03: el reconocimiento facial está corriendo."""
        self._enviar(self._ui_identificando)

    def mostrar_fallo_camara(self, detalle=None):
        """Pantalla 07: fallo técnico de cámara, que no es un rechazo."""
        self._enviar(self._ui_fallo_camara, detalle)

    def mostrar_validando(self):
        self._enviar(self._ui_validando)

    def mostrar_resultado(self, resultado, usuario):
        """
        Pantalla de resultado. Con "denegado_rostro_desconocido" incluye los
        botones "Usar botones" y "Reintentar": el controlador espera la
        elección con esperar_opcion().
        """
        self._enviar(self._ui_resultado, resultado, usuario)

    def registrar_boton_fisico(self, numero):
        """
        Recibe una pulsación desde el hilo GPIO.
        La modificación del campo se ejecuta en el hilo de Tkinter.
        """
        self._enviar(self._ui_boton_fisico, numero)

    def pedir_identificacion(self):
        """
        Muestra la pantalla de identificación y espera al usuario.
        Devuelve (id, secuencia_de_clave_o_None), o None si cancela,
        pasan TIEMPO_INACTIVIDAD_GUI segundos sin actividad o se cierra
        la ventana.
        """
        return self._preguntar(self._ui_identificacion)

    def limpiar_respuestas(self):
        """Descarta pulsaciones viejas antes de mostrar una pantalla con opciones."""
        while not self._respuestas.empty():
            try:
                self._respuestas.get_nowait()
            except queue.Empty:
                break

    def esperar_opcion(self, timeout):
        """
        Espera la pulsación de un botón de la pantalla actual hasta
        `timeout` segundos. Devuelve su valor, o None si venció el tiempo.
        """
        try:
            return self._respuestas.get(timeout=timeout)
        except queue.Empty:
            return None

    # ------------------ enrolamiento (modo administración) ---------------

    def preguntar_menu_admin(self, nombre):
        """Menú del administrador. Devuelve "nuevo" o "salir"."""
        return self._preguntar(self._ui_menu_admin, nombre)

    def pedir_datos_usuario(self, roles, valores=None, error=None):
        """
        Pantalla 01: alta de usuario. `roles` es la lista que devuelve
        db.obtener_roles(). `valores` = (nombre, rol_id) para volver a
        rellenar el formulario y `error` un mensaje (clave ocupada, etc.).
        Devuelve {"nombre", "rol_id", "clave"} o None si se cancela.
        """
        return self._preguntar(self._ui_nuevo_usuario, roles, valores, error)

    def confirmar_captura(self, nombre):
        """Pantalla 02: preparación. True si se inicia la captura."""
        return self._preguntar(self._ui_preparar_captura, nombre) == "iniciar"

    def mostrar_captura(self, numero, total, instruccion=None):
        """Pantalla 03: capturando la muestra `numero` de `total`."""
        self._enviar(self._ui_capturando, numero, total, instruccion)

    def preguntar_sin_rostro(self, capturadas, total):
        """Pantalla 04. Devuelve "reintentar" o "cancelar"."""
        resultado = self._preguntar(self._ui_sin_rostro, capturadas, total)
        return resultado or "cancelar"

    def confirmar_descarte(self, capturadas, total):
        """
        Pantalla 08. True si se descarta el enrolamiento. Si nadie
        responde y vence la inactividad, se descarta: dejar la captura
        abierta con la cámara tomada sería peor.
        """
        respuesta = self._preguntar(self._ui_descartar, capturadas, total)
        return respuesta in (None, "descartar")

    def mostrar_fallo_enrolamiento(self, detalle, reintentable=True):
        """
        Pantalla 05: fallo del enrolamiento. ESPERA al administrador.
        Devuelve "reintentar" o "salir" (también si vence la inactividad).
        """
        resultado = self._preguntar(self._ui_fallo_enrolamiento, detalle, reintentable)
        return resultado or "salir"

    def mostrar_generando_plantilla(self, muestras):
        """Pantalla 06: generando la plantilla."""
        self._enviar(self._ui_generando, muestras)

    def mostrar_enrolamiento_completo(self, nombre, rol, muestras, usuario_id=None):
        """Pantalla 07. Devuelve "otro" o "finalizar"."""
        resultado = self._preguntar(self._ui_enrolado, nombre, rol, muestras, usuario_id)
        return resultado or "finalizar"

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

        # Widgets de la pantalla de identificación. Existen solo mientras
        # esa pantalla está montada; fuera de ella valen None.
        self._entrada_id = None
        self._entrada_clave = None
        self._mensaje = None

        # Widgets del alta de usuario (pantalla 01 del enrolamiento).
        self._form_nombre = None
        self._form_rol = None
        self._form_clave = None
        self._roles = []

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

        # Tipografía de la lista desplegable del selector de rol. Si la
        # versión de Tk no la usa, simplemente se ignora.
        self.raiz.option_add("*TCombobox*Listbox.font", FUENTE_CAMPO)

    def _enviar(self, funcion, *args, espera_respuesta=False):
        self._ordenes.put((lambda: funcion(*args), espera_respuesta))

    def _preguntar(self, funcion, *args):
        """
        Muestra una pantalla que espera respuesta y bloquea al hilo de
        trabajo hasta que la ventana la entrega. Vacía primero la cola
        para no leer la respuesta de una pantalla anterior.
        """
        self.limpiar_respuestas()
        self._enviar(funcion, *args, espera_respuesta=True)
        return self._respuestas.get()

    def _responder(self, valor):
        self._detener_inactividad()
        self._respuestas.put(valor)

    def _procesar_ordenes(self):
        if not self._activa:
            return
        while True:
            try:
                orden, espera_respuesta = self._ordenes.get_nowait()
            except queue.Empty:
                break
            try:
                orden()
            except Exception:
                # Una pantalla fallida no debe congelar el sistema. Si
                # alguien esperaba su respuesta, se le contesta None
                # (equivale a cancelar) en lugar de dejarlo bloqueado
                # para siempre en _respuestas.get().
                print("Error en la interfaz gráfica:")
                traceback.print_exc()
                if espera_respuesta:
                    self._respuestas.put(None)
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
        # Los widgets de identificación acaban de ser destruidos: hay que
        # soltar las referencias o una pulsación encolada los tocaría ya
        # muertos y reventaría con TclError.
        self._entrada_id = None
        self._entrada_clave = None
        self._mensaje = None
        self._form_nombre = None
        self._form_rol = None
        self._form_clave = None
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

    @staticmethod
    def _marcador_camara(bloque, texto):
        """
        Recuadro que ocupa el lugar del preview de la cámara. El video en
        vivo no se dibuja aquí: la GUI no toca la cámara, y mostrarlo
        exigiría PIL/ImageTk además de copiar cada fotograma al hilo de
        Tkinter. Queda como marcador, igual que en el wireframe.
        """
        marco = tk.Frame(bloque, bg=FONDO, highlightbackground=BORDE,
                         highlightthickness=2, height=180)
        marco.pack(fill="x", pady=(0, 16))
        marco.pack_propagate(False)
        tk.Label(
            marco, text=texto, font=FUENTE_MARCADOR, bg=FONDO, fg=GRIS,
        ).pack(expand=True)

    @staticmethod
    def _vinetas(bloque, lineas):
        for linea in lineas:
            tk.Label(
                bloque, text=f"·  {linea}", font=FUENTE_ETIQUETA,
                bg=FONDO, fg=TEXTO, anchor="w",
            ).pack(fill="x", pady=2)

    # ----------------------------- pantallas ------------------------------

    def _ui_reposo(self):
        bloque = self._nueva_pantalla("REPOSO")
        self._titulo(bloque, TEXTO_REPOSO, anchor="center")

    def _ui_preparando(self):
        bloque = self._nueva_pantalla("PREPARANDO")
        self._titulo(bloque, "Colóquese frente a la cámara")
        self._marcador_camara(bloque, "INICIANDO CÁMARA")
        self._vinetas(bloque, [
            "Mire al frente, a unos 50 cm",
            "Retire gorra o lentes oscuros",
            "La identificación es automática",
        ])

    def _ui_identificando(self):
        bloque = self._nueva_pantalla("IDENTIFICANDO")
        self._titulo(bloque, "Identificando…")
        self._marcador_camara(bloque, "ROSTRO DETECTADO")
        barra = ttk.Progressbar(bloque, mode="indeterminate", length=420)
        barra.pack(anchor="w")
        barra.start(12)

    def _ui_validando(self):
        bloque = self._nueva_pantalla("VALIDANDO")
        self._titulo(bloque, "Validando…", "Consultando la base de datos", anchor="center")
        barra = ttk.Progressbar(bloque, mode="indeterminate", length=420)
        barra.pack()
        barra.start(12)

    def _ui_fallo_camara(self, detalle=None):
        bloque = self._nueva_pantalla("FALLO DEL SISTEMA")
        self._titulo(bloque, "NO SE PUDO COMPLETAR",
                     detalle or "La cámara no responde")
        self._caja(bloque, "Esto NO es un acceso denegado")
        self._caja(bloque, "Identifíquese con su código y clave")

    def _ui_resultado(self, resultado, usuario):
        if resultado == "autorizado":
            bloque = self._nueva_pantalla("AUTORIZADO")
            self._titulo(bloque, "ACCESO AUTORIZADO", self._nombre_y_rol(usuario))
        elif resultado == "denegado_sin_permiso":
            bloque = self._nueva_pantalla("DENEGADO")
            self._titulo(bloque, "ACCESO DENEGADO", self._nombre_y_rol(usuario))
            self._caja(bloque, "El rol no tiene permiso en este punto de acceso")
        elif resultado == "denegado_rostro_desconocido":
            bloque = self._nueva_pantalla("DENEGADO")
            self._titulo(bloque, "ACCESO DENEGADO", "Rostro no reconocido")
            self._caja(bloque, "El rostro no coincide con ningún usuario dado de alta")
            self._botonera(bloque, [
                ("Usar botones", "botones", True),
                ("Reintentar", "reintentar", False),
            ])
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

    def _ui_boton_fisico(self, numero):
        """
        Añade una pulsación física al campo de clave.
        Se ejecuta exclusivamente en el hilo principal de Tkinter.
        """
        if not self._activa:
            return

        # La pantalla de identificación debe estar activa.
        if self._entrada_clave is None:
            return

        # Ignorar números que no correspondan a botones configurados.
        if numero not in BOTONES:
            return

        try:
            texto_actual = self._entrada_clave.get()
        except tk.TclError:
            # El widget se destruyó entre que se encoló la orden y ahora.
            self._entrada_clave = None
            return

        # No permitir más dígitos que la longitud de la clave.
        if len(texto_actual) >= LONGITUD_CLAVE:
            return

        self._entrada_clave.insert(tk.END, str(numero))
        self._reiniciar_inactividad()

    def _tras_id(self, _evento=None):
        if self._entrada_clave is not None:
            self._entrada_clave.focus_set()
        else:
            self._enviar_identificacion()

    def _enviar_identificacion(self):
        if self._entrada_id is None:
            return

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

    # ================= pantallas de enrolamiento (PI3) ====================

    def _botonera(self, bloque, opciones):
        """
        Fila de botones. `opciones` es [(texto, valor, principal)]; al
        pulsar uno se responde con su valor.
        """
        barra = tk.Frame(bloque, bg=FONDO)
        barra.pack(anchor="w", pady=(14, 0))
        for texto, valor, principal in opciones:
            tk.Button(
                barra, text=texto, font=FUENTE_BOTON,
                bg=TEXTO if principal else FONDO,
                fg="#ffffff" if principal else TEXTO,
                activebackground="#333333" if principal else CAJA,
                activeforeground="#ffffff" if principal else TEXTO,
                padx=22, pady=8,
                command=lambda v=valor: self._responder(v),
            ).pack(side="left", padx=(0, 12))

    def _ui_menu_admin(self, nombre):
        bloque = self._nueva_pantalla("ADMINISTRACIÓN")
        self._titulo(bloque, "Modo administración", f"{nombre} · Administrador")
        self._botonera(bloque, [
            ("Nuevo usuario", "nuevo", True),
            ("Salir", "salir", False),
        ])
        self._reiniciar_inactividad()

    # -- 01 Nuevo usuario ---------------------------------------------------

    def _ui_nuevo_usuario(self, roles, valores=None, error=None):
        bloque = self._nueva_pantalla("DATOS DEL USUARIO")
        self._titulo(bloque, "Nuevo usuario")
        nombre_previo, rol_previo = valores if valores else ("", None)

        self._campo_etiqueta(bloque, "NOMBRE COMPLETO")
        self._form_nombre = tk.Entry(bloque, font=FUENTE_CAMPO, relief="solid", bd=1)
        self._form_nombre.pack(fill="x", ipady=6, pady=(2, 12))
        self._form_nombre.insert(0, nombre_previo)

        self._campo_etiqueta(bloque, "ROL")
        self._roles = roles
        # Los widgets ttk no aceptan font= como los tk normales: según la
        # versión de Tk truena con 'unknown option "-font"'. El tamaño de
        # la lista desplegable se ajusta por la base de opciones.
        self._form_rol = ttk.Combobox(
            bloque, state="readonly",
            values=[r["nombre"] for r in roles],
        )
        indice = next((i for i, r in enumerate(roles) if r["id"] == rol_previo), 0)
        self._form_rol.current(indice)
        self._form_rol.pack(fill="x", ipady=4, pady=(2, 12))

        # La clave no está en el wireframe, pero usuarios.credencial_hash
        # es NOT NULL: sin ella no se puede dar de alta a nadie.
        self._campo_etiqueta(bloque, f"CLAVE ({LONGITUD_CLAVE} dígitos)")
        self._form_clave = tk.Entry(
            bloque, font=FUENTE_CAMPO, show="*", relief="solid", bd=1
        )
        self._form_clave.pack(fill="x", ipady=6, pady=(2, 12))

        self._mensaje = tk.Label(bloque, text=error or "", font=FUENTE_ETIQUETA,
                                 bg=FONDO, fg="#b00020")
        self._mensaje.pack(anchor="w")

        barra = tk.Frame(bloque, bg=FONDO)
        barra.pack(anchor="w", pady=(14, 0))
        tk.Button(
            barra, text="Continuar", font=FUENTE_BOTON, bg=TEXTO, fg="#ffffff",
            activebackground="#333333", activeforeground="#ffffff",
            padx=22, pady=8, command=self._enviar_nuevo_usuario,
        ).pack(side="left")
        tk.Button(
            barra, text="Cancelar", font=FUENTE_BOTON, bg=FONDO, fg=TEXTO,
            padx=22, pady=8, command=self._cancelar,
        ).pack(side="left", padx=(12, 0))

        self._form_nombre.focus_set()
        self._reiniciar_inactividad()
        self.raiz.bind("<Key>", self._reiniciar_inactividad)
        self.raiz.bind("<ButtonPress>", self._reiniciar_inactividad)

    def _enviar_nuevo_usuario(self):
        if self._form_nombre is None:
            return

        nombre = self._form_nombre.get().strip()
        if not nombre or len(nombre) > ENROLAMIENTO_NOMBRE_MAX:
            self._mensaje.config(
                text=f"Escribe el nombre (máximo {ENROLAMIENTO_NOMBRE_MAX} caracteres)"
            )
            self._form_nombre.focus_set()
            return

        digitos_validos = "".join(str(n) for n in BOTONES)
        clave = self._form_clave.get()
        if len(clave) != LONGITUD_CLAVE or any(c not in digitos_validos for c in clave):
            self._mensaje.config(
                text=f"La clave son {LONGITUD_CLAVE} dígitos "
                     f"({digitos_validos[0]}-{digitos_validos[-1]})"
            )
            self._form_clave.delete(0, tk.END)
            self._form_clave.focus_set()
            return

        rol = self._roles[self._form_rol.current()]
        self._responder({"nombre": nombre, "rol_id": rol["id"], "clave": clave})

    # -- 02 Preparación -----------------------------------------------------

    def _ui_preparar_captura(self, nombre):
        bloque = self._nueva_pantalla("PREPARACIÓN")
        self._titulo(bloque, "Prepare la captura", nombre)
        self._marcador_camara(bloque, "VISTA PREVIA DE CÁMARA")
        self._vinetas(bloque, [
            "1 · Colóquese frente a la cámara, a unos 50 cm",
            "2 · Mantenga una expresión neutra",
            "3 · Gire ligeramente la cabeza cuando se le indique",
        ])
        self._botonera(bloque, [
            ("Iniciar captura", "iniciar", True),
            ("Cancelar", "cancelar", False),
        ])
        self._reiniciar_inactividad()

    # -- 03 Capturando ------------------------------------------------------

    def _ui_capturando(self, numero, total, instruccion=None):
        bloque = self._nueva_pantalla("CAPTURANDO")
        self._titulo(bloque, f"Muestra {numero} de {total}",
                     instruccion or "Mire al frente")
        self._marcador_camara(bloque, "ROSTRO DETECTADO")
        self._campo_etiqueta(bloque, "PROGRESO")
        barra = ttk.Progressbar(bloque, mode="determinate",
                                maximum=total, value=numero - 1, length=520)
        barra.pack(anchor="w", pady=(4, 0))

    # -- 04 Sin rostro ------------------------------------------------------

    def _ui_sin_rostro(self, capturadas, total):
        bloque = self._nueva_pantalla("SIN ROSTRO")
        self._titulo(bloque, "NO SE DETECTA NINGÚN ROSTRO", "La captura está en pausa")
        self._marcador_camara(bloque, "SIN ROSTRO EN CUADRO")
        self._vinetas(bloque, [
            "Acérquese y centre el rostro en el recuadro",
            "Verifique que haya luz suficiente",
            f"Muestras válidas hasta ahora: {capturadas} de {total}",
        ])
        self._botonera(bloque, [
            ("Reintentar", "reintentar", True),
            ("Cancelar", "cancelar", False),
        ])
        self._reiniciar_inactividad()

    # -- 05 Fallo del enrolamiento -----------------------------------------

    def _ui_fallo_enrolamiento(self, detalle, reintentable):
        bloque = self._nueva_pantalla("FALLO DEL SISTEMA")
        self._titulo(bloque, "NO SE PUDO COMPLETAR", detalle)
        self._caja(bloque, "Esto NO es un enrolamiento rechazado")
        self._caja(bloque, "El usuario no se guarda hasta completar la captura")
        opciones = [("Salir", "salir", not reintentable)]
        if reintentable:
            opciones.insert(0, ("Reintentar", "reintentar", True))
        self._botonera(bloque, opciones)
        self._reiniciar_inactividad()

    # -- 06 Generando plantilla --------------------------------------------

    def _ui_generando(self, muestras):
        bloque = self._nueva_pantalla("GUARDANDO")
        self._titulo(bloque, "Generando plantilla…",
                     f"Procesando las {muestras} muestras en el equipo local")
        barra = ttk.Progressbar(bloque, mode="indeterminate", length=520)
        barra.pack(anchor="w", pady=(4, 14))
        barra.start(12)
        self._caja(bloque, "Las imágenes capturadas se descartan al terminar")

    # -- 07 Completado ------------------------------------------------------

    def _ui_enrolado(self, nombre, rol, muestras, usuario_id=None):
        bloque = self._nueva_pantalla("COMPLETADO")
        self._titulo(bloque, "ENROLAMIENTO COMPLETADO", f"{nombre} · Rol: {rol}")
        if usuario_id is not None:
            self._caja(bloque, f"Código de usuario: {usuario_id}")
        self._caja(bloque, f"Plantilla creada · {muestras} muestras")
        self._caja(bloque, "Ya puede identificarse con reconocimiento facial")
        self._botonera(bloque, [
            ("Finalizar", "finalizar", True),
            ("Enrolar otro", "otro", False),
        ])
        self._reiniciar_inactividad()

    # -- 08 Descartar -------------------------------------------------------

    def _ui_descartar(self, capturadas, total):
        bloque = self._nueva_pantalla("CANCELAR")
        self._titulo(bloque, "¿Descartar el enrolamiento?",
                     f"Se han capturado {capturadas} de {total} muestras")
        self._caja(bloque, "Las muestras capturadas se descartan")
        self._caja(bloque, "El usuario no se dará de alta")
        self._botonera(bloque, [
            ("Descartar", "descartar", True),
            ("Continuar capturando", "continuar", False),
        ])
        self._reiniciar_inactividad()

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