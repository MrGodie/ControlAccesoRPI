```mermaid
classDiagram
    direction LR

    class IdentificationActivity {
        -onIdentifyClicked()
        -showError(message: String?)
        -askServerAddress()
    }
    class RequestActivity {
        -watchPresence()
        -onPresenceChanged(status: PresenceStatus)
        -onRequestClicked()
    }
    class ResultActivity {
        -showResult(result: AccessResult)
    }

    class AccessApp {
        +settings: ServerSettings
        +manager: AccessManager
        +changeServerAddress(address: String)
    }

    class ServerSettings {
        +address: String
        +normalize(text: String)$ String
    }

    class AccessManager {
        -client: RaspberryClient
        +state: AppState
        +currentUser: User?
        +lastResult: AccessResult?
        +identify(userId: String, pin: String) IdentifyOutcome
        +checkPresence() PresenceStatus
        +canRequestAccess() Boolean
        +requestAccess() AccessResult
        +reset()
    }

    class RaspberryClient {
        -baseUrl: String
        -connectTimeoutMs: Int
        -readTimeoutMs: Int
        +identify(user: User) String?
        +getPresence() Boolean
        +sendRequest(request: AccessRequest) AccessResult
    }

    class User {
        +userId: Int
        -pin: String
        +name: String?
        +isValidFormat() Boolean
        +withName(name: String) User
        +newAccessRequest() AccessRequest
        +fromInput(idText: String, pinText: String)$ User?
    }

    class AccessRequest {
        +userId: Int
        -pin: String
        +toJson() String
    }

    class AccessResult {
        +status: ResultStatus
        +userName: String?
        +isAuthorized() Boolean
        +fromJson(json: String)$ AccessResult
        +connectionError()$ AccessResult
    }

    class ResultStatus {
        <<enumeration>>
        AUTHORIZED
        DENIED_NO_PERMISSION
        DENIED_NOT_RECOGNIZED
        SYSTEM_ERROR
        CONNECTION_ERROR
        +isDenied: Boolean
        +isTechnicalFailure: Boolean
        +fromApi(value: String?)$ ResultStatus
    }

    class AppState {
        <<enumeration>>
        IDLE
        IDENTIFIED
        READY
        SENDING
        SHOWING_RESULT
    }

    class IdentifyOutcome {
        <<enumeration>>
        IDENTIFIED
        INVALID_FORMAT
        NOT_RECOGNIZED
        CONNECTION_ERROR
    }

    class PresenceStatus {
        <<enumeration>>
        PRESENT
        ABSENT
        UNREACHABLE
    }

    IdentificationActivity --> AccessApp : uses
    RequestActivity --> AccessApp : uses
    ResultActivity --> AccessApp : uses
    ResultActivity ..> AccessResult : displays

    AccessApp "1" *-- "1" AccessManager
    AccessApp "1" *-- "1" ServerSettings

    AccessManager "1" *-- "1" RaspberryClient
    AccessManager "1" --> "0..1" User : currentUser
    AccessManager "1" --> "0..1" AccessResult : lastResult
    AccessManager --> AppState
    AccessManager ..> IdentifyOutcome : returns
    AccessManager ..> PresenceStatus : returns

    User ..> AccessRequest : creates
    RaspberryClient ..> AccessRequest : sends
    RaspberryClient ..> AccessResult : returns
    AccessResult --> ResultStatus
```
