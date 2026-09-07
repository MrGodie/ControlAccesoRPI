```mermaid
flowchart TD
    A[Inicio / esperar entrada] --> B[[Agregar valor a secuencia]]
    B --> C{Longitud alcanzada?}
    C -- No --> B
    C -- Sí --> D{Secuencia == clave válida?}
    D -- Sí --> E[Mostrar: Acceso autorizado]
    D -- No --> F[Mostrar: Acceso denegado]
    E --> G[Reiniciar estado]
    F --> G
    G --> A
    ```