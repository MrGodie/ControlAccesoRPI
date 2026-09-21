# Functional Requirements (FR)

FR-01. The system shall capture each press of the physical buttons connected to the GPIO inputs, store it in order as part of the entered sequence, and automatically compare it against the configured valid key as soon as the defined length is reached (between 4 and 6 presses).

FR-02. The system shall display the message "Access granted" on the terminal when the captured sequence exactly matches the valid key, or "Access denied" otherwise.

FR-03. The system shall reset the capture state (clear the stored sequence) immediately after displaying the result, allowing a new attempt without restarting the program.

FR-04. The system shall allow the valid key and the required sequence length (4 to 6 presses) to be modified by editing a single configuration variable or data structure in the source code, without requiring changes to the input-reading or comparison logic.

FR-05. The system shall provide immediate terminal feedback confirming that each individual press has been registered, without revealing the configured valid key, the required sequence length, or the number of presses captured so far.

FR-06. The system shall detect human presence via the PIR sensor and transition from an idle state to an active interaction state; subsequently, it shall display a graphical interface allowing the user to enter their identification credentials.

FR-07. When the graphical interface or monitor is unavailable, the system shall allow the user to complete identification and validation using only physical buttons, generating the same result categories (authorized/denied) as the graphical method.

FR-08. The system shall use the same validation logic to evaluate access attempts, regardless of whether the identification was entered via the graphical interface or physical buttons, without employing separate or duplicate authorization paths.

FR-09. The system shall log every access attempt in a MySQL database, whether access is granted or denied. The log entry shall include the identifier used, the timestamp, the interaction method (graphical interface or physical buttons), and the resulting outcome.

FR-10. The system shall issue an audible response (e.g., a voice message or a tone indicating "Access granted") and activate a physical actuator (e.g., a servomotor, relay, or equivalent) to signify the opening or authorization of access whenever an attempt is authorized.

FR-11. The system shall distinguish—both in its user response and in the stored log—between the following outcomes: access authorized, access denied due to insufficient permissions, access denied due to unrecognized credentials, and inability to complete validation due to a database connection failure.

# Non-Functional Requirements (NFR)

NFR-01. The system shall implement a debounce technique such that a single physical press does not generate more than one record in 95% of the test presses performed.

NFR-02. The source code shall be organized in the src/ directory following a modular structure (e.g., separation between input reading, validation logic, and output of results), such that a team member other than the author can locate each function in under 2 minutes.

NFR-03. The system shall display the result ("Access granted" / "Access denied").

NFR-04. A database connection failure shall never be communicated to the user or logged as "access denied"; instead, it shall be communicated and logged as a distinct system failure condition, verifiable by inspecting both the terminal/GUI message and the corresponding log entry.

NFR-05. The graphical user interface, validation logic, and data access layer will be implemented as independent modules, such that the validation logic can be invoked identically from both the GUI and the button-based input path.

NFR-06. Credentials, passwords, or database connection secrets shall not be stored in plain text in any file committed to the repository.