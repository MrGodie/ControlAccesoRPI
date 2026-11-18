package com.controlaccesorpi.mobile.logic

import com.controlaccesorpi.mobile.model.AccessResult
import com.controlaccesorpi.mobile.model.AppState
import com.controlaccesorpi.mobile.model.ResultStatus
import com.controlaccesorpi.mobile.model.User
import com.controlaccesorpi.mobile.network.ConnectionException
import com.controlaccesorpi.mobile.network.RaspberryClient

/** What happened when the user tried to identify themselves. */
enum class IdentifyOutcome {
    IDENTIFIED,

    /** The form was not filled in correctly; nothing was sent. */
    INVALID_FORMAT,

    /** The Raspberry Pi does not know that code and key. */
    NOT_RECOGNIZED,

    /** Technical failure: never shown as "wrong code or key". */
    CONNECTION_ERROR,
}

/** What happened with the facial access (FR-22). */
enum class FaceOutcome {
    /** The face was recognized and the Raspberry Pi decided: see [AccessManager.lastResult]. */
    RESULT,

    /** There was a face, but it does not match any registered user. */
    NOT_RECOGNIZED,

    /** None of the photos had a face. */
    NO_FACE,

    /** Facial recognition is turned off or not installed on the Raspberry Pi. */
    UNAVAILABLE,

    /** Technical failure on the Raspberry Pi (database). Never a denial. */
    SYSTEM_ERROR,

    /** The Raspberry Pi could not be reached. */
    CONNECTION_ERROR,
}

/**
 * The rules of one access operation: who is identified, whether the
 * request is enabled, and what the last result was. It knows nothing about
 * screens and delegates all communication to [RaspberryClient].
 *
 * The app never decides whether access is granted: that is done on the
 * Raspberry Pi. Its calls block, so they must run off the main thread.
 */
class AccessManager(private val client: RaspberryClient) {

    @Volatile
    var state: AppState = AppState.IDLE
        private set

    @Volatile
    var currentUser: User? = null
        private set

    @Volatile
    var lastResult: AccessResult? = null
        private set

    /** Identifies the user with the text typed in the form. */
    @Synchronized
    fun identify(userId: String, pin: String): IdentifyOutcome {
        reset()
        val user = User.fromInput(userId, pin) ?: return IdentifyOutcome.INVALID_FORMAT

        val name = try {
            client.identify(user)
        } catch (_: ConnectionException) {
            return IdentifyOutcome.CONNECTION_ERROR
        } ?: return IdentifyOutcome.NOT_RECOGNIZED

        currentUser = user.withName(name)
        state = AppState.IDENTIFIED
        return IdentifyOutcome.IDENTIFIED
    }

    /**
     * True only while a user is identified and no request has been sent.
     * The app does not wait for the PIR sensor (PIC-115).
     */
    fun canRequestAccess(): Boolean = state == AppState.IDENTIFIED

    /**
     * Sends the access request and returns the result from the Raspberry Pi.
     *
     * @throws IllegalStateException if the request is not enabled.
     */
    @Synchronized
    fun requestAccess(): AccessResult {
        val user = currentUser
        check(user != null && state == AppState.IDENTIFIED) { "The access request is not enabled" }

        state = AppState.SENDING
        val result = client.sendRequest(user.newAccessRequest())
        lastResult = result
        state = AppState.SHOWING_RESULT
        return result
    }

    /**
     * Facial access (FR-22): sends the photos and lets the Raspberry Pi
     * identify the face and decide. Only a recognized face ends in a
     * result screen; anything else returns to the start so the user can
     * use their code and key. A recognized user without access gets the
     * denial: their key would give the same answer.
     */
    @Synchronized
    fun requestAccessByFace(photos: List<ByteArray>): FaceOutcome {
        reset()
        if (photos.isEmpty()) return FaceOutcome.NO_FACE

        state = AppState.SENDING
        val answer = try {
            client.sendFaceRequest(photos)
        } catch (_: ConnectionException) {
            reset()
            return FaceOutcome.CONNECTION_ERROR
        }

        val outcome = when (answer.result) {
            "rostro_no_reconocido" -> FaceOutcome.NOT_RECOGNIZED
            "sin_rostro" -> FaceOutcome.NO_FACE
            "rostro_no_disponible" -> FaceOutcome.UNAVAILABLE
            else -> when (ResultStatus.fromApi(answer.result)) {
                ResultStatus.AUTHORIZED, ResultStatus.DENIED_NO_PERMISSION -> FaceOutcome.RESULT
                else -> FaceOutcome.SYSTEM_ERROR
            }
        }

        if (outcome != FaceOutcome.RESULT) {
            reset()
            return outcome
        }
        lastResult = AccessResult(ResultStatus.fromApi(answer.result), answer.name)
        state = AppState.SHOWING_RESULT
        return outcome
    }

    /** Back to the initial state, forgetting the identification data (FR-19). */
    @Synchronized
    fun reset() {
        currentUser = null
        lastResult = null
        state = AppState.IDLE
    }
}
