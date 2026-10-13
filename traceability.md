# Trazabilidad del Proyecto

| Requeriment | Issue | PR | Validation evidence |
|---|---|---|---|
| Base documentation (README/requirements) | #1 | #2 | Added problem description, features, and initial structure to README.md and requirements.md. Approved by ArantzaJQ. |
| Flowchart | #3 | #5 | Added docs/flow.md with a Mermaid diagram of the key capture and validation flow. Approved and merged. |
| README translation | #4 | #6 | README.md fully translated into English for repository consistency. Approved by ArantzaJQ. |
| RF-04, RF-05, NFR-03 | *none* | #8 | Completed the missing RF/NFR items in requirements.md and added the GPIO pin assignment table to README.md. |
| Project traceability | #7 | #9 | Created and populated traceability.md with the full mapping between requirements, issues, PRs, and validation evidence. |
| Add src folder | #10 | #12 | The src folder will contain the code that interacts with the prototype. |
| Add missing flowcharts | #11 | #13 | Added context, subprocess, and system flow diagrams. |
| Add code to controller.py | #14 | #16 | Added the initial version of the controller code; testing will be required to determine future modifications. |
|Added the missing teamates names| *none* | #17 | The section that list the names of the members of our team was completed|
|Fixed the code by request of the hardware team| *none* | #18 | Code fixed accordingly to the changes made by the hardware team|
|Fixed the README.md again- #19| *none* | #19 | Several sections of the README.md had incompleted or wrongfull information|
| Debugging of controller due to connection issues with Raspberry | #20 | #22 | Changes to controller.py document due to errors within it. Merged after extensive testing (10 days in review). |
| Updated and translated the traceability.md | none | #21 | Updated the document with the missing changes, as well as translating it. Approved by 2 reviewers. |
| Added the new FR and NFR (V2) | #24 | #31 | First commit of the new flowcharts for the V2 of the project. Approved by 2 reviewers (20 sep). |
| Added BPMN process | #26 | #30 | First new flowchart for the project evolution to V2. Approved by 2 reviewers. |
| Add sequence and states flowcharts | #28 | #32 | Adds docs/states.md and docs/sequence.md with Mermaid diagrams for this version. Approved by 2 reviewers. |
| Add design low fidelity wireframes | #25 | #45 | Wireframes for the main screens (waiting, identification, result) and their navigation. Approved by 2 reviewers. |
| Added the data flowchart and schema for MySQL | #27 | #46 | Data flowchart and schema for MySQL database design. Approved by 2 reviewers. |
| Updated DFD-0 (context diagram) | #34 | #47 | Updated docs/dfd-0.md with refined context diagram for V2. Approved by 2 reviewers. |
| Updated DFD-1 (system diagram) | #35 | #48 | Updated docs/dfd-1.md with refined system decomposition diagram. Approved by 1 reviewer. |
| Updated flow.md with new requirements | #36 | #57 | Updated docs/flow.md according to new FR/NFR specifications for V2. Approved by 2 reviewers. |
| Refactor: Divided controller.py into modules | #38 | #49 | Created modular architecture: controller.py, gpio_handler.py, validator.py, gui.py, db.py, exit.py. Approved by 2 reviewers. |
| Create database module and update validator | #39 | #51 | Implemented db.py module with MySQL connection pooling and SHA2 hash validation. Approved by 1 reviewer. |
| Integrate PIR sensor for presence detection | #40 | #50 | Implemented PIR sensor integration in gpio_handler.py with configurable timeout (10s). Approved by 1 reviewer. |
| Add system fail message | #41 | #52 | Added error_sistema result type; LED red blink pattern differentiates from access denied. Approved by 1 reviewer. |
| Create graphical interface (GUI) | #42 | #54 | Implemented Tkinter GUI (gui.py) for credential input; auto-hidden if DISPLAY unavailable. Approved by 1 reviewer. |
| Add audio output and physical actuator activation | #43 | #53 | Implemented exit.py with servo PWM control and buzzer tone generation; 2s open, 0.5s close, silence. Approved by 1 reviewer. |
| Fix modules structure (iteration 1) | #55 | #58 | Fixed import paths and module initialization after refactor. Approved by 2 reviewers. |
| Implement module changes into controller.py | none | #56 | Integrated all module updates into orchestration logic. Approved by 1 reviewer. |
| Fix modules structure (iteration 2) | #59 | #62 | Second round of module fixes for import and initialization issues. Approved by 1 reviewer. |
| Fix schema and migration file | #60 | #61 | Fixed database/schema.sql and added migration support. Approved by 1 reviewer. |
| Fix schema and migration (final) | #60 | #63 | Final corrections to schema.sql and migration file. Labeled as "invalid" (technical debt tag). Approved by 1 reviewer. |
