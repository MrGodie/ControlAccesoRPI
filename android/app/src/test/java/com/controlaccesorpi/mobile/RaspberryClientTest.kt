package com.controlaccesorpi.mobile

import com.controlaccesorpi.mobile.model.ResultStatus
import com.controlaccesorpi.mobile.model.User
import com.controlaccesorpi.mobile.network.ConnectionException
import com.controlaccesorpi.mobile.network.RaspberryClient
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import java.net.ServerSocket

class RaspberryClientTest {

    private val pi = FakeRaspberry()
    private val client = RaspberryClient(pi.baseUrl, connectTimeoutMs = 1_000, readTimeoutMs = 1_000)
    private val user = User(12, "123")

    @After
    fun stop() = pi.close()

    /** An address where nothing is listening. */
    private fun deadUrl(): String = ServerSocket(0).use { "http://127.0.0.1:${it.localPort}" }

    @Test
    fun `identify returns the name and sends the code and key`() {
        pi.answer("/api/login", 200, """{"identified": true, "name": "Ana"}""")

        assertEquals("Ana", client.identify(user))

        val call = pi.callsTo("/api/login").single()
        assertEquals("POST", call.method)
        val sent = JSONObject(call.body)
        assertEquals(12, sent.getInt("id"))
        assertEquals("123", sent.getString("pin"))
    }

    @Test
    fun `identify returns null when the user is not recognized`() {
        pi.answer("/api/login", 200, """{"identified": false, "name": null}""")
        assertNull(client.identify(user))
    }

    @Test
    fun `a database failure during identification is not reported as not recognized`() {
        pi.answer("/api/login", 503, """{"result": "error_sistema"}""")
        assertThrows(ConnectionException::class.java) { client.identify(user) }
    }

    @Test
    fun `identify fails as a connection problem when nothing answers`() {
        val offline = RaspberryClient(deadUrl(), connectTimeoutMs = 500, readTimeoutMs = 500)
        assertThrows(ConnectionException::class.java) { offline.identify(user) }
    }

    @Test
    fun `an access request returns each result of the Raspberry Pi`() {
        val expected = mapOf(
            "autorizado" to ResultStatus.AUTHORIZED,
            "denegado_sin_permiso" to ResultStatus.DENIED_NO_PERMISSION,
            "denegado_no_reconocido" to ResultStatus.DENIED_NOT_RECOGNIZED,
            "error_sistema" to ResultStatus.SYSTEM_ERROR,
        )
        for ((value, status) in expected) {
            pi.answer("/api/access", 200, """{"result": "$value", "name": "Ana"}""")
            assertEquals(status, client.sendRequest(user.newAccessRequest()).status)
        }
        assertEquals("POST", pi.callsTo("/api/access").first().method)
    }

    @Test
    fun `a server error during the request is a technical failure`() {
        pi.answer("/api/access", 500, """{"result": "error_sistema"}""")
        assertEquals(ResultStatus.SYSTEM_ERROR, client.sendRequest(user.newAccessRequest()).status)
        pi.answer("/api/access", 400, """{"error": "bad"}""")
        assertEquals(ResultStatus.SYSTEM_ERROR, client.sendRequest(user.newAccessRequest()).status)
    }

    @Test
    fun `an unreachable Raspberry Pi is a connection error, not a denial`() {
        val offline = RaspberryClient(deadUrl(), connectTimeoutMs = 500, readTimeoutMs = 500)
        val result = offline.sendRequest(user.newAccessRequest())
        assertEquals(ResultStatus.CONNECTION_ERROR, result.status)
        assertFalse(result.status.isDenied)
    }

    @Test
    fun `no answer within the expected time is a connection error`() {
        pi.answer("/api/access", 200, """{"result": "autorizado", "name": "Ana"}""", delayMs = 2_500)
        val impatient = RaspberryClient(pi.baseUrl, connectTimeoutMs = 500, readTimeoutMs = 300)
        assertEquals(ResultStatus.CONNECTION_ERROR, impatient.sendRequest(user.newAccessRequest()).status)
    }

    @Test
    fun `a malformed address is a connection error`() {
        for (address in listOf("", "not a url", "ftp://192.168.1.10")) {
            val broken = RaspberryClient(address, connectTimeoutMs = 300, readTimeoutMs = 300)
            assertEquals(address, ResultStatus.CONNECTION_ERROR, broken.sendRequest(user.newAccessRequest()).status)
        }
    }

    @Test
    fun `a trailing slash in the address is accepted`() {
        pi.answer("/api/login", 200, """{"identified": true, "name": "Ana"}""")
        assertEquals("Ana", RaspberryClient(pi.baseUrl + "/").identify(user))
    }
}
