``` mermaid
flowchart LR
    Start([Inicio: usuario se acerca])

    subgraph Usuario
        Start
        Botones[Botones físicos<br/>Usuario ingresa clave]
        Identifica[Se identifica<br/>Datos por interfaz gráfica]
        Notifica[Notifica resultado<br/>Mensaje / audio al usuario]
    end

    subgraph Sistema_RPi [Sistema · Raspberry Pi]
        PIR[Sensor PIR<br/>Detecta presencia]
        GW1{¿Interfaz gráfica<br/>disponible?}
        Interfaz[Interfaz gráfica<br/>Se muestra en el monitor]
        GW2{¿Autorizado?}
        Autoriza[Autoriza acceso<br/>Actuador + audio OK]
        Rechaza[Rechaza acceso<br/>Muestra mensaje]
        Registra[Registra intento<br/>Fecha, usuario, resultado]
        End([Fin: vuelve a espera])
    end

    subgraph BD [Base de datos · MySQL]
        Valida[Valida credenciales<br/>Consulta rol y permisos]
    end

    Start --> PIR
    PIR --> GW1
    GW1 -- Si --> Interfaz
    GW1 -- No --> Botones
    Interfaz --> Identifica
    Identifica --> Valida
    Botones -. misma logica .-> Valida
    Valida --> GW2
    GW2 -- Si --> Autoriza
    GW2 -- No --> Rechaza
    Autoriza --> Notifica
    Rechaza --> Notifica
    Notifica --> Registra
    Registra --> End

    classDef taskNormal fill:#DCEEFB,stroke:#2E75B6,color:#1B4B72;
    classDef taskAlt fill:#FDEBD3,stroke:#C87F0A,color:#7A4A05;
    classDef ok fill:#E4F3DE,stroke:#548235,color:#375623;
    classDef bad fill:#FBE2E1,stroke:#C0504D,color:#7A2E2C;

    class PIR,Interfaz,Identifica,Notifica,Registra taskNormal;
    class Botones taskAlt;
    class Autoriza ok;
    class Rechaza bad;
    ```