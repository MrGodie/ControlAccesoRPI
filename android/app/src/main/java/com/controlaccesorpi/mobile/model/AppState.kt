package com.controlaccesorpi.mobile.model

/** Where the app is in one access operation. */
enum class AppState {
    /** Nobody identified; the form is empty. */
    IDLE,

    /** User identified, waiting for the PIR sensor to detect presence. */
    IDENTIFIED,

    /** Presence detected: the access request is enabled. */
    READY,

    /** Request sent, waiting for the Raspberry Pi. */
    SENDING,

    /** The result is on screen. */
    SHOWING_RESULT,
}
