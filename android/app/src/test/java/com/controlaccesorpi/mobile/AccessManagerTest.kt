package com.controlaccesorpi.mobile

import com.controlaccesorpi.mobile.logic.AccessManager
import com.controlaccesorpi.mobile.logic.IdentifyOutcome
import com.controlaccesorpi.mobile.logic.PresenceStatus
import com.controlaccesorpi.mobile.model.AppState
import com.controlaccesorpi.mobile.model.ResultStatus
import com.controlaccesorpi.mobile.network.RaspberryClient
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class AccessManagerTest {

    private val pi = FakeRaspberry()
    private val manager = AccessManager(RaspberryClient(pi.baseUrl, connectTimeoutMs = 1_000, readTimeoutMs = 1_000))

    @After
    fun stop() = pi.close()

    private fun identifyAna() {
        pi.answer("/api/login", 200, """{"identified": true, "name": "Ana"}""")
        assertEquals(IdentifyOutcome.IDENTIFIED, manager.identify("12", "123"))
    }

    @Test
    fun `it starts with nobody identified`() {
        assertEquals(AppState.IDLE, manager.state)
        assertNull(manager.currentUser)
        assertFalse(manager.canRequestAccess())
    }

    @Test
    fun `a complete authorized operation goes through every state`() {
        identifyAna()
        assertEquals(AppState.IDENTIFIED, manager.state)
        assertEquals("Ana", manager.currentUser?.name)

        pi.answer("/api/presence", 200, """{"present": false}""")
        assertEquals(PresenceStatus.ABSENT, manager.checkPresence())
        assertFalse(manager.canRequestAccess())

        pi.answer("/api/presence", 200, """{"present": true}""")
        assertEquals(PresenceStatus.PRESENT, manager.checkPresence())
        assertEquals(AppState.READY, manager.state)
        assertTrue(manager.canRequestAccess())

        pi.answer("/api/access", 200, """{"result": "autorizado", "name": "Ana"}""")
        val result = manager.requestAccess()
        assertTrue(result.isAuthorized())
        assertEquals(AppState.SHOWING_RESULT, manager.state)
        assertEquals(result, manager.lastResult)

        manager.reset()
        assertEquals(AppState.IDLE, manager.state)
        assertNull(manager.currentUser)
        assertNull(manager.lastResult)
    }

    @Test
    fun `an invalid form is rejected without calling the Raspberry Pi`() {
        assertEquals(IdentifyOutcome.INVALID_FORMAT, manager.identify("", "123"))
        assertEquals(IdentifyOutcome.INVALID_FORMAT, manager.identify("12", "abc"))
        assertTrue(pi.calls.isEmpty())
        assertEquals(AppState.IDLE, manager.state)
    }

    @Test
    fun `a wrong code or key leaves nobody identified`() {
        pi.answer("/api/login", 200, """{"identified": false, "name": null}""")
        assertEquals(IdentifyOutcome.NOT_RECOGNIZED, manager.identify("12", "999"))
        assertEquals(AppState.IDLE, manager.state)
        assertNull(manager.currentUser)
    }

    @Test
    fun `a technical failure while identifying is not reported as a wrong code or key`() {
        pi.answer("/api/login", 503, """{"result": "error_sistema"}""")
        assertEquals(IdentifyOutcome.CONNECTION_ERROR, manager.identify("12", "123"))
        assertEquals(AppState.IDLE, manager.state)
    }

    @Test
    fun `the request is not enabled without presence`() {
        identifyAna()
        pi.answer("/api/presence", 200, """{"present": false}""")
        manager.checkPresence()

        assertThrows(IllegalStateException::class.java) { manager.requestAccess() }
        assertTrue(pi.callsTo("/api/access").isEmpty())
    }

    @Test
    fun `the request is not enabled before identifying`() {
        pi.answer("/api/presence", 200, """{"present": true}""")
        assertEquals(PresenceStatus.ABSENT, manager.checkPresence())
        assertTrue("presence alone must not enable anything", pi.callsTo("/api/presence").isEmpty())
        assertThrows(IllegalStateException::class.java) { manager.requestAccess() }
    }

    @Test
    fun `presence going away disables the request again`() {
        identifyAna()
        pi.answer("/api/presence", 200, """{"present": true}""")
        manager.checkPresence()
        pi.answer("/api/presence", 200, """{"present": false}""")
        manager.checkPresence()
        assertFalse(manager.canRequestAccess())
    }

    @Test
    fun `losing the Raspberry Pi disables the request`() {
        identifyAna()
        pi.answer("/api/presence", 200, """{"present": true}""")
        manager.checkPresence()
        pi.answer("/api/presence", 500, "boom")
        assertEquals(PresenceStatus.UNREACHABLE, manager.checkPresence())
        assertFalse(manager.canRequestAccess())
    }

    @Test
    fun `a denied request is reported as denied`() {
        identifyAna()
        pi.answer("/api/presence", 200, """{"present": true}""")
        manager.checkPresence()
        pi.answer("/api/access", 200, """{"result": "denegado_sin_permiso", "name": "Ana"}""")

        val result = manager.requestAccess()
        assertFalse(result.isAuthorized())
        assertTrue(result.status.isDenied)
        assertEquals(AppState.SHOWING_RESULT, manager.state)
    }

    @Test
    fun `a technical failure during the request is not reported as denied`() {
        identifyAna()
        pi.answer("/api/presence", 200, """{"present": true}""")
        manager.checkPresence()
        pi.answer("/api/access", 200, """{"result": "error_sistema", "name": null}""")

        val result = manager.requestAccess()
        assertEquals(ResultStatus.SYSTEM_ERROR, result.status)
        assertTrue(result.status.isTechnicalFailure)
        assertFalse(result.status.isDenied)
    }

    @Test
    fun `a request cannot be sent twice for the same operation`() {
        identifyAna()
        pi.answer("/api/presence", 200, """{"present": true}""")
        manager.checkPresence()
        pi.answer("/api/access", 200, """{"result": "autorizado", "name": "Ana"}""")
        manager.requestAccess()

        assertThrows(IllegalStateException::class.java) { manager.requestAccess() }
        assertEquals(1, pi.callsTo("/api/access").size)
    }

    @Test
    fun `identifying again forgets the previous user`() {
        identifyAna()
        pi.answer("/api/login", 200, """{"identified": false, "name": null}""")
        manager.identify("99", "000")
        assertNull(manager.currentUser)
        assertEquals(AppState.IDLE, manager.state)
    }
}
