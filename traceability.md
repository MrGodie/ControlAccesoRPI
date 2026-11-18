# Project Traceability

This document maps every requirement in `requirements.md` to the Jira issue that
covers it, the pull request that delivered it, and its verification status.

Jira project: **PIC** (ControlAccesoRPI) · Repository: `MrGodie/ControlAccesoRPI`

> **Note on verification.** The mobile app has automated unit and screen tests
> (`android/app/src/test`, run with `./gradlew testDebugUnitTest`). The Python
> code on the Raspberry Pi has no test suite in the repository yet; that work
> belongs to epic **PIC-1 (Integration & Testing)**. The "Test" column records
> how each requirement has actually been verified: automated, manual on the
> prototype, by inspection, or *pending* where it has not.

---

## 1. Functional requirements

| Requirement | Jira issue | PR | Test |
|---|---|---|---|
| **FR-01** Capture button presses in order and compare at the configured length | PIC-34, PIC-47, PIC-53, PIC-69 | #16, #49, #56, #79 | Manual on prototype (#79 fixed button detection under the GUI) |
| **FR-02** Display "Access granted" / "Access denied" | PIC-34, PIC-51 | #16, #54 | Manual on prototype |
| **FR-03** Reset capture state after showing the result | PIC-34, PIC-47 | #16, #49 | Manual on prototype |
| **FR-04** Key and sequence length configurable in one place | PIC-47 | #49 | Pending — `config.py` not yet exercised by a test |
| **FR-05** Per-press feedback without revealing the key or its length | PIC-34 | #16 | Manual on prototype |
| **FR-06** Detect presence with the PIR and move from idle to interaction | PIC-49 | #50 | Manual on prototype (configurable timeout, `TIEMPO_ESPERA_PRESENCIA`, 30 s by default) |
| **FR-07** Complete identification with buttons when the GUI is unavailable | PIC-53, PIC-60 | #56 | Manual on prototype |
| **FR-08** One shared validation path for both input methods | PIC-47, PIC-48 | #49, #51 | Pending |
| **FR-09** Log every attempt in MySQL with id, timestamp, method and outcome | PIC-48, PIC-18 | #51 | Pending — implemented (`db.registrar_intento`, method `gui`, `botones`, `facial`, `app` or `app_facial`); no recorded verification on the prototype |
| **FR-10** Audible response and actuator activation on authorized access | PIC-52, PIC-76, PIC-79, PIC-82 | #53, #91, #95, #96, #97 | Manual on prototype (servo 2 s open, 0.5 s close); audio through the USB speaker (#91, #96, #97) has no recorded verification yet |
| **FR-11** Distinguish authorized / no permission / unknown credential / DB failure | PIC-50, PIC-78, PIC-79 | #52, #92, #95 | Manual on prototype (distinct LED pattern for system error) |
| **FR-12** Acquire images, detect and identify a face, then authorize accordingly | PIC-14, PIC-19, PIC-16, PIC-17, PIC-59, PIC-68, PIC-71, PIC-72, PIC-73 | #75, #82, #84, #85, #86, #90 | Pending — implemented (`src/face.py` identifies against the stored templates; `controller.intento_facial` authorizes through `validator.verificar_rostro`), no recorded verification |
| **FR-13** Guided facial enrollment flow for the administrator | PIC-12, PIC-15, PIC-61, PIC-70, PIC-71, PIC-75, PIC-80 | #73, #83, #84, #88, #94 | Pending — flow implemented in `src/enrollment.py` (new users, and existing users since #94), no recorded verification |
| **FR-14** Store the facial template with the user, deleted along with the user | PIC-9, PIC-10, PIC-11, PIC-74, PIC-77 | #70, #71, #87, #89 | Pending — `ON DELETE CASCADE` is declared in `schema.sql` and `migration.sql`; cascade delete not verified |
| **FR-15** Identify the user from the mobile application | PIC-105, PIC-97, PIC-102, PIC-100, PIC-88 | #104, #105, #106, #107 | Automated on a PC (`/api/login` over HTTP; `AccessManagerTest`, `ScreensTest`): a wrong code and a wrong key give the same answer; pending on the real Raspberry Pi and on a phone (PIC-107) |
| **FR-16** Enable the mobile access request as soon as the user is identified, without waiting for the PIR | PIC-105, PIC-97, PIC-100, PIC-89, PIC-115 | #102, #104, #106, #107, #113 | Changed in PIC-115: the app no longer asks for presence. Automated on a PC (`AccessManagerTest`, `ScreensTest`: the button is enabled after identifying and `/api/presence` is never called); pending on a phone (PIC-107) |
| **FR-17** Send the access request from the app and receive the result there | PIC-105, PIC-97, PIC-100, PIC-89 | #103, #104, #106, #107 | Automated on a PC: the Kotlin client against the Python API with simulated hardware (authorized request moves the motor and is logged as `app`); pending on the real Raspberry Pi and on a phone (PIC-107) |
| **FR-18** App distinguishes authorized / denied / not completed for a technical condition | PIC-105, PIC-100, PIC-89 | #106, #107 | Automated on a PC (`ModelTest`, `RaspberryClientTest`, `ScreensTest`); pending on the real Raspberry Pi and on a phone (PIC-107) |
| **FR-19** App returns to its initial state when the operation ends | PIC-105, PIC-100, PIC-89 | #106, #107 | Automated on a PC (`AccessManager.reset()`; result view closes by itself and the form comes back empty in `ScreensTest`); pending on a phone (PIC-107) |
| **FR-20** Same validation logic for the app as for the existing access methods | PIC-105, PIC-97, PIC-111 | #104, #114 | By inspection: `src/api_server.py` calls `validator.verificar_usuario()` (code and key) or `validator.verificar_rostro()` (face) and has no permission check of its own; automated on a PC with the real `validator` and `controller` |
| **FR-21** User management from the app with the same role capabilities as the GUI | PIC-108, PIC-90, PIC-99, PIC-112, PIC-114 | #110, #112 | Pending — not implemented in the app. The GUI can change a user's role since PIC-114 (`db.cambiar_rol`), tested on a PC against a throwaway MySQL |
| **FR-22** Facial access from the app with the phone camera, decided on the Raspberry Pi | PIC-108, PIC-111 | #110, #114 | Pending — implemented in PIC-111 (`POST /api/access/face`, `face.identificar_imagenes`, `FaceActivity`). Automated on a PC: the API with the real `face.py` and a simulated model; the app with `AccessManagerTest`, `RaspberryClientTest` and `ScreensTest`. Not yet run on the Raspberry Pi or on a phone |
| **FR-23** Log every relevant event, not only access attempts | PIC-108, PIC-109 | #110, #111 | Pending — implemented in #111 (`src/bitacora.py`, table `eventos`), tested on a PC against a throwaway MySQL; not yet run on the Raspberry Pi |
| **FR-24** Without connection the app never reports access as authorized and disables administration | PIC-108, PIC-113 | #110 | Pending — not implemented |
| **FR-25** Events produced without connection are queued on the phone and synced once | PIC-108, PIC-113 | #110 | Pending — not implemented |
| **FR-26** View the log from the GUI and from the app | PIC-108, PIC-93, PIC-99 | #110 | Pending — not implemented |

