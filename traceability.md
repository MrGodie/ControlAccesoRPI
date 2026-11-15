# Project Traceability

This document maps every requirement in `requirements.md` to the Jira issue that
covers it, the pull request that delivered it, and its verification status.

Jira project: **PIC** (ControlAccesoRPI) · Repository: `MrGodie/ControlAccesoRPI`

> **Note on verification.** The repository has no automated test suite yet; that
> work belongs to epic **PIC-1 (Integration & Testing)**. Until it exists, the
> "Test" column records how each requirement has actually been verified: manual
> verification on the prototype where it happened, or *pending* where it has not.

---

## 1. Functional requirements

| Requirement | Jira issue | PR | Test |
|---|---|---|---|
| **FR-01** Capture button presses in order and compare at the configured length | PIC-34, PIC-47, PIC-53, PIC-69 | #16, #49, #56, #79 | Manual on prototype (#79 fixed button detection under the GUI) |
| **FR-02** Display "Access granted" / "Access denied" | PIC-34, PIC-51 | #16, #54 | Manual on prototype |
| **FR-03** Reset capture state after showing the result | PIC-34, PIC-47 | #16, #49 | Manual on prototype |
| **FR-04** Key and sequence length configurable in one place | PIC-47 | #49 | Pending — `config.py` not yet exercised by a test |
| **FR-05** Per-press feedback without revealing the key or its length | PIC-34 | #16 | Manual on prototype |
| **FR-06** Detect presence with the PIR and move from idle to interaction | PIC-49 | #50 | Manual on prototype (configurable 10 s timeout) |
| **FR-07** Complete identification with buttons when the GUI is unavailable | PIC-53, PIC-60 | #56 | Manual on prototype |
| **FR-08** One shared validation path for both input methods | PIC-47, PIC-48 | #49, #51 | Pending |
| **FR-09** Log every attempt in MySQL with id, timestamp, method and outcome | PIC-48, PIC-18 | #51 | Pending — PIC-18 still in progress |
| **FR-10** Audible response and actuator activation on authorized access | PIC-52 | #53 | Manual on prototype (servo 2 s open, 0.5 s close) |
| **FR-11** Distinguish authorized / no permission / unknown credential / DB failure | PIC-50 | #52 | Manual on prototype (distinct LED pattern for system error) |
| **FR-12** Acquire images, detect and identify a face, then authorize accordingly | PIC-14, PIC-19, PIC-16, PIC-17, PIC-59 | #75 | Pending — only capture and quality validation are merged; recognition not implemented |
| **FR-13** Guided facial enrollment flow for the administrator | PIC-12, PIC-15, PIC-61 | #73 | Pending — wireframes merged, flow not implemented |
| **FR-14** Store the facial template with the user, deleted along with the user | PIC-9, PIC-10, PIC-11 | #70, #71 | Pending — schema merged, cascade delete not verified |

## 2. Non-functional requirements

| Requirement | Jira issue | PR | Test |
|---|---|---|---|
| **NFR-01** Debounce: one press never produces more than one record in 95% of trials | PIC-34, PIC-69 | #16, #79 | Pending — the 95% figure has not been measured |
| **NFR-02** Modular `src/`, any function locatable in under 2 minutes | PIC-47, PIC-54, PIC-55 | #49, #58, #62 | Manual review by the team (two review iterations) |
| **NFR-03** Display the result on screen | PIC-51 | #54 | Manual on prototype |
| **NFR-04** A DB failure is never reported or logged as "access denied" | PIC-50 | #52 | Manual on prototype (separate `error_sistema` result type) |
| **NFR-05** GUI, validation and data access as independent modules | PIC-47, PIC-48 | #49, #51 | Manual review by the team |
| **NFR-06** No credentials or secrets in plain text in the repository | PIC-48 | #51 | Pending — no automated check in CI |
| **NFR-07** Detection, identification, storage and decision run entirely locally | PIC-14, PIC-19 | #75 | Pending — holds for the merged camera module; recognition not implemented |
| **NFR-08** Store only the biometric template, never the captured images | PIC-11, PIC-19 | #70, #75 | Pending |

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
| Requirements document updated for facial recognition | PIC-25 | #69 |
| System architecture diagram | PIC-23 | #77 *(open)* |
| `flow.md` and `system_flowchart.md` with facial recognition | PIC-66, PIC-67 | #78 *(open)* |

## 4. Coverage gaps

Open items that keep requirements from being fully traceable:

- **No automated tests.** Epic PIC-1 has no test suite; every "pending" entry above
  depends on it.
- **Facial recognition not implemented.** PIC-16, PIC-17, PIC-59 and PIC-15 are in
  progress, so FR-12, FR-13, NFR-07 and NFR-08 are only partially covered by the
  merged camera module (#75).
- **`data.md` is outdated and not in English** (PIC-65, in progress).
- **README not yet updated** for this version (PIC-63).

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
| System architecture diagram | PIC-23 | #77 | docs/system_architecture.md with hardware, application modules and database. **Open**, approved by 1 reviewer. |
| Flow and system flowcharts with facial recognition | PIC-66, PIC-67 | #78 | docs/flow.md and docs/system_flowchart.md updated and translated to English. **Open**, approved by 1 reviewer. |
| Fixed buttons not detected under the GUI | PIC-69 | #79 | Physical buttons now register while the graphical interface is active. |
