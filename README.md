# RPiAccessControl

Access control system on a Raspberry Pi. A person is identified by facial recognition, by their user code and key on the screen, by a key on physical buttons, or from a mobile app on their phone. Every method goes through the same validation against a MySQL database; an authorized access lights the green LED, plays a sound and opens a servo, and everything that happens is logged.

The project started as a button-only prototype and grew in stages: GUI and database (V2), local facial recognition, and the mobile app (Integrativo 4, now in its second stage). Everything runs on the local network; no cloud service is used.

## Team Members

| Name |
|------|
| Arantza Paola Jaime Quevedo |
| Diego Hernández Alfaro |
| Luis Angel Gutiérrez Magallanes |
| Hugo Buentello Arriaga |
| Carlos Alberto Limon Escamilla |

## Features

- Four ways to identify: face in front of the camera, code and key on the screen, key on the physical buttons, and the mobile app (face with the phone camera, or code and key).
- One shared validation for every method, based on the role of the user (`usuario`, `admin`, `soporte`).
- Distinct answers for authorized, denied (no permission or not recognized) and technical failure, which is never shown as a denial.
- Green LED, sound and servo on an authorized access; red LED and sound otherwise.
- Administration on the screen for roles that can manage: register users, enroll or re-enroll their face, and change their role.
- Full event log in MySQL: accesses, identifications, administration and failures.
- Key length set in `config.py` (`LONGITUD_CLAVE`, 3 by default) and debounce on the physical buttons.


### Hardware

*   Raspberry Pi 5
*   Keyboard
*   Monitor (for the GUI)
*   USB camera (facial recognition)
*   USB speaker (Jabra Link 370) for the access sounds
*   1x Passive Infrared (PIR) Motion Sensor
*   3x Momentary Push Buttons (Tactile switches)
*   5x LEDs (3x Sequence indicators, 1x Green status, 1x Red status)
*   5x Current-limiting resistors (220Ω - 330Ω recommended)
*   1x Buzzer on GPIO 27 (wired since the first stage; the sounds now play through the USB speaker)
*   1x 50 Hz Analog/Digital Micro Servo (e.g., SG90)
*   Breadboard and male-to-female / male-to-male jumper wires
*   External power supply and HDMI display (for GUI deployment)


### Software
*   Raspberry Pi OS (64-bit recommended)
*   Python 3.9+
*   Python packages: RPi.GPIO, mysql-connector-python, tkinter, opencv-python, numpy, deepface
*   MySQL Server / MariaDB Server
*   `aplay` (ALSA) for the sounds; `setup_audio.sh` sets up the USB speaker
*   The database connection is read from the environment variables `DB_HOST`, `DB_USER`, `DB_PASSWORD` and `DB_NAME` (NFR-06)

### Core Features

*   *Presence Detection:* Automated event initiation triggered by a Passive Infrared (PIR) sensor to preserve system resources during idle states.
*   *Several Authentication Modes:* local facial recognition first, then code and key on the GUI, physical buttons when there is no monitor, and the mobile app (face, or code and key).
*   *Physical Actuation & Feedback:*
    *   Automated physical barrier control via 50 Hz PWM servo actuation.
    *   Access sounds through the USB speaker: success, denial and technical failure (`sounds/`).
    *   Independent visual LED indicators for individual button confirmation, authorized entry (green), denied entry (red), and system errors.
*   *Input Debounce Optimization:* Software-level debouncing logic to mitigate mechanical contact noise and prevent duplicate registrations (NFR-01).
*   *Relational Access Auditing:* every access attempt in `intentos_acceso` (user, method, result, time) and every event in `eventos` (FR-23).

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
| Audio Buzzer | GPIO 27 | Output | Active High (kept low; sounds go through the USB speaker) |

### Architecture and System Design

The system implements a modular architecture under the src/ directory to guarantee high cohesion, low coupling, and maintainability (NFR-02):

