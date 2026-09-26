
import tkinter as tk
import validador

def on_submit(entry, resultado_label):
    secuencia = [int(c) for c in entry.get()]
    usuario, resultado = validador.verificar_credencial(secuencia)
    resultado_label.config(text=resultado)
    # aquí se conecta con controller.py para disparar
    # indicar_exito/error/error_sistema y registrar el intento

def iniciar_gui():
    ventana = tk.Tk()
    ventana.title("Control de Acceso")

    entry = tk.Entry(ventana, show="*")
    entry.pack()

    resultado_label = tk.Label(ventana, text="")
    resultado_label.pack()

    boton = tk.Button(ventana, text="Validar",
                       command=lambda: on_submit(entry, resultado_label))
    boton.pack()

    ventana.mainloop()