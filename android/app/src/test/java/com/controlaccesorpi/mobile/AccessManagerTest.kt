package com.controlaccesorpi.mobile

import com.controlaccesorpi.mobile.logic.AccessManager
import com.controlaccesorpi.mobile.logic.FaceOutcome
import com.controlaccesorpi.mobile.logic.IdentifyOutcome
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
    fun `the request is enabled without asking the PIR sensor`() {
        identifyAna()
        pi.answer("/api/access", 200, """{"result": "autorizado", "name": "Ana"}""")

        manager.requestAccess()
        assertEquals(1, pi.callsTo("/api/access").size)
        assertTrue("the app must not ask for presence", pi.callsTo("/api/presence").isEmpty())
    }

    @Test
    fun `the request is not enabled before identifying`() {
        assertFalse(manager.canRequestAccess())
        assertThrows(IllegalStateException::class.java) { manager.requestAccess() }
        assertTrue(pi.calls.isEmpty())
    }

    @Test
    fun `a denied request is reported as denied`() {
        identifyAna()
        pi.answer("/api/access", 200, """{"result": "denegado_sin_permiso", "name": "Ana"}""")

        val result = manager.requestAccess()
        assertFalse(result.isAuthorized())
        assertTrue(result.status.isDenied)
        assertEquals(AppState.SHOWING_RESULT, manager.state)
    }

    @Test
    fun `a technical failure during the request is not reported as denied`() {
        identifyAna()
        pi.answer("/api/access", 200, """{"result": "error_sistema", "name": null}""")

        val result = manager.requestAccess()
        assertEquals(ResultStatus.SYSTEM_ERROR, result.status)
        assertTrue(result.status.isTechnicalFailure)
        assertFalse(result.status.isDenied)
    }

    @Test
    fun `a request cannot be sent twice for the same operation`() {
        identifyAna()
        pi.answer("/api/access", 200, """{"result": "autorizado", "name": "Ana"}""")
        manager.requestAccess()

        assertThrows(IllegalStateException::class.java) { manager.requestAccess() }
        assertEquals(1, pi.callsTo("/api/access").size)
    }

    private val photo = listOf(byteArrayOf(1, 2, 3))

    @Test
    fun `a recognized face with access ends in the authorized result`() {
        pi.answer("/api/access/face", 200, """{"result": "autorizado", "name": "Hugo"}""")
        assertEquals(FaceOutcome.RESULT, manager.requestAccessByFace(photo))
        assertEquals(ResultStatus.AUTHORIZED, manager.lastResult?.status)
        assertEquals("Hugo", manager.lastResult?.userName)
        assertEquals(AppState.SHOWING_RESULT, manager.state)
        assertTrue("no code or key is sent", pi.callsTo("/api/login").isEmpty())
    }

    @Test
    fun `a recognized face without access is a denial, not a fallback`() {
        pi.answer("/api/access/face", 200, """{"result": "denegado_sin_permiso", "name": "Beto"}""")
        assertEquals(FaceOutcome.RESULT, manager.requestAccessByFace(photo))
        assertEquals(ResultStatus.DENIED_NO_PERMISSION, manager.lastResult?.status)
    }

    @Test
    fun `a face that does not work sends the user to the code and key`() {
        val cases = mapOf(
            """{"result": "rostro_no_reconocido", "name": null}""" to FaceOutcome.NOT_RECOGNIZED,
            """{"result": "sin_rostro", "name": null}""" to FaceOutcome.NO_FACE,
            """{"result": "error_sistema", "name": null}""" to FaceOutcome.SYSTEM_ERROR,
            """{"result": "algo_nuevo"}""" to FaceOutcome.SYSTEM_ERROR,
        )
        for ((body, expected) in cases) {
            pi.answer("/api/access/face", 200, body)
            assertEquals(body, expected, manager.requestAccessByFace(photo))
            assertEquals(body, AppState.IDLE, manager.state)
            assertNull(body, manager.lastResult)
        }
        pi.answer("/api/access/face", 503, """{"result": "rostro_no_disponible"}""")
        assertEquals(FaceOutcome.UNAVAILABLE, manager.requestAccessByFace(photo))
    }

    @Test
    fun `a facial access without connection is not a denial`() {
        pi.answer("/api/access/face", 500, "boom")
        assertEquals(FaceOutcome.CONNECTION_ERROR, manager.requestAccessByFace(photo))
        assertEquals(AppState.IDLE, manager.state)
    }

    @Test
    fun `no photos means no request`() {
        assertEquals(FaceOutcome.NO_FACE, manager.requestAccessByFace(emptyList()))
        assertTrue(pi.calls.isEmpty())
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