*   *controller.py*: Central orchestrator and execution loop. Governs system state, awaits presence triggers, delegates input reading, executes verification routines, dispatches actuator responses, and ensures event persistence.
*   *gpio_handler.py*: Hardware abstraction layer for GPIO operations. Handles pin initialization, pull-up input sensing, debouncing routines, LED indicator control, and motion sensor event loops.
*   *gui.py*: Presentation layer implemented in Tkinter. Shows the access screens (idle, face, code and key, result) and the administration screens (user list, registration, face enrollment, role change).
*   *validator.py*: Decoupled credential evaluation logic shared by every method: buttons, GUI, face and the mobile app. Classifies each attempt as authorized, denied (no permission or not recognized) or system error.
*   *db.py*: Persistence layer utilizing mysql.connector. Connects to the local database (control_acceso), checks credentials against their hashes, logs access attempts and events, and manages users, roles and face templates.
*   *camera.py*: Opens the USB camera, checks the quality of each frame and always releases the camera.
*   *face.py*: Local facial recognition with DeepFace: turns a camera frame, or a photo sent by the app, into an embedding and compares it with the stored templates (NFR-07). It never stores images (NFR-08).
*   *enrollment.py*: Guided registration of a new user and enrollment or re-enrollment of a face (FR-13).
*   *api_server.py*: HTTP API for the mobile app, in its own thread; it only orchestrates and reuses the modules above.
*   *bitacora.py*: Full event log (FR-23). Records everything the system does, not only access attempts: identifications, administration sessions and changes, technical failures, start and stop. Events are queued and written by a background thread into the `eventos` table, so an access never waits for the database; if the database is down they are retried, and each event has its own `evento_uid` so a retry never stores it twice.
*   *exit.py*: Actuation and output driver. Plays the access sounds on the USB speaker (found by name) and moves the servo with PWM.
*   *config.py*: Centralized configuration repository defining pin mappings, temporal constants, and system parameters without modifying business logic (FR-04).

## Mobile App

Integrativo 4 adds a mobile application as a new way to request access. It is meant for users only and works alongside the existing access methods (physical buttons, graphical interface and facial recognition), which keep working unchanged (NFR-10).

*   *Facial access first:* the app opens on the front camera. The photos go to the Raspberry Pi, which identifies the face and decides (FR-22). If the face is not recognized, no face is seen or facial recognition is not available, the app goes to the code and key form and says why; a recognized user without access gets the denial.
*   *Identification:* the user identifies themselves in the app with their user code and password (FR-15).
*   *Request after identifying:* the access request is enabled as soon as the user is identified. The app does not wait for the PIR sensor; the Raspberry Pi decides the result (FR-16).
*   *Result in the app:* the app shows whether access was authorized, denied, or could not be completed due to a technical condition. A technical failure is never shown as a denial (FR-17, FR-18, NFR-11).
*   *Return to the start:* when the operation ends, the app clears the entered data and returns to its initial state (FR-19).
*   *Same validation logic:* requests from the app are authorized by the same validation used by the other access methods; there is no separate authorization path for the app (FR-20).
*   *Administration not in the app yet:* NFR-09 now allows it for the roles that can manage or consult (FR-21), within a session (NFR-12), but it is not implemented: users, roles and faces are managed on the screen of the Raspberry Pi. The app never changes the system configuration.

The requirements are listed in `requirements.md` (FR-15 to FR-26, NFR-09 to NFR-14) and the screens in `docs/Interface_5.png` and `docs/Interface_6.png`. Those wireframes predate the facial access from the app (FR-22) and the request without presence (FR-16).

**Status:** implemented in Kotlin (`android/`), with the API on the Raspberry Pi in `src/api_server.py`. Tested on a PC; the run on the real Raspberry Pi and on a phone is tracked in `docs/verification_checklist.md` (PIC-107).

### How it works

The app is organized in three layers that do not mix:

| Layer | Classes | Responsibility |
| :--- | :--- | :--- |
| Interface | `FaceActivity`, `IdentificationActivity`, `RequestActivity`, `ResultActivity` | Show the views, take the photos and forward the taps |
| Logic | `AccessManager` | Who is identified, whether the request is enabled, the last result |
| Communication | `RaspberryClient` | HTTP requests to the Raspberry Pi, and nothing else |

The Raspberry Pi serves four routes, on port 8000 by default (`API_PUERTO` in `src/config.py`):

