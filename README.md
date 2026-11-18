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
*   *bitacora.py*: Full event log (FR-23). Records everything the system does, not only access attempts: identifications, administration sessions and changes, technical failures, start and stop. Events are queued and written by a background thread into the `eventos` table, so an access never waits for the database; if the database is down they are retried, and each event has its own `evento_uid` so a retry never stores it twice.
*   *exit.py*: Actuation and output driver. Controls Pulse Width Modulation (PWM) duty cycles for servo-based locking mechanisms and triggers digital buzzers for acoustic signaling.
*   *config.py*: Centralized configuration repository defining pin mappings, temporal constants, and system parameters without modifying business logic (FR-04).

## Mobile App

Integrativo 4 adds a mobile application as a new way to request access. It is meant for users only and works alongside the existing access methods (physical buttons, graphical interface and facial recognition), which keep working unchanged (NFR-10).

*   *Identification:* the user identifies themselves in the app with their user code and password (FR-15).
*   *Request after identifying:* the access request is enabled as soon as the user is identified. The app does not wait for the PIR sensor; the Raspberry Pi decides the result (FR-16).
*   *Result in the app:* the app shows whether access was authorized, denied, or could not be completed due to a technical condition. A technical failure is never shown as a denial (FR-17, FR-18, NFR-11).
*   *Return to the start:* when the operation ends, the app clears the entered data and returns to its initial state (FR-19).
*   *Same validation logic:* requests from the app are authorized by the same validation used by the other access methods; there is no separate authorization path for the app (FR-20).
*   *No administrative functions:* the app does not register users, change permissions, manage accounts, or configure the system (NFR-09).

The requirements are listed in `requirements.md` (FR-15 to FR-20, NFR-09 to NFR-11) and the screens in `docs/Interface_5.png` and `docs/Interface_6.png`.

**Status:** implemented in Kotlin (`android/`), with the API on the Raspberry Pi in `src/api_server.py`. Tested on a PC; the run on the real Raspberry Pi and on a phone is tracked in `docs/verification_checklist.md` (PIC-107).

### How it works

The app is organized in three layers that do not mix:

| Layer | Classes | Responsibility |
| :--- | :--- | :--- |
| Interface | `IdentificationActivity`, `RequestActivity`, `ResultActivity` | Show the three views and forward the taps |
| Logic | `AccessManager` | Who is identified, whether the request is enabled, the last result |
| Communication | `RaspberryClient` | HTTP requests to the Raspberry Pi, and nothing else |

The Raspberry Pi serves three routes, on port 8000 by default (`API_PUERTO` in `src/config.py`):

| Method | Route | Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/login` | Identify the user (FR-15) |
| `GET` | `/api/presence` | Has the PIR sensor detected presence? Still served, but the app no longer uses it (PIC-115) |
| `POST` | `/api/access` | Request access and receive the result (FR-17, FR-18) |

`/api/access` calls `validator.verificar_usuario()` and then `controller.procesar_resultado()`, the same functions the other access methods use. The API runs in its own thread next to the access cycle; if it cannot start, the system starts anyway and the other methods keep working.

### Installation

*   The app runs on the user's phone and sends its requests to the Raspberry Pi that runs this system, so the Raspberry Pi must be running and reachable from the phone.
*   No administrator setup is done from the app; users and permissions are still managed on the Raspberry Pi.

| Step | How |
| :--- | :--- |
| Platform and SDK | Android 8.0 or newer on the phone. To build: JDK 17 or newer and the Android SDK (platform 35, build-tools 35.0.0), or Android Studio |
| Build | Open the `android/` folder in Android Studio, or run `./gradlew assembleDebug` inside it. The APK is written to `android/app/build/outputs/apk/debug/` |
| Deployment to the phone | Run the app from Android Studio with the phone connected by USB, or copy `app-debug.apk` to the phone and install it |
| Connecting the app to the Raspberry Pi | Phone and Raspberry Pi on the same network. In the first view, tap **Conexión** and type the address of the Raspberry Pi, for example `192.168.1.50:8000` |

The API needs nothing new on the Raspberry Pi: it uses the Python standard library. It starts with the system (`python3 src/controller.py`) and can be turned off with `API_ACTIVA = False` in `src/config.py`.

### Tests

Inside `android/`:

```
./gradlew testDebugUnitTest
```

The tests run on the PC, without a phone: the logic and the HTTP client against a server that answers like the API, and the three views with Robolectric. To check a real Raspberry Pi from the PC:

```
RASPBERRY_URL=http://<pi-address>:8000 RASPBERRY_USER_ID=<id> RASPBERRY_PIN=<key> ./gradlew testDebugUnitTest --tests "*LiveRaspberryTest*"
```

### Trying the app without the Raspberry Pi

`tools/simulated_api.py` serves the real `src/api_server.py` on a PC. Only the PIR sensor, the database and the physical reaction are simulated, so the app gets the same answers it gets from the Raspberry Pi. From the repository root:

```
python tools/simulated_api.py
```

In the first view of the app, tap **Conexión** and type `10.0.2.2:8000` from the Android Studio emulator, or `<PC address>:8000` from a phone on the same Wi-Fi. While it runs, type `e` to toggle a database failure and `q` to stop. `p` toggles the presence of the PIR sensor, which the app no longer needs.

| Code | Key | Result |
| :--- | :--- | :--- |
| 1 | 123 | `autorizado` |
| 2 | 456 | `denegado_sin_permiso` |
| any other | any | `denegado_no_reconocido` |

It never touches GPIO, the database or the access log. It does not replace the run on the real prototype (`docs/verification_checklist.md`).

### Known limitation

The code and key travel over plain HTTP on the local network. They are stored hashed in the database, but they are not encrypted in transit. HTTPS or a session token is future work.

## Project Structure

```
ControlAccesoRPI/
├── README.md
├── requirements.md
├── traceability.md
├── setup_audio.sh
├── docs/
│   ├── Interface.png
│   ├── Interface_2.png
│   ├── Interface_3.png
│   ├── Interface_4.png
│   ├── Interface_5.png
│   ├── Interface_6.png
│   ├── bpmn-process.md
│   ├── data.md
│   ├── dfd-0.md
│   ├── dfd-1.md
│   ├── flow.md
│   ├── sequence.md
│   ├── states.md
│   ├── system_architecture.md
│   └── system_flowchart.md
├── sounds/
│   ├── error.wav
│   ├── exito.wav
│   └── fallo.wav
├── tools/
│   ├── generate_mobile_wireframes.py
│   └── simulated_api.py
├── android/                 (mobile app, Kotlin)
│   └── app/src/
│       ├── main/java/com/controlaccesorpi/mobile/
│       │   ├── model/       (User, AccessRequest, AccessResult, ResultStatus, AppState)
│       │   ├── network/     (RaspberryClient)
│       │   ├── logic/       (AccessManager)
│       │   └── ui/          (the three views)
│       └── test/            (unit and screen tests)
└── src/
    ├── api_server.py
    ├── bitacora.py
    ├── camera.py
    ├── config.py
    ├── controller.py
    ├── db.py
    ├── enrollment.py
    ├── exit.py
    ├── face.py
    ├── gpio_handler.py
    ├── gui.py
    ├── validator.py
    └── database/
        ├──schema.sql
        └──migration.sql
```