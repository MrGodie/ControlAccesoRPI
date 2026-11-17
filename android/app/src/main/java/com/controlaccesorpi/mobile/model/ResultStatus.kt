package com.controlaccesorpi.mobile.model

/**
 * Outcome of an access request.
 *
 * The first four values are the ones the Raspberry Pi returns; they come
 * straight from its validation logic. [CONNECTION_ERROR] is produced by
 * the app when the Raspberry Pi could not be reached at all.
 */
enum class ResultStatus(private val apiValue: String?) {
    AUTHORIZED("autorizado"),
    DENIED_NO_PERMISSION("denegado_sin_permiso"),
    DENIED_NOT_RECOGNIZED("denegado_no_reconocido"),
    SYSTEM_ERROR("error_sistema"),
    CONNECTION_ERROR(null);

    /** The request reached a decision and the decision was "no". */
    val isDenied: Boolean
        get() = this == DENIED_NO_PERMISSION || this == DENIED_NOT_RECOGNIZED

    /** The request could not be completed; this is never a denial (NFR-11). */
    val isTechnicalFailure: Boolean
        get() = this == SYSTEM_ERROR || this == CONNECTION_ERROR

    companion object {
        /**
         * Maps the value sent by the Raspberry Pi. An unknown or missing
         * value is a technical failure, never a denial.
         */
        fun fromApi(value: String?): ResultStatus =
            entries.firstOrNull { it.apiValue != null && it.apiValue == value } ?: SYSTEM_ERROR
    }
}
