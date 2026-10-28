``` mermaid
flowchart TB
    S([Start]) --> PIR[PIR detects presence]
    PIR --> C{Camera and GUI available?}
    C -- No --> BTN[Fallback: PIN via buttons]
    C -- Yes --> CAM[Capture frame]
    CAM --> F{Face detected?}
    F -- No --> R{Retries left?}
    R -- Yes --> CAM
    R -- No --> DENY
    F -- Yes --> REC[Local recognition: match against stored embeddings]
    REC --> K{Known face?}
    K -- No, unknown face --> DENY
    K -- Yes --> PERM
    BTN --> PERM[Query user role and permissions in DB]
    PERM --> A{Authorized?}
    A -- Yes --> GRANT[Grant access: actuator + audio]
    A -- No --> DENY[Deny access: show message]
    GRANT --> LOG
    DENY --> LOG[Log event: user, method, result, timestamp]
    LOG --> REL[Release camera, return to idle]
    REL --> E([End])

    ADM[Admin registers user: name and role] --> NEW[Create user in DB]
    NEW --> CAP[Guided capture of multiple face samples]
    CAP --> V{Enough valid samples?}
    V -- No --> CAP
    V -- Yes --> SAVE[Store embeddings locally, linked to user]
    SAVE --> OK[Show enrollment confirmation]
    OK --> REL

    classDef ok fill:#E4F3DE,stroke:#548235,color:#375623;
    classDef bad fill:#FBE2E1,stroke:#C0504D,color:#7A2E2C;
    classDef alt fill:#FDEBD3,stroke:#C87F0A,color:#7A4A05;
    classDef face fill:#EADCF8,stroke:#7030A0,color:#44205F;
    class GRANT,OK ok;
    class DENY bad;
    class BTN alt;
    class CAM,REC,CAP,SAVE face;
    ```