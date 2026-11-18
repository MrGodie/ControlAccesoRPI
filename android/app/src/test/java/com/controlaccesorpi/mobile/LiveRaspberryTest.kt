package com.controlaccesorpi.mobile

import com.controlaccesorpi.mobile.logic.AccessManager
import com.controlaccesorpi.mobile.logic.IdentifyOutcome
import com.controlaccesorpi.mobile.model.ResultStatus
import com.controlaccesorpi.mobile.network.RaspberryClient
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assume.assumeTrue
import org.junit.Test

/**
 * Checks the app's communication layer against a real Raspberry Pi from
 * the PC, without a phone. Skipped unless RASPBERRY_URL is set:
 *
 *     RASPBERRY_URL=http://192.168.1.50:8000 RASPBERRY_USER_ID=1 RASPBERRY_PIN=123 \
 *         ./gradlew testDebugUnitTest --tests "*LiveRaspberryTest*"
 *
 * The access request is only sent with RASPBERRY_SEND_ACCESS=1, because it
 * moves the motor and writes to the access log.
 */
class LiveRaspberryTest {

    private val url = System.getenv("RASPBERRY_URL")
    private val userId = System.getenv("RASPBERRY_USER_ID")
    private val pin = System.getenv("RASPBERRY_PIN")

    private fun manager(): AccessManager {
        assumeTrue("RASPBERRY_URL is not set", !url.isNullOrBlank())
        return AccessManager(RaspberryClient(url))
    }

    @Test
    fun `a wrong key is not recognized`() {
        assertEquals(IdentifyOutcome.NOT_RECOGNIZED, manager().identify("99999999", "00000000"))
    }

    @Test
    fun `a registered user is identified`() {
        val manager = manager()
        assumeTrue("RASPBERRY_USER_ID and RASPBERRY_PIN are not set", !userId.isNullOrBlank() && !pin.isNullOrBlank())
        assertEquals(IdentifyOutcome.IDENTIFIED, manager.identify(userId, pin))
    }

    @Test
    fun `an access request returns a result from the validation`() {
        val manager = manager()
        assumeTrue("RASPBERRY_SEND_ACCESS is not 1", System.getenv("RASPBERRY_SEND_ACCESS") == "1")
        assumeTrue("RASPBERRY_USER_ID and RASPBERRY_PIN are not set", !userId.isNullOrBlank() && !pin.isNullOrBlank())

        assertEquals(IdentifyOutcome.IDENTIFIED, manager.identify(userId, pin))

        val result = manager.requestAccess()
        assertNotEquals(ResultStatus.CONNECTION_ERROR, result.status)
        println("Access result from the Raspberry Pi: ${result.status} (${result.userName})")
    }
}
