# ControlAccesoRPI

Sistema de control de acceso mediante secuencia de pulsaciones en botones físicos conectados a las entradas GPIO de una Raspberry Pi. El sistema captura una secuencia de pulsaciones, la compara contra una clave válida configurada y muestra en terminal si el acceso fue autorizado o denegado.

## Características

Captura de pulsaciones desde botones físicos conectados a GPIO.

Almacenamiento temporal de la secuencia hasta alcanzar la longitud definida (entre 4 y 6 pulsaciones).

Comparación automática de la secuencia capturada contra la clave válida configurada.

Mensajes en terminal: Acceso autorizado o Acceso denegado.

Reinicio automático del estado de captura tras cada intento, sin necesidad de reiniciar el programa.

Anti-rebote (debounce) para evitar registros duplicados por una sola pulsación física.

Requisitos 

## Hardware

Raspberry Pi (modelo 5)

Monitor

Teclado

Resistencias

Cables jumper / protoboard

## Software

Raspberry Pi OS 

 

 