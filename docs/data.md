erDiagram
    ROLES ||--o{ USUARIOS : "tiene"
    USUARIOS ||--o{ INTENTOS_ACCESO : "genera"

    ROLES {
        int id PK 
        string nombre
        string descripcion
    }

    USUARIOS {
        int id PK
        string nombre
        string credencial_hash
        int rol_id FK
    }

    INTENTOS_ACCESO {
        int id PK
        int usuario_id FK
        string metodo
        string resultado
        datetime fecha_hora
    }
   
