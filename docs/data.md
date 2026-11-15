```mermaid
erDiagram
    ROLES ||--o{ USUARIOS : "assigned to"
    USUARIOS ||--o{ DATOS_BIOMETRICOS : "has"
    USUARIOS |o--o{ INTENTOS_ACCESO : "generates"

    ROLES {
        int id PK
        string nombre UK "usuario | admin | soporte"
        string descripcion
        boolean acceso_permitido "opens the door"
        boolean puede_gestionar "registers and edits users"
        boolean puede_consultar "views other users"
    }

    USUARIOS {
        int id PK "user ID typed in GUI and app"
        string nombre
        string credencial_hash UK "SHA2-256 of the PIN"
        int rol_id FK
        boolean activo "false = disabled, keeps history"
    }

    DATOS_BIOMETRICOS {
        int id PK
        int usuario_id FK "ON DELETE CASCADE"
        string tipo "facial"
        blob embedding "template only, no images"
        string modelo
        datetime fecha_registro
    }

    INTENTOS_ACCESO {
        int id PK
        int usuario_id FK "NULL if nobody identified"
        string metodo "facial | gui | botones | app"
        string resultado "autorizado | denegado_* | error_sistema"
        datetime fecha_hora
    }
```