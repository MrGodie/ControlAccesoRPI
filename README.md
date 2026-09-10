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

## Requirements

### Hardware

- Raspberry Pi (model 5)
- Monitor
- Keyboard
- 3 push buttons
- Jumper wires / breadboard

### Software

- [Add OS, Python version, libraries used, e.g. RPi.GPIO or gpiozero]

## GPIO Pin Assignment

| Button | GPIO Pin | Symbol |
|--------|----------|--------|
| Button 1 | [Pending] | 1 |
| Button 2 | [Pending] | 2 |
| Button 3 | [Pending] | 3 |

## How to Run

1. [Add setup step, e.g. clone the repo]
2. [Add step, e.g. install dependencies]
3. [Add step, e.g. connect buttons per the table above]
4. Run the program: `[add command, e.g. python3 src/main.py]`
5. Enter the sequence using the physical buttons. The result ("Access granted" / "Access denied") will be shown in the terminal.

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
└── src/
    └── ...
```