## 2. Non-functional requirements

| Requirement | Jira issue | PR | Test |
|---|---|---|---|
| **NFR-01** Debounce: one press never produces more than one record in 95% of trials | PIC-34, PIC-69 | #16, #79 | Pending — the 95% figure has not been measured |
| **NFR-02** Modular `src/`, any function locatable in under 2 minutes | PIC-47, PIC-54, PIC-55 | #49, #58, #62 | Manual review by the team (two review iterations) |
| **NFR-03** Display the result on screen | PIC-51 | #54 | Manual on prototype |
| **NFR-04** A DB failure is never reported or logged as "access denied" | PIC-50 | #52 | Manual on prototype (separate `error_sistema` result type) |
| **NFR-05** GUI, validation and data access as independent modules | PIC-47, PIC-48 | #49, #51 | Manual review by the team |
| **NFR-06** No credentials or secrets in plain text in the repository | PIC-48 | #51 | Pending — no automated check in CI |
| **NFR-07** Detection, identification, storage and decision run entirely locally | PIC-14, PIC-19, PIC-68 | #75, #82 | Pending — `src/face.py` runs DeepFace on the Raspberry Pi (the model weights are downloaded once); not verified |
| **NFR-08** Store only the biometric template, never the captured images | PIC-11, PIC-19, PIC-70 | #70, #75, #83 | Pending — the access and enrollment flows write no image to disk (only the manual `camera.py` self-test saves a frame, when run with `--guardar`); not verified |
| **NFR-09** Administration in the app only for allowed roles, only connected, only within a session; never the system configuration | PIC-105, PIC-97, PIC-89, PIC-108 | #104, #107, #110 | Pending — requirement changed to allow administration (FR-21). The previous wording (no administration at all) was verified by inspection in #104 and #107 |
| **NFR-10** The existing access methods keep working unchanged | PIC-105, PIC-97, PIC-107 | #102, #103, #104 | Automated on a PC: `procesar_resultado()` runs the same outputs in the same order for each result; the system starts when the API cannot. Pending on the prototype: one access by GUI, buttons and face (PIC-107) |
| **NFR-11** A technical failure in the app is never reported or logged as "access denied" | PIC-105, PIC-97, PIC-100, PIC-89 | #104, #106, #107 | Automated on a PC: database down, Raspberry Pi unreachable, no answer in time and unknown answers are reported as a technical failure; pending on the real Raspberry Pi and on a phone (PIC-107) |
| **NFR-12** Credential sent once; session token that expires; every admin request re-checked on the Raspberry Pi | PIC-108, PIC-110 | #110 | Pending — not implemented |
| **NFR-13** The phone never stores credentials, templates, images or the user list; only pending events | PIC-108, PIC-113 | #110 | Pending — not implemented |
| **NFR-14** Face images from the phone are only processed on the Raspberry Pi and discarded | PIC-108, PIC-111 | #110 | By inspection (PIC-111): the photos are decoded in memory (`face.decodificar_imagen`) and never written to disk, on the phone or on the Raspberry Pi |

