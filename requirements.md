# Functional Requirements (FR)

FR-01. The system shall capture each press of the physical buttons connected to the GPIO inputs, store it in order as part of the entered sequence, and automatically compare it against the configured valid key as soon as the defined length is reached (between 4 and 6 presses).

FR-02. The system shall display the message "Access granted" on the terminal when the captured sequence exactly matches the valid key, or "Access denied" otherwise.

FR-03. The system shall reset the capture state (clear the stored sequence) immediately after displaying the result, allowing a new attempt without restarting the program.

FR-04. The system shall allow the valid key and the required sequence length (4 to 6 presses) to be modified by editing a single configuration variable or data structure in the source code, without requiring changes to the input-reading or comparison logic.

FR-05. The system shall provide immediate terminal feedback confirming that each individual press has been registered, without revealing the configured valid key, the required sequence length, or the number of presses captured so far.


# Non-Functional Requirements (NFR)

NFR-01. The system shall implement a debounce technique such that a single physical press does not generate more than one record in 95% of the test presses performed.

NFR-02. The source code shall be organized in the src/ directory following a modular structure (e.g., separation between input reading, validation logic, and output of results), such that a team member other than the author can locate each function in under 2 minutes.

NFR-03. The system shall display the result ("Access granted" / "Access denied").
 