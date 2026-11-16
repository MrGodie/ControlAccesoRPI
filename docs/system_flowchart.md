```mermaid
flowchart TD
    A[Power on the Raspberry Pi] --> B[Load .env config, init GPIO and audio]
    B --> C{Camera OK?}
    C -- Yes --> D[Load face templates from DB]
    C -- No --> E[Face recognition off]
    D & E --> F{Monitor available?}
    F -- Yes --> G[Start GUI]
    F -- No --> H[Buttons only]
    G & H --> T[Start both threads]

    T --> L1
    T --> A1

    subgraph MAIN["Thread 1: local access cycle"]
        L1[Wait for PIR presence] --> L2[Identify: face, then GUI or buttons]
        L2 --> L3[[Validate, respond and log]]
        L3 --> L4[Wait for presence to end, reset]
        L4 --> L1
    end

    subgraph API["Thread 2: api_server.py"]
        A1[Listen on Wi-Fi] --> A2{Request}
        A2 -- GET /presence --> A3[Return PIR state]
        A2 -- POST /identify --> A4[Look up user, return name]
        A2 -- POST /access --> A5{Presence active?}
        A5 -- No --> A6[409: request not enabled]
        A5 -- Yes --> A7[[Validate, respond and log<br/>method = app]]
        A3 & A4 & A6 & A7 --> A1
    end

    classDef app fill:#DDEBF7,stroke:#1F4E79,color:#1F3864;
    class A1,A2,A3,A4,A5,A6,A7 app;
```