## 3. Design and documentation artifacts

| Artifact | Jira issue | PR |
|---|---|---|
| ER diagram with biometric data | PIC-10 | #71 |
| MySQL schema extended for biometric data | PIC-11 | #70 |
| Facial enrollment wireframe | PIC-12 | #73 |
| Authentication and status wireframe | PIC-20 | #74 |
| User and access management wireframe | PIC-21 | #74 |
| BPMN process with facial authentication | PIC-13 | #72, #76 |
| DFD level 0 and level 1 | PIC-22 | #76 |
| Sequence and state diagrams | PIC-24, PIC-58 | #76 |
| Use case and class diagrams for the mobile app | PIC-96 | #98 |
| Mobile app wireframes | PIC-101 | #100 |
| Verification checklist for the prototype and the phone | PIC-107 | #108 |
| Requirements document updated for facial recognition | PIC-25 | #69 |
| System architecture diagram | PIC-23 | #77 |
| `flow.md` and `system_flowchart.md` with facial recognition | PIC-66, PIC-67 | #78 |

## 4. Coverage gaps

Open items that keep requirements from being fully traceable:

- **No automated tests for the Raspberry Pi code.** Epic PIC-1 has no test suite
  for `src/`; the mobile app has its own tests. Most "pending" entries above
  depend on a run on the prototype.
