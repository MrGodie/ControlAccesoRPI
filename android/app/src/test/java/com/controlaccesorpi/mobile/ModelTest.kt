package com.controlaccesorpi.mobile

import com.controlaccesorpi.mobile.model.AccessRequest
import com.controlaccesorpi.mobile.model.AccessResult
import com.controlaccesorpi.mobile.model.ResultStatus
import com.controlaccesorpi.mobile.model.User
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ModelTest {

    @Test
    fun `the four results of the Raspberry Pi are told apart`() {
        assertEquals(ResultStatus.AUTHORIZED, ResultStatus.fromApi("autorizado"))
        assertEquals(ResultStatus.DENIED_NO_PERMISSION, ResultStatus.fromApi("denegado_sin_permiso"))
        assertEquals(ResultStatus.DENIED_NOT_RECOGNIZED, ResultStatus.fromApi("denegado_no_reconocido"))
        assertEquals(ResultStatus.SYSTEM_ERROR, ResultStatus.fromApi("error_sistema"))
    }

    @Test
    fun `an unknown result is a technical failure, never a denial`() {
        for (value in listOf("", "otro", null)) {
            val status = ResultStatus.fromApi(value)
            assertEquals(ResultStatus.SYSTEM_ERROR, status)
            assertTrue(status.isTechnicalFailure)
            assertFalse(status.isDenied)
        }
    }

    @Test
    fun `denied and technical failure never overlap`() {
        for (status in ResultStatus.entries) {
            assertFalse("$status", status.isDenied && status.isTechnicalFailure)
        }
        assertTrue(ResultStatus.CONNECTION_ERROR.isTechnicalFailure)
        assertTrue(ResultStatus.DENIED_NO_PERMISSION.isDenied)
        assertTrue(ResultStatus.DENIED_NOT_RECOGNIZED.isDenied)
    }

    @Test
    fun `an authorized answer is parsed with the user name`() {
        val result = AccessResult.fromJson("""{"result": "autorizado", "name": "Ana"}""")
        assertTrue(result.isAuthorized())
        assertEquals("Ana", result.userName)
    }

    @Test
    fun `a denied answer without a name is parsed`() {
        val result = AccessResult.fromJson("""{"result": "denegado_no_reconocido", "name": null}""")
        assertFalse(result.isAuthorized())
        assertEquals(ResultStatus.DENIED_NOT_RECOGNIZED, result.status)
        assertNull(result.userName)
    }

    @Test
    fun `an answer that is not JSON is a technical failure`() {
        assertEquals(ResultStatus.SYSTEM_ERROR, AccessResult.fromJson("<html>500</html>").status)
        assertEquals(ResultStatus.SYSTEM_ERROR, AccessResult.fromJson("{}").status)
    }

    @Test
    fun `the form accepts only a numeric code and key`() {
        assertNotNull(User.fromInput("12", "123"))
        assertNotNull(User.fromInput(" 12 ", "123"))
        for ((id, pin) in listOf(
            "" to "123", "12" to "", "abc" to "123", "12" to "12a",
            "0" to "123", "-1" to "123", "123456789" to "123", "12" to "1 2",
        )) {
            assertNull("id='$id' pin='$pin'", User.fromInput(id, pin))
        }
    }

    @Test
    fun `the request carries the code and key and nothing else`() {
        val json = JSONObject(User(12, "123").newAccessRequest().toJson())
        assertEquals(12, json.getInt("id"))
        assertEquals("123", json.getString("pin"))
        assertEquals(2, json.length())
    }

    @Test
    fun `the key never appears in a text representation`() {
        val user = User(12, "98765", "Ana")
        assertFalse(user.toString().contains("98765"))
        assertFalse(user.newAccessRequest().toString().contains("98765"))
        assertFalse(AccessRequest(12, "98765").toString().contains("98765"))
    }
}
