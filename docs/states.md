flowchart TD
    A[Inicializar sistema] --> B{Hardware y BD OK?}
    B -- No --> C[Modo degradado: solo botones]
    B -- Sí --> D[Reposo]
    C --> D
    D --> E{PIR detecta presencia?}
    E -- No --> F[Notificar: sin presencia detectada]
    F --> G{Seguir esperando?}
    G -- Sí --> D
    G -- No --> A
    E --> I[Capturar secuencia]
    I --> J{Logitud Valida?}
    J -- No -->I
    J -- Sí --> K[Validar contra base de datos]
    K --> L{Resultado}
    L -- Autorizado --> M[Mostrar: Acceso autorizado]
    L -- Sin permiso --> N[Mostrar: Acceso denegado]
    L -- Credencial inválida --> N
    L -- Sin respuesta de BD --> O[Mostrar: Error del sistema]
    M --> P[Registrar intento]
    N --> P
    O --> P
    N --> D