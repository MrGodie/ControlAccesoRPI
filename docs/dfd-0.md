```mermaid
flowchart LR
    U[Usuario] -->|Pulsaciones de botones| S((Sistema de Control de Acceso))
    S -->|Mensaje: Acceso autorizado / denegado| U
    S -->|Solicita configuración vigente| A[Administrador]
    A -->|Define clave válida| S
    A -->|Define longitud de secuencia 4-6| S
```