| Method | Route | Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/login` | Identify the user (FR-15) |
| `GET` | `/api/presence` | Has the PIR sensor detected presence? Still served, but the app no longer uses it (PIC-115) |
| `POST` | `/api/access` | Request access and receive the result (FR-17, FR-18) |
| `POST` | `/api/access/face` | Request access with up to three photos of the face (FR-22) |

`/api/access` calls `validator.verificar_usuario()` and then `controller.procesar_resultado()`, the same functions the other access methods use. `/api/access/face` identifies the photos with `face.identificar_imagenes()`, the same model and templates as the camera of the Raspberry Pi, then calls `validator.verificar_rostro()` and `controller.procesar_resultado()` with method `app_facial`. The photos are only decoded in memory and never stored (NFR-14). The API runs in its own thread next to the access cycle; if it cannot start, the system starts anyway and the other methods keep working.

### Installation

*   The app runs on the user's phone and sends its requests to the Raspberry Pi that runs this system, so the Raspberry Pi must be running and reachable from the phone.
*   No administration is done from the app yet; users, roles and faces are managed on the Raspberry Pi. A face used from the app must be enrolled there first.

| Step | How |
| :--- | :--- |
| Platform and SDK | Android 8.0 or newer on the phone. To build: JDK 17 or newer and the Android SDK (platform 35, build-tools 35.0.0), or Android Studio |
| Build | Open the `android/` folder in Android Studio, or run `./gradlew assembleDebug` inside it. The APK is written to `android/app/build/outputs/apk/debug/` |
| Deployment to the phone | Run the app from Android Studio with the phone connected by USB, or copy `app-debug.apk` to the phone and install it. The first time it asks for the camera; without it, the app still works with code and key |
| Connecting the app to the Raspberry Pi | Phone and Raspberry Pi on the same network. In the first view, tap **Conexión** and type the address of the Raspberry Pi, for example `192.168.1.50:8000` |

The API itself uses only the Python standard library; the facial access from the app uses the same OpenCV and DeepFace that the camera of the Raspberry Pi needs. It starts with the system (`python3 src/controller.py`) and can be turned off with `API_ACTIVA = False` in `src/config.py`.

### Tests

Inside `android/`:

```
./gradlew testDebugUnitTest
```

The tests run on the PC, without a phone: the logic and the HTTP client against a server that answers like the API, and the views with Robolectric. To check a real Raspberry Pi from the PC:

```
RASPBERRY_URL=http://<pi-address>:8000 RASPBERRY_USER_ID=<id> RASPBERRY_PIN=<key> ./gradlew testDebugUnitTest --tests "*LiveRaspberryTest*"
```

### Trying the app without the Raspberry Pi

`tools/simulated_api.py` serves the real `src/api_server.py` on a PC. Only the PIR sensor, the database, the facial recognition and the physical reaction are simulated, so the app gets the same answers it gets from the Raspberry Pi. From the repository root:

```
python tools/simulated_api.py
```

In the first view of the app, tap **Conexión** and type `10.0.2.2:8000` from the Android Studio emulator, or `<PC address>:8000` from a phone on the same Wi-Fi. While it runs, type `e` to toggle a database failure, `f` to change what the facial access answers (user 1, user 2, unknown face, no face, not available) and `q` to stop. `p` toggles the presence of the PIR sensor, which the app no longer needs.

| Code | Key | Result |
| :--- | :--- | :--- |
| 1 | 123 | `autorizado` |
| 2 | 456 | `denegado_sin_permiso` |
| any other | any | `denegado_no_reconocido` |

It never touches GPIO, the database or the access log. It does not replace the run on the real prototype (`docs/verification_checklist.md`).

### Known limitation

The code and key travel over plain HTTP on the local network. They are stored hashed in the database, but they are not encrypted in transit, and neither are the photos of the facial access. A session token is planned (NFR-12, PIC-110); HTTPS is not.

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
│   ├── class_diagram.md
│   ├── data.md
│   ├── dfd-0.md
│   ├── dfd-1.md
│   ├── flow.md
│   ├── sequence.md
│   ├── states.md
│   ├── system_architecture.md
│   ├── system_flowchart.md
│   ├── use_cases.md
│   └── verification_checklist.md
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
│       │   └── ui/          (camera, identification, request and result views)
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