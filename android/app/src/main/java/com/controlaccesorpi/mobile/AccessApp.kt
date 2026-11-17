package com.controlaccesorpi.mobile

import android.app.Application
import com.controlaccesorpi.mobile.logic.AccessManager
import com.controlaccesorpi.mobile.network.RaspberryClient
import com.controlaccesorpi.mobile.ui.ServerSettings

/**
 * Holds the one [AccessManager] the three screens share, so the operation
 * survives going from one screen to the next.
 */
class AccessApp : Application() {

    lateinit var settings: ServerSettings
        private set

    lateinit var manager: AccessManager
        private set

    override fun onCreate() {
        super.onCreate()
        settings = ServerSettings(this)
        manager = newManager()
    }

    /** Points the app at another Raspberry Pi address and starts over. */
    fun changeServerAddress(address: String) {
        settings.address = address
        manager = newManager()
    }

    private fun newManager() = AccessManager(RaspberryClient(settings.address))
}
