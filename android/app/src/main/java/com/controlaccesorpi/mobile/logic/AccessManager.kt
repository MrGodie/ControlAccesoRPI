package com.controlaccesorpi.mobile.logic

import com.controlaccesorpi.mobile.model.AccessResult
import com.controlaccesorpi.mobile.model.AppState
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

/** What the Raspberry Pi says about the PIR sensor. */
enum class PresenceStatus {
    PRESENT,
    ABSENT,

    /** The Raspberry Pi did not answer. */
    UNREACHABLE,
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
     * Asks once whether there is presence and enables or disables the
     * request accordingly. The screen calls it every [PRESENCE_POLL_MS].
     *
     * Presence only enables the request; it never authorizes access.
     */
    @Synchronized
    fun checkPresence(): PresenceStatus {
        if (state != AppState.IDENTIFIED && state != AppState.READY) return PresenceStatus.ABSENT

        val present = try {
            client.getPresence()
        } catch (_: ConnectionException) {
            state = AppState.IDENTIFIED
            return PresenceStatus.UNREACHABLE
        }

        state = if (present) AppState.READY else AppState.IDENTIFIED
        return if (present) PresenceStatus.PRESENT else PresenceStatus.ABSENT
    }

    /** True only while a user is identified and presence has been detected. */
    fun canRequestAccess(): Boolean = state == AppState.READY

    /**
     * Sends the access request and returns the result from the Raspberry Pi.
     *
     * @throws IllegalStateException if the request is not enabled.
     */
    @Synchronized
    fun requestAccess(): AccessResult {
        val user = currentUser
        check(user != null && state == AppState.READY) { "The access request is not enabled" }

        state = AppState.SENDING
        val result = client.sendRequest(user.newAccessRequest())
        lastResult = result
        state = AppState.SHOWING_RESULT
        return result
    }

    /** Back to the initial state, forgetting the identification data (FR-19). */
    @Synchronized
    fun reset() {
        currentUser = null
        lastResult = null
        state = AppState.IDLE
    }

    companion object {
        const val PRESENCE_POLL_MS = 1_000L
    }
}
