# Functional Requirements (FR)

FR-01. The system shall capture each press of the physical buttons connected to the GPIO inputs, store it in order as part of the entered sequence, and automatically compare it against the configured valid key as soon as the defined length is reached (between 4 and 6 presses).

FR-02. The system shall display the message "Access granted" on the terminal when the captured sequence exactly matches the valid key, or "Access denied" otherwise.

FR-03. The system shall reset the capture state (clear the stored sequence) immediately after displaying the result, allowing a new attempt without restarting the program.

FR-04. The system shall allow the valid key and the required sequence length (3) to be modified by editing a single configuration variable or data structure in the source code, without requiring changes to the input-reading or comparison logic.

FR-05. The system shall provide immediate terminal feedback confirming that each individual press has been registered, without revealing the configured valid key, the required sequence length, or the number of presses captured so far.

FR-06. The system shall detect human presence via the PIR sensor and transition from an idle state to an active interaction state; subsequently, it shall display a graphical interface allowing the user to enter their identification credentials.

FR-07. When the graphical interface or monitor is unavailable, the system shall allow the user to complete identification and validation using only physical buttons, generating the same result categories (authorized/denied) as the graphical method.

FR-08. The system shall use the same validation logic to evaluate access attempts, regardless of whether the identification was entered via the graphical interface or physical buttons, without employing separate or duplicate authorization paths.

FR-09. The system shall log every access attempt in a MySQL database, whether access is granted or denied. The log entry shall include the identifier used, the timestamp, the interaction method (graphical interface or physical buttons), and the resulting outcome.

FR-10. The system shall issue an audible response (e.g., a voice message or a tone indicating "Access granted") and activate a physical actuator (e.g., a servomotor, relay, or equivalent) to signify the opening or authorization of access whenever an attempt is authorized.

FR-11. The system shall distinguish—both in its user response and in the stored log—between the following outcomes: access authorized, access denied due to insufficient permissions, access denied due to unrecognized credentials, and inability to complete validation due to a database connection failure.

FR-12. The system shall acquire images or video stably from a camera connected to the system, and shall shall detect a face presented to the camera and identify it by comparing it against the biometric representations of the enrolled users, returning either the matching user or no match. After a user is identified by facial recognition, the system shall query the user's permissions, authorize or deny the access accordingly, and trigger the same audible and physical responses as the other identification methods.

FR-13. The system shall provide a guided facial enrollment flow through which an administrator registers a new user: entering the user's information, capturing multiple valid facial samples through the live camera, and receiving an on-screen confirmation when the enrollment is completed successfully.

FR-14. The system shall store the biometric representation (facial template) of each enrolled user in the local database, associated with that user and with their permissions, such that deleting the user also deletes their biometric data.

FR-15. The system shall allow a user to identify themselves from the mobile application by entering their user identifier and credential. When the identification is not valid, the application shall inform the user without revealing which of the two fields was wrong.

FR-16. The mobile application shall enable the access request as soon as the user has been identified (FR-15); it shall not wait for the PIR sensor. The PIR sensor keeps starting the access cycle of the Raspberry Pi (FR-06), and the result of a request from the app is always decided by the Raspberry Pi (FR-20).

FR-17. The system shall allow an identified user to send an access request from the mobile application and shall return the result of that request to the application. An authorized request shall trigger the same audible and physical responses as the other identification methods (FR-10), and every request shall be logged with the mobile application as its interaction method (FR-09).

FR-18. The mobile application shall distinguish between access authorized, access denied (insufficient permissions or unrecognized credentials), and access that could not be completed due to a technical condition.

FR-19. The mobile application shall return to its initial state once the operation ends, clearing the identification data entered for that attempt.

FR-20. The system shall authorize requests coming from the mobile application with the same validation logic used by the existing access methods (physical buttons, graphical interface and facial recognition), without a separate or parallel authorization path for the application.

FR-21. The mobile application shall offer the same user management functions as the graphical interface of the Raspberry Pi, limited by the same role capabilities: a user whose role can consult shall be able to list the registered users, and a user whose role can manage shall also be able to register a new user and enroll or re-enroll a user's face with the phone camera. Every change shall be validated and applied by the Raspberry Pi with the same functions the graphical interface uses.

