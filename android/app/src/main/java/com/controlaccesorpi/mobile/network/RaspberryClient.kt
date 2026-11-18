package com.controlaccesorpi.mobile.network

import com.controlaccesorpi.mobile.model.AccessRequest
import com.controlaccesorpi.mobile.model.AccessResult
import com.controlaccesorpi.mobile.model.ResultStatus
import com.controlaccesorpi.mobile.model.User
import org.json.JSONException
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL

/** The Raspberry Pi could not be reached or did not give a usable answer. */
class ConnectionException(message: String, cause: Throwable? = null) : IOException(message, cause)

/**
 * HTTP communication with the Raspberry Pi, and nothing else: no screens
 * and no application rules. Every call blocks, so it must run off the
 * main thread.
 */
class RaspberryClient(
    baseUrl: String,
    private val connectTimeoutMs: Int = 5_000,
    // A request waits while the LED, the sound and the motor finish.
    private val readTimeoutMs: Int = 20_000,
) {
    private val baseUrl: String = baseUrl.trim().trimEnd('/')

    /**
     * Asks the Raspberry Pi whether the code and key belong to a registered
     * user. Returns the user's name, or null if they were not recognized.
     *
     * @throws ConnectionException on a technical failure, which must not be
     * shown as "wrong code or key".
     */
    @Throws(ConnectionException::class)
    fun identify(user: User): String? {
        val response = call("POST", "/api/login", user.newAccessRequest().toJson())
        if (response.status != HttpURLConnection.HTTP_OK) {
            throw ConnectionException("Unexpected answer to the identification: HTTP ${response.status}")
        }
        val body = parse(response.body)
        if (!body.optBoolean("identified", false)) return null
        return if (body.isNull("name")) "" else body.optString("name")
    }

    /**
     * Sends the access request. It never throws: a failure to reach the
     * Raspberry Pi comes back as [ResultStatus.CONNECTION_ERROR].
     */
    fun sendRequest(request: AccessRequest): AccessResult {
        val response = try {
            call("POST", "/api/access", request.toJson())
        } catch (_: ConnectionException) {
            return AccessResult.connectionError()
        }
        // Any answer other than a result from the validation is technical.
        if (response.status != HttpURLConnection.HTTP_OK) return AccessResult(ResultStatus.SYSTEM_ERROR)
        return AccessResult.fromJson(response.body)
    }

    private class Response(val status: Int, val body: String)

    private fun parse(body: String): JSONObject =
        try {
            JSONObject(body)
        } catch (error: JSONException) {
            throw ConnectionException("The Raspberry Pi sent an answer that is not valid JSON", error)
        }

    private fun call(method: String, path: String, body: String?): Response {
        var connection: HttpURLConnection? = null
        try {
            connection = URL(baseUrl + path).openConnection() as HttpURLConnection
            connection.requestMethod = method
            connection.connectTimeout = connectTimeoutMs
            connection.readTimeout = readTimeoutMs
            connection.useCaches = false
            connection.setRequestProperty("Accept", "application/json")

            if (body != null) {
                val bytes = body.toByteArray(Charsets.UTF_8)
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.setFixedLengthStreamingMode(bytes.size)
                connection.outputStream.use { it.write(bytes) }
            }

            val status = connection.responseCode
            val stream = if (status >= 400) connection.errorStream else connection.inputStream
            val text = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            return Response(status, text)
        } catch (error: IOException) {
            throw ConnectionException("Could not reach the Raspberry Pi at $baseUrl", error)
        } catch (error: IllegalArgumentException) {
            throw ConnectionException("The Raspberry Pi address is not valid: $baseUrl", error)
        } catch (error: ClassCastException) {
            throw ConnectionException("The Raspberry Pi address must start with http://", error)
        } finally {
            connection?.disconnect()
        }
    }
}
