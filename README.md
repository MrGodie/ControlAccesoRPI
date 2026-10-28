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

*   Raspberry Pi 5
*   Keyboard
*   Monitor
*   1x Passive Infrared (PIR) Motion Sensor
*   3x Momentary Push Buttons (Tactile switches)
*   5x LEDs (3x Sequence indicators, 1x Green status, 1x Red status)
*   5x Current-limiting resistors (220Ω - 330Ω recommended)
*   1x Active or Passive 5V/3.3V Buzzer
*   1x 50 Hz Analog/Digital Micro Servo (e.g., SG90)
*   Breadboard and male-to-female / male-to-male jumper wires
*   External power supply and HDMI display (for GUI deployment)


### Software
*   Raspberry Pi OS (64-bit recommended)
*   Python 3.9+
*   Python packages: RPi.GPIO, mysql-connector-python, tkinter
*   MySQL Server / MariaDB Server

### Core Features

*   *Presence Detection:* Automated event initiation triggered by a Passive Infrared (PIR) sensor to preserve system resources during idle states.
*   *Dual Authentication Modes:* Fallback input design supporting both physical sequence buttons (hardware mode) and desktop input forms (GUI mode).
*   *Physical Actuation & Feedback:*
    *   Automated physical barrier control via 50 Hz PWM servo actuation.
    *   Active buzzer acoustic signaling for authorized unlocks.
    *   Independent visual LED indicators for individual button confirmation, authorized entry (green), denied entry (red), and system errors.
*   *Input Debounce Optimization:* Software-level debouncing logic to mitigate mechanical contact noise and prevent duplicate registrations (NFR-01).
*   *Relational Access Auditing:* Structured event logging recording timestamps, user references, access vectors (GUI vs. buttons), and operational results.

### Hardware Configuration (GPIO Pinout)

All pin references follow the Broadcom (BCM) GPIO numbering standard:

| Component | Pin (BCM) | Mode | Default State / Configuration |
| :--- | :--- | :--- | :--- |
| Sequence Button 1 | GPIO 4 | Input | Internal Pull-Up (PUD_UP) |
| Sequence Button 2 | GPIO 5 | Input | Internal Pull-Up (PUD_UP) |
| Sequence Button 3 | GPIO 6 | Input | Internal Pull-Up (PUD_UP) |
| Sequence Indicator LED 1 | GPIO 18 | Output | Active High |
| Sequence Indicator LED 2 | GPIO 19 | Output | Active High |
| Sequence Indicator LED 3 | GPIO 20 | Output | Active High |
| Status LED Green (Granted) | GPIO 12 | Output | Active High |
| Status LED Red (Denied/Error) | GPIO 13 | Output | Active High |
| PIR Motion Sensor | GPIO 16 | Input | Active High (Motion Triggered) |
| Servo Actuator | GPIO 26 | Output | 50 Hz PWM Signal |
| Audio Buzzer | GPIO 27 | Output | Active High |

### Architecture and System Design

The system implements a modular architecture under the src/ directory to guarantee high cohesion, low coupling, and maintainability (NFR-02):

*   *controller.py*: Central orchestrator and execution loop. Governs system state, awaits presence triggers, delegates input reading, executes verification routines, dispatches actuator responses, and ensures event persistence.
*   *gpio_handler.py*: Hardware abstraction layer for GPIO operations. Handles pin initialization, pull-up input sensing, debouncing routines, LED indicator control, and motion sensor event loops.
*   *gui.py*: Presentation layer implemented in Tkinter. Provides a desktop interface for entering credentials via masked input fields.
*   *validator.py*: Decoupled credential evaluation logic. Normalizes inputs captured from both the physical buttons and the GUI before forwarding verification requests to the data layer.
*   *db.py*: Persistence layer utilizing mysql.connector. Connects to a local relational database (control_acceso), authenticates credentials against stored records, and logs access attempts.
*   *exit.py*: Actuation and output driver. Controls Pulse Width Modulation (PWM) duty cycles for servo-based locking mechanisms and triggers digital buzzers for acoustic signaling.
*   *config.py*: Centralized configuration repository defining pin mappings, temporal constants, and system parameters without modifying business logic (FR-04).

## Project Structure

```
ControlAccesoRPI/
├── README.md
├── requirements.md
├── traceability.md
├── docs/
│   ├── Interface.png
│   ├── bpmn-process.md
│   ├── data.md
│   ├── dfd-0.md
│   ├── dfd-1.md
│   ├── flow.md
│   ├── sequence.md
│   ├── states.md
│   └── system_flowchart.md
└── src/
    ├── config.py
    ├── controller.py
    ├── db.py
    ├── exit.py
    ├── gpio_handler.py
    ├── gui.py
    ├── validator.py
    └── database/
        ├──schema.sql
        └──migration.sql
```