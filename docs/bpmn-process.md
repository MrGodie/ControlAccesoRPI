```mermaid
flowchart LR
    subgraph L1["User"]
        S([Start]) --> LOOK[Look at the camera,<br/>tap Entrar con rostro]
        ID[Enter ID and PIN]
        TAP[Tap Request access]
        SEE[See result]
    end

    subgraph L2["Mobile app"]
        PHOTOS[Take 3 photos,<br/>send them to the Raspberry Pi]
        WHY[Open the ID and PIN form<br/>with the reason]
        REG{Registered user?}
        READY[Request enabled<br/>no presence needed]
        SEND[Send request to the Raspberry Pi]
        NET{Answer received?}
        SHOW[Show authorized / denied]
        TECH[Show: operation could not be completed]
        RST[Return to initial state]
    end

    subgraph L3["Raspberry Pi"]
        FACE{Face recognized?<br/>face.py}
        VAL[[Shared validation<br/>validator.py]]
        RES{Result}
        OK[Green LED, motor, success audio]
        NO[Red LED, denial audio]
        ERR[Red blink, failure audio]
        LOG[Log attempt, method = app or app_facial]
        OTHER[/Face, GUI, buttons/] -.-> VAL
    end

    LOOK --> PHOTOS --> FACE
    FACE -- Yes --> VAL
    FACE -- "No, no face, not available" --> WHY --> ID
    ID --> REG
    REG -- No --> ID
    REG -- Yes --> READY --> TAP
    TAP --> SEND --> VAL --> RES
    RES -- Authorized --> OK --> LOG
    RES -- Denied --> NO --> LOG
    RES -- DB failure --> ERR --> LOG
    LOG --> NET
    SEND -.->|timeout| NET
    NET -- Yes --> SHOW --> SEE
    NET -- No --> TECH --> SEE
    SEE --> RST --> E([End])

    classDef ok fill:#E4F3DE,stroke:#548235,color:#375623;
    classDef bad fill:#FBE2E1,stroke:#C0504D,color:#7A2E2C;
    classDef app fill:#DDEBF7,stroke:#1F4E79,color:#1F3864;
    class OK ok;
    class NO,ERR,TECH bad;
    class SEND,READY,PHOTOS,WHY app;
```