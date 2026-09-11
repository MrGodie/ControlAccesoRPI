# RPiAccessControl

Access control system based on a sequence of presses on physical buttons connected to the GPIO inputs of a Raspberry Pi. The system captures a sequence of button presses, compares it against a configured valid key, and displays in the terminal whether access was granted or denied.

This is the first stage of a system that will grow throughout the semester. This delivery focuses on the local prototype only — no network, database, or external services are included at this stage.

## Team Members

| Name |
|------|
| Arantza Paola Jaime Quevedo |
| Diego Hernández Alfaro |
| Luis Angel Gutiérrez Magallanes |
| Hugo Buentello Arriaga |
| Carlos Alberto Limon Escamilla |

## Features

- Capture of button presses from physical buttons connected to GPIO.
- Temporary storage of the sequence until it reaches the defined length (between 4 and 6 presses).
- Automatic comparison of the captured sequence against the configured valid key.
- Terminal messages: "Access granted" or "Access denied".
- Automatic reset of the capture state after each attempt, with no need to restart the program.
- Debounce logic to prevent duplicate registrations from a single physical press.


### Hardware

- Raspberry Pi (model 5)
- Monitor
- Keyboard
- 5 push buttons
- Jumper wires / breadboard

### Software

- [Add OS, Python version, libraries used, e.g. RPi.GPIO or gpiozero]


## Evidence of Result

[Insertar aquí una captura de pantalla de la terminal mostrando un intento exitoso y uno fallido, o una breve descripción textual de la corrida, una vez completado el prototipo.]

## Project Structure

```
ControlAccesoRPI/
├── README.md
├── requirements.md
├── traceability.md
├── docs/
│   └── flow.md
│   └── dfd-0.md
│   └── dfd-1.md
│   └── system_flowchart.md
└── src/
    └── controller.py
```