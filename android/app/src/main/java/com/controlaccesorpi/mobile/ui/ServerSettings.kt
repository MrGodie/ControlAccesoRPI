package com.controlaccesorpi.mobile.ui

import android.content.Context

/**
 * Where the Raspberry Pi is on the local network. It is the only thing
 * the app remembers between operations; it is a setting of this phone,
 * not of the access control system.
 */
class ServerSettings(context: Context) {

    private val preferences = context.getSharedPreferences("server", Context.MODE_PRIVATE)

    var address: String
        get() = preferences.getString(KEY_ADDRESS, null) ?: DEFAULT_ADDRESS
        set(value) {
            preferences.edit().putString(KEY_ADDRESS, normalize(value)).apply()
        }

    companion object {
        const val DEFAULT_ADDRESS = "http://192.168.1.100:8000"
        private const val KEY_ADDRESS = "address"

        /** Accepts "192.168.1.50:8000" as well as a full "http://..." address. */
        fun normalize(text: String): String {
            val address = text.trim().trimEnd('/')
            if (address.isEmpty()) return DEFAULT_ADDRESS
            return if (address.startsWith("http://") || address.startsWith("https://")) address else "http://$address"
        }
    }
}