- **Facial recognition implemented but not verified.** `face.py` (#82) and
  `enrollment.py` (#83) are merged, so FR-12, FR-13, NFR-07 and NFR-08 are
  implemented; none of them has a recorded verification yet.
- **Mobile application implemented but not verified on the device.** FR-15 to
  FR-20 and NFR-09 to NFR-11 (Integrativo 4) are implemented (#102 to #107) and
  tested on a PC with simulated hardware. None of them has a recorded run on the
  real Raspberry Pi or on a phone yet; `docs/verification_checklist.md` (PIC-107)
  lists what has to be shown. PIC-107 is marked as done in Jira, but the
  checklist has not been filled in.
- **Mobile application, second stage in progress.** FR-21 to FR-26 and
  NFR-12 to NFR-14 (administration, facial access and full log from the app,
  with offline queue) are specified in #110 (PIC-108). Implemented so far:
  the full event log (FR-23, #111), the role change on the GUI that FR-21 will
  mirror (#112), and the facial access from the app (FR-22, NFR-14, #114).
  The rest is planned in PIC-90, PIC-93, PIC-99, PIC-110, PIC-112 and PIC-113.
  NFR-09 was changed to allow administration from the app.
- **FR-16 changed (PIC-115, #113).** The app no longer waits for PIR presence.
  The project brief lists presence as the first step of the access from the
  app, so the change still has to be confirmed with the professor.
- **FR-01 and FR-04 disagree with the configuration.** FR-01 asks for a key of
  4 to 6 presses and FR-04 mentions a length of 3; `LONGITUD_CLAVE` in
  `config.py` is 3.
- **PIC-98 (login lockout) was reopened.** It was marked as done, but there is
  no lockout logic in the code.

---

## 5. Change log

Chronological record of the work merged into the repository. Issue numbers before
the Jira migration (PIC-7, PR #7) refer to GitHub issues.

| Change | Issue | PR | Validation evidence |
|---|---|---|---|
| Base documentation (README/requirements) | #1 · PIC-28 | #2 | Added problem description, features, and initial structure to README.md and requirements.md. Approved by ArantzaJQ. |
| Flowchart | #3 · PIC-29 | #5 | Added docs/flow.md with a Mermaid diagram of the key capture and validation flow. Approved and merged. |
| README translation | #4 · PIC-30 | #6 | README.md fully translated into English for repository consistency. Approved by ArantzaJQ. |
| RF-04, RF-05, NFR-03 | *none* | #8 | Completed the missing RF/NFR items in requirements.md and added the GPIO pin assignment table to README.md. |
| Project traceability | #7 · PIC-31 | #9 | Created and populated traceability.md with the full mapping between requirements, issues, PRs, and validation evidence. |
| Add src folder | #10 · PIC-32 | #12 | The src folder will contain the code that interacts with the prototype. |
| Add missing flowcharts | #11 · PIC-33 | #13 | Added context, subprocess, and system flow diagrams. |
| Add code to controller.py | #14 · PIC-34 | #16 | Added the initial version of the controller code; testing will be required to determine future modifications. |
| Added the missing teammates names | *none* | #17 | The section that lists the names of the members of our team was completed. |
| Fixed the code by request of the hardware team | *none* | #18 | Code fixed according to the changes made by the hardware team. |
| Fixed the README.md again | *none* | #19 | Several sections of the README.md had incomplete or wrong information. |
| Debugging of controller due to connection issues with Raspberry | #20 · PIC-36 | #22 | Changes to controller.py due to errors within it. Merged after extensive testing (10 days in review). |
| Updated and translated the traceability.md | #15 · PIC-35 | #21 | Updated the document with the missing changes, as well as translating it. Approved by 2 reviewers. |
| Added the new FR and NFR (V2) | #24 · PIC-37 | #31 | First commit of the new flowcharts for the V2 of the project. Approved by 2 reviewers (20 sep). |
| Added BPMN process | #26 · PIC-39 | #30 | First new flowchart for the project evolution to V2. Approved by 2 reviewers. |
| Add sequence and states flowcharts | #28 · PIC-41 | #32 | Adds docs/states.md and docs/sequence.md with Mermaid diagrams for this version. Approved by 2 reviewers. |
| Add design low fidelity wireframes | #25 · PIC-38 | #45 | Wireframes for the main screens (waiting, identification, result) and their navigation. Approved by 2 reviewers. |
| Added the data flowchart and schema for MySQL | #27 · PIC-40 | #46 | Data flowchart and schema for MySQL database design. Approved by 2 reviewers. |
| Updated DFD-0 (context diagram) | #34 · PIC-43 | #47 | Updated docs/dfd-0.md with refined context diagram for V2. Approved by 2 reviewers. |
| Updated DFD-1 (system diagram) | #35 · PIC-44 | #48 | Updated docs/dfd-1.md with refined system decomposition diagram. Approved by 1 reviewer. |
| Updated flow.md with new requirements | #36 · PIC-45 | #57 | Updated docs/flow.md according to new FR/NFR specifications for V2. Approved by 2 reviewers. |
| Refactor: Divided controller.py into modules | #38 · PIC-47 | #49 | Created modular architecture: controller.py, gpio_handler.py, validator.py, gui.py, db.py, exit.py. Approved by 2 reviewers. |
| Create database module and update validator | #39 · PIC-48 | #51 | Implemented db.py module with MySQL connection pooling and SHA2 hash validation. Approved by 1 reviewer. |
| Integrate PIR sensor for presence detection | #40 · PIC-49 | #50 | Implemented PIR sensor integration in gpio_handler.py with configurable timeout (10s). Approved by 1 reviewer. |
| Add system fail message | #41 · PIC-50 | #52 | Added error_sistema result type; LED red blink pattern differentiates from access denied. Approved by 1 reviewer. |
| Create graphical interface (GUI) | #42 · PIC-51 | #54 | Implemented Tkinter GUI (gui.py) for credential input; auto-hidden if DISPLAY unavailable. Approved by 1 reviewer. |
| Add audio output and physical actuator activation | #43 · PIC-52 | #53 | Implemented exit.py with servo PWM control and buzzer tone generation; 2s open, 0.5s close, silence. Approved by 1 reviewer. |
| Fix modules structure (iteration 1) | #55 · PIC-54 | #58 | Fixed import paths and module initialization after refactor. Approved by 2 reviewers. |
| Implement module changes into controller.py | *none* | #56 | Integrated all module updates into orchestration logic. Approved by 1 reviewer. |
| Fix modules structure (iteration 2) | #59 · PIC-55 | #62 | Second round of module fixes for import and initialization issues. Approved by 1 reviewer. |
| Fix schema and migration file | #60 · PIC-56 | #61 | Fixed database/schema.sql and added migration support. Approved by 1 reviewer. |
| Fix schema and migration (final) | #60 · PIC-56 | #63 | Final corrections to schema.sql and migration file. Labeled as "invalid" (technical debt tag). Approved by 1 reviewer. |
| Completed the traceability file | #15 · PIC-35 | #64 | Filled in the entries missing from traceability.md. |
| Updated requirements and README to V2 | #29 · PIC-42 | #65 | requirements.md and README.md brought in line with the V2 scope. |
| Fixed the GUI to align with the wireframes | #66 · PIC-57 | #68 | gui.py adjusted so the screens match docs/Interface.png. |
| Update requirements for facial recognition | PIC-25 | #69 | Added FR-12, FR-13, FR-14, NFR-07 and NFR-08 to requirements.md. |
| Extended the MySQL schema and database | PIC-11 | #70 | Schema extended with the biometric data table, linked to users. |
| ER diagram updated | PIC-10 | #71 | docs/data.md updated with biometric data and authentication method. |
| Updated BPMN process flow | PIC-13 | #72 | docs/bpmn-process.md rewritten for the facial authentication flow, in English. |
| Facial enrollment wireframes | PIC-12 | #73 | docs/Interface_2.png: eight screens for the guided enrollment flow. Approved by 1 reviewer. |
| Authentication and management wireframes | PIC-20, PIC-21 | #74 | docs/Interface_3.png and docs/Interface_4.png, same grid and style as the previous sheets. Approved by 1 reviewer. |
| Camera module created and integrated | PIC-19 | #75 | src/camera.py with capture, quality validation and guaranteed release; the system still starts without a camera. Approved by 1 reviewer. |
| Updated the original flowcharts | PIC-22, PIC-24, PIC-58 | #76 | docs/dfd-0.md, dfd-1.md, sequence.md and states.md updated for facial recognition and translated to English. Approved by 1 reviewer. |
| System architecture diagram | PIC-23 | #77 | docs/system_architecture.md with hardware, application modules and database. Approved by 2 reviewers. |
| Flow and system flowcharts with facial recognition | PIC-66, PIC-67 | #78 | docs/flow.md and docs/system_flowchart.md updated and translated to English. Approved by 2 reviewers. |
| Fixed buttons not detected under the GUI | PIC-69 | #79 | Physical buttons now register while the graphical interface is active. |
| Traceability mapped per requirement | PIC-64 | #80 | traceability.md rewritten to map every requirement to its Jira issue, PR and test. Approved by 2 reviewers. |
| Updated and fixed data.md | PIC-65 | #81 | docs/data.md corrected and updated. Approved by 1 reviewer. |
| GUI updated to the new wireframes, face module added | PIC-68 | #82 | src/face.py created; gui.py, controller.py, validator.py and config.py updated for facial authentication. Approved by 1 reviewer. |
| Enrollment module added | PIC-70 | #83 | src/enrollment.py created and wired into controller.py, gui.py, db.py and config.py. Approved by 1 reviewer. |
| User management page added | PIC-71 | #84 | Fixed the user management button and the relationships between controller.py, enrollment.py, face.py and gui.py. Approved by 1 reviewer. |
| Fixed the user interface logic | PIC-72 | #85 | controller.py, db.py and gui.py adjusted. Approved by 1 reviewer. |
| Fixed the camera configuration | PIC-73 | #86 | config.py corrected for the camera. Approved by 1 reviewer. |
| App account granted access to the biometric tables | PIC-74 | #87 | migration.sql grants the application's database account access to the biometric tables. Approved by 2 reviewers. |
| GUI aligned with the enrollment flow | PIC-75 | #88 | gui.py matches the interface expected by the enrollment module. Approved by 1 reviewer. |
| Biometric functions restored in the database module | PIC-77 | #89 | The biometric functions of db.py were restored. Approved by 1 reviewer. |
| OpenCV backend for the USB camera | PIC-73 | #90 | config.py selects the OpenCV backend for the USB camera. Approved by 1 reviewer. |
| Access sounds through the USB speaker | PIC-76 | #91 | exit.py plays the sounds through the USB speaker; added setup_audio.sh and sounds/. Approved by 1 reviewer. |
| Role set replaced with declared capabilities | PIC-78 | #92 | Roles declare their capabilities in the schema and migration; controller.py, db.py, gui.py and validator.py use them. Approved by 2 reviewers. |
| Duplicate roles cleaned before the unique index | PIC-81 | #93 | migration.sql removes duplicate roles before adding the unique index. Approved by 2 reviewers. |
| Face enrollment for existing users | PIC-80 | #94 | An administrator can enroll the face of a user who already exists. Approved by 1 reviewer. |
| Fixed LEDs and audio not being called | PIC-79 | #95 | controller.py and exit.py now trigger the LEDs and sounds; added sounds/fallo.wav. Approved by 2 reviewers. |
| USB speaker found by name | PIC-82 | #96 | exit.py finds the USB speaker by name instead of a fixed card number. Approved by 2 reviewers. |
| New team access sounds | PIC-82 | #97 | sounds/ replaced with the team's new sounds; error and fallo are repeated. Approved by 2 reviewers. |
| Use case and class diagrams for the mobile app | PIC-96 | #98 | docs/use_cases.md and docs/class_diagram.md; mobile app in the other diagrams. Approved by 2 reviewers. |
| Mobile app requirements and traceability | PIC-105 | #99 | FR-15 to FR-20 and NFR-09 to NFR-11 added; traceability updated. Approved by 2 reviewers. |
| Mobile app wireframes | PIC-101 | #100 | docs/Interface_5.png and docs/Interface_6.png. Approved by 2 reviewers. |
| Mobile app in the README | PIC-106 | #101 | README.md describes the mobile app and its installation. Approved by 2 reviewers. |
| Non-blocking PIR presence check | PIC-97 | #102 | gpio_handler.presencia_reciente() for the API, without blocking the access cycle. |
| Physical outputs one at a time | PIC-97 | #103 | controller.procesar_resultado() runs LEDs, sound and servo under a lock, so two methods never react at once. Approved by 1 reviewer. |
| HTTP API for the mobile app | PIC-97 | #104 | src/api_server.py with /api/login, /api/presence and /api/access, in its own thread. Approved by 2 reviewers. |
| Android project in Kotlin | PIC-102 | #105 | android/ project, build and test setup. Approved by 1 reviewer. |
| Shared layer of the mobile app | PIC-100 | #106 | Model, AccessManager and RaspberryClient, with unit tests. Approved by 1 reviewer. |
| Three views of the mobile app | PIC-88, PIC-89 | #107 | Identification, request and result views, with Robolectric tests. Approved by 2 reviewers. |
| Mobile app documentation aligned with the code | PIC-107 | #108 | README, diagrams and docs/verification_checklist.md. Approved by 1 reviewer. |
| Simulated API to try the app without the Raspberry Pi | *none* | #109 | tools/simulated_api.py serves the real api_server.py with simulated hardware and test users. Approved by 1 reviewer. |
| Requirements for the second stage of the app | PIC-108 | #110 | FR-21 to FR-26 and NFR-12 to NFR-14; NFR-09 allows administration from the app. Approved by 2 reviewers. |
| Full event log | PIC-109 | #111 | src/bitacora.py and table eventos: every event, queued and written by a background thread. Approved by 1 reviewer. |
| Role change from the GUI | PIC-114 | #112 | db.cambiar_rol(); the last active user that can manage cannot lose that role; event cambio_rol. Approved by 1 reviewer. |
| The app no longer waits for PIR presence | PIC-115 | #113 | FR-16 changed; the request is enabled right after identifying. |
