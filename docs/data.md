```mermaid
erDiagram
    ROLES ||--o{ USUARIOS : "se asigna a"
    USUARIOS ||--o{ DATOS_BIOMETRICOS : "tiene"
    USUARIOS |o--o{ EVENTOS : "realiza"
    USUARIOS |o--o{ EVENTOS : "le afecta"

    ROLES {
        int id PK
        string nombre UK "usuario | admin | soporte"
        string descripcion
        boolean acceso_permitido "abre la puerta"
        boolean puede_gestionar "da de alta y edita usuarios"
        boolean puede_consultar "ve a otros usuarios"
    }

    USUARIOS {
        int id PK "ID que se escribe en la GUI y la app"
        string nombre
        string credencial_hash "Argon2id o bcrypt del PIN, con salt"
        int rol_id FK
        boolean activo "false = deshabilitado, conserva historial"
    }

    DATOS_BIOMETRICOS {
        int id PK
        int usuario_id FK "ON DELETE CASCADE"
        string tipo "facial"
        blob embedding "solo plantilla, sin imagenes"
        string modelo
        datetime fecha_registro
    }

    EVENTOS {
        int id PK
        string evento_uid UK "un reintento nunca lo guarda dos veces"
        datetime fecha_hora "cuando ocurrio"
        datetime recibido "cuando se guardo"
        string tipo "CHECK: acceso | identificacion | admin_* | alta_usuario | cambio_rol | ..."
        string origen "CHECK: gui | botones | facial | app | app_facial | sistema"
        int usuario_id FK "quien actua, ON DELETE SET NULL"
        int afectado_id FK "a quien afecta, ON DELETE SET NULL"
        string resultado "CHECK: autorizado | denegado_* | error_sistema | ..."
        string detalle "nunca una clave"
        boolean sin_conexion "registrado por el movil sin conexion (FR-25)"
        string dispositivo "direccion del movil"
    }
```