FR-22. The mobile application shall allow a user to request access by facial recognition with the phone camera, as the first option when the application opens. The application shall send the captured images to the Raspberry Pi, which shall identify the face against the stored templates and authorize or deny the access with the same logic as FR-12, and log it as a facial access from the mobile application. When the face is not recognized, no face is detected, or the facial recognition is not available, the application shall offer the identification with code and key (FR-15) and say why; a recognized user whose role does not allow access shall receive the denial instead.

FR-23. The system shall log every relevant event, not only access attempts: identifications, access attempts by any method, the start and end of administration sessions, every administrative change (with the user who made it and the user affected), the loss and recovery of the connection between the mobile application and the Raspberry Pi, and technical failures. Each entry shall include the timestamp, the user when known, the origin (interaction method or device), the event type, the outcome and a detail.

FR-24. When the mobile application cannot reach the Raspberry Pi, it shall remain available for access requests, but it shall report every request as not completed for a technical condition (NFR-11), never as authorized, and it shall disable every administrative function until the connection returns.

FR-25. The events produced by the mobile application while it cannot reach the Raspberry Pi shall be stored on the phone and sent to the Raspberry Pi automatically when the connection returns. Each event shall keep the time at which it happened on the phone, shall be marked as recorded without connection, shall be stored only once even if it is sent more than once, and shall not be removed from the phone until the Raspberry Pi confirms it was stored.

FR-26. The log of FR-23, including the events received from phones, shall be viewable from the graphical interface of the Raspberry Pi and from the mobile application by users whose role can consult, filtered by date, user and event type.
 


# Non-Functional Requirements (NFR)

NFR-01. The system shall implement a debounce technique such that a single physical press does not generate more than one record in 95% of the test presses performed.

NFR-02. The source code shall be organized in the src/ directory following a modular structure (e.g., separation between input reading, validation logic, and output of results), such that a team member other than the author can locate each function in under 2 minutes.

NFR-03. The system shall display the result ("Access granted" / "Access denied").

NFR-04. A database connection failure shall never be communicated to the user or logged as "access denied"; instead, it shall be communicated and logged as a distinct system failure condition, verifiable by inspecting both the terminal/GUI message and the corresponding log entry.

NFR-05. The graphical user interface, validation logic, and data access layer will be implemented as independent modules, such that the validation logic can be invoked identically from both the GUI and the button-based input path.

NFR-06. Credentials, passwords, or database connection secrets shall not be stored in plain text in any file committed to the repository.

NFR-07. Facial detection, facial identification, biometric storage and the access decision shall run entirely on the local system, without using external or cloud-based recognition services.

NFR-08. The system shall store only the biometric template of each user in the database and shall not persist the captured face images.

NFR-09. The mobile application shall offer administrative functions (FR-21) only to users whose role allows them, only while it is connected to the Raspberry Pi, and only within an authenticated session (NFR-12). It shall not change the system configuration (the values of config.py).

NFR-10. Adding the mobile application shall not change the behavior of the existing access methods (physical buttons, graphical interface and facial recognition), which shall keep working as before.

NFR-11. A technical failure during a mobile access request (database connection failure, Raspberry Pi unreachable, or no response within the expected time) shall never be shown in the application or logged as "access denied"; it shall be reported as a distinct condition, as required by NFR-04.

NFR-12. The user's credential shall be sent from the mobile application only once, when identifying. The Raspberry Pi shall then issue a session token that expires after a period of inactivity and when the user leaves; administrative and log functions shall require a valid token, and every administrative request shall be checked on the Raspberry Pi against the current capabilities of the user's role.

NFR-13. The phone shall never store credentials, session tokens after the session ends, biometric templates, face images or the list of users. Only the pending events of FR-25 may be stored on it, and they shall contain no credential or face image.

NFR-14. The face images captured by the phone shall only be sent to the Raspberry Pi, processed there as required by NFR-07 and discarded after use, as required by NFR-08.
