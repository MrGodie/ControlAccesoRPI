package com.controlaccesorpi.mobile

import com.controlaccesorpi.mobile.ui.ServerSettings
import org.junit.Assert.assertEquals
import org.junit.Test

class ServerSettingsTest {

    @Test
    fun `an address typed without http is completed`() {
        assertEquals("http://192.168.1.50:8000", ServerSettings.normalize("192.168.1.50:8000"))
        assertEquals("http://192.168.1.50:8000", ServerSettings.normalize("  http://192.168.1.50:8000/ "))
    }

    @Test
    fun `an empty address falls back to the default`() {
        assertEquals(ServerSettings.DEFAULT_ADDRESS, ServerSettings.normalize("   "))
    }
}
