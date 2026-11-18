# Verification checklist — Integrativo 4 (PIC-107)

What has to be shown on the real prototype, with a phone, to confirm that the mobile app works as a new access method and that the previous methods still work. Each row is filled in during the run: the result and where the evidence is (photo, video, screenshot or log query).

**Status: not run yet.** Everything below has only been tested on a PC with simulated hardware.

## Before starting

| # | Check | Result | Evidence |
| :--- | :--- | :--- | :--- |
| P1 | The system starts with `python3 src/controller.py` and prints `API de la app móvil escuchando en 0.0.0.0:8000` | | |
| P2 | The phone and the Raspberry Pi are on the same network, and the address of the Raspberry Pi is set in the app (**Conexión**) | | |
| P3 | There is one registered user with access and one without (inactive, or with a role without access) | | |

## A. Authorized access from the app

The twelve steps the project brief asks for, in its order.

| # | Step | Expected | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| A1 | The PIR sensor detects presence | The terminal prints `Presencia detectada` | | |
| A2 | The request is enabled in the app | After identifying, the button "Solicitar acceso" is enabled; the app does not wait for presence (PIC-115) | | |
| A3 | The user identifies themselves | The app shows "Hola, *name*" | | |
| A4 | The user requests access from the phone | The app shows "Enviando solicitud…" | | |
| A5 | The app communicates with the Raspberry Pi | The terminal prints `API <phone address> - "POST /api/access HTTP/1.1" 200 -` | | |
| A6 | The user and their permissions are validated | The result is `autorizado` | | |
| A7 | The result is shown in the app | Green view "Acceso autorizado" | | |
| A8 | The LED turns on | Green LED on | | |
| A9 | The motor is activated | The servo opens and closes | | |
| A10 | The speaker plays the success message | `exito.wav` is heard | | |
| A11 | The operation is logged | A new row in `intentos_acceso` with `metodo = 'app'` and `resultado = 'autorizado'` | | |
| A12 | The system goes back to its initial state | The app returns to an empty form; the Raspberry Pi returns to the idle screen | | |

Query for A11 and B4:

```sql
SELECT id, usuario_id, metodo, resultado, fecha_hora
FROM intentos_acceso ORDER BY id DESC LIMIT 5;
```

## B. Denied access from the app

| # | Step | Expected | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| B1 | A user without access identifies themselves and requests access | The app shows the red view "Acceso rechazado" | | |
| B2 | The motor | Does **not** move | | |
| B3 | LED and speaker | Red LED and `error.wav` | | |
| B4 | The attempt is logged | A new row with `metodo = 'app'` and `resultado = 'denegado_sin_permiso'` | | |
| B5 | A wrong code or key on the form | "Código o clave incorrectos.", the same message for either field | | |

## C. Technical failure is not a denial

| # | Step | Expected | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| C1 | Stop the database (`sudo systemctl stop mariadb`) and request access | Amber view "No se pudo completar"; red LED blinks; the motor does not move | | |
| C2 | Turn off the Wi-Fi of the phone on the request view and tap "Solicitar acceso" | Amber view "No se pudo completar": "No hubo respuesta del punto de acceso. Tu acceso no fue rechazado…" | | |
| C3 | Start the database again and repeat A | Works as before | | |

## D. The previous access methods still work

With the API running. Each one must behave as it did before Integrativo 4.

| # | Method | Expected | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| D1 | Graphical interface (code and key), authorized | Green LED, sound, motor, row with `metodo = 'gui'` | | |
| D2 | Graphical interface, denied | Red LED, sound, no motor, row with `metodo = 'gui'` | | |
| D3 | Facial recognition, authorized | Green LED, sound, motor, row with `metodo = 'facial'` | | |
| D4 | Physical buttons (system started without a screen), authorized | Green LED, sound, motor, row with `metodo = 'botones'` | | |
| D5 | The system starts with the API turned off (`API_ACTIVA = False`) | It starts and D1 works | | |
| D6 | An access from the app while the graphical interface is showing a result | The two reactions happen one after the other, never at the same time | | |

## E. Facial access from the app (FR-22)

| # | Step | Expected | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| E1 | A user with a registered face opens the app and taps "Entrar con rostro" | Green view "Acceso autorizado" with their name; LED, sound and motor as in A | | |
| E2 | The attempt is logged | A new row in `intentos_acceso` with `metodo = 'app_facial'` | | |
| E3 | A person without a registered face tries | The app goes to the form with "No te reconocimos. Usa tu código y clave."; no LED, no motor | | |
| E4 | Cover the camera and try | The form with "No se detectó tu rostro. Usa tu código y clave." | | |
| E5 | A registered face of a user without access | Red view "Acceso rechazado"; the app does not offer the code and key | | |
| E6 | The photos are not kept | No new files on the phone's gallery or on the Raspberry Pi | | |

## Notes for the run

- The person with the phone also triggers the access cycle of the Raspberry Pi, because the PIR starts both. If that person has a registered face, the facial recognition can open the door before the app does. Decide beforehand who stands in front of the camera, or run A with `RECONOCIMIENTO_ACTIVO = False`.
- The project brief describes presence first and identification second. Since PIC-115 the app does not depend on presence, so the PIR step (A1) only starts the cycle of the Raspberry Pi; the demonstration can still follow the order of the brief.
- The code and key travel over plain HTTP on the local network. It is a known limitation, to be mentioned in the presentation.
