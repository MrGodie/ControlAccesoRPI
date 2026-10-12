``` mermaid

erDiagram
    ROLES ||--o{ USERS : has
    USERS ||--o{ BIOMETRIC_DATA : owns
    USERS |o--o{ ACCESS_LOGS : generates

    ROLES {
        int id PK
        string name UK
        string permissions "e.g. OPEN_MAIN_DOOR"
    }

    USERS {
        int id PK
        string name
        string credential_hash "nullable, button fallback"
        int role_id FK
        boolean active
    }

    BIOMETRIC_DATA {
        int id PK
        int user_id FK
        blob embedding "local facial representation"
        datetime captured_at
    }

    ACCESS_LOGS {
        int id PK
        int user_id FK "nullable, unknown face"
        string method "FACIAL | BUTTONS"
        string result "GRANTED | DENIED"
        datetime timestamp
    }
    ```