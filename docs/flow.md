```mermaid
flowchart TD
    A([Inicio / estado de espera]) --> B{¿PIR detecta presencia?}
    B -- No --> A
    B -- Sí --> C{¿Interfaz gráfica disponible?}

    C -- Sí --> D[Mostrar pantalla de identificación]
    D --> E[/Capturar identificación y PIN en la GUI/]
    E --> V[[Validar acceso: lógica compartida]]

    C -- No --> F[/Leer pulsación de botón/]
    F --> G[[Agregar valor a secuencia]]
    G --> H{¿Longitud alcanzada?}
    H -- No --> F
    H -- Sí --> V

    V --> I{¿Consulta a MySQL exitosa?}
    I -- No --> R5[Mostrar: No es posible completar la operación]
    I -- Sí --> J{¿Usuario existe?}
    J -- No --> R4[Mostrar: Usuario no reconocido]
    J -- Sí --> K{¿Credencial correcta?}
    K -- No --> R3[Mostrar: Credencial incorrecta]
    K -- Sí --> L{¿El rol tiene permiso?}
    L -- No --> R2[Mostrar: Acceso denegado, sin permiso]
    L -- Sí --> R1[Mostrar: Acceso autorizado]

    R1 --> S[Reproducir audio: Acceso correcto]
    S --> T[Activar actuador]
    T --> REG[Registrar intento: usuario, método, resultado, fecha y hora]
    R2 --> REG
    R3 --> REG
    R4 --> REG
    R5 --> REG

    REG --> Z[Reiniciar estado]
    Z --> A
    ```