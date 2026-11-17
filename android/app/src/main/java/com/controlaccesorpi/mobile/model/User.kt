package com.controlaccesorpi.mobile.model

/**
 * The person using the app: the code and key they typed and, once the
 * Raspberry Pi has identified them, their name.
 */
class User(
    val userId: Int,
    private val pin: String,
    val name: String? = null,
) {
    fun isValidFormat(): Boolean =
        userId > 0 && pin.isNotEmpty() && pin.length <= MAX_PIN_LENGTH && pin.all { it in '0'..'9' }

    fun withName(name: String): User = User(userId, pin, name)

    fun newAccessRequest(): AccessRequest = AccessRequest(userId, pin)

    // The key must never end up in a log.
    override fun toString(): String = "User(userId=$userId, name=$name)"

    companion object {
        const val MAX_ID_DIGITS = 8
        const val MAX_PIN_LENGTH = 32

        /** Builds a user from the text typed in the form, or null if it is not valid. */
        fun fromInput(idText: String, pinText: String): User? {
            val id = idText.trim()
            if (id.isEmpty() || id.length > MAX_ID_DIGITS || !id.all { it in '0'..'9' }) return null
            return User(id.toInt(), pinText.trim()).takeIf { it.isValidFormat() }
        }
    }
}
