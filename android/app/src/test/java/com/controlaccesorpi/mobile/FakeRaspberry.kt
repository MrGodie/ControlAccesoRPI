package com.controlaccesorpi.mobile

import java.io.IOException
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import kotlin.concurrent.thread

/**
 * A small HTTP server that answers like the Raspberry Pi API, so the
 * tests exercise real HTTP requests without the device.
 */
class FakeRaspberry : AutoCloseable {

    class Answer(val status: Int, val body: String, val delayMs: Long = 0)

    class Call(val method: String, val path: String, val body: String)

    private val server = ServerSocket(0, 50, InetAddress.getByName("127.0.0.1"))
    private val answers = mutableMapOf<String, Answer>()
    private val recorded = mutableListOf<Call>()

    val baseUrl: String get() = "http://127.0.0.1:${server.localPort}"
    val calls: List<Call> get() = synchronized(recorded) { recorded.toList() }

    init {
        thread(isDaemon = true, name = "FakeRaspberry") {
            while (!server.isClosed) {
                val socket = try {
                    server.accept()
                } catch (_: IOException) {
                    break
                }
                thread(isDaemon = true) { serve(socket) }
            }
        }
    }

    fun answer(path: String, status: Int, body: String, delayMs: Long = 0) {
        synchronized(answers) { answers[path] = Answer(status, body, delayMs) }
    }

    fun callsTo(path: String): List<Call> = calls.filter { it.path == path }

    override fun close() = server.close()

    private fun serve(socket: Socket) {
        try {
            socket.use {
                val input = it.getInputStream()
                val requestLine = readLine(input).split(" ")
                if (requestLine.size < 2) return

                var length = 0
                while (true) {
                    val header = readLine(input)
                    if (header.isEmpty()) break
                    if (header.startsWith("content-length:", ignoreCase = true)) {
                        length = header.substringAfter(":").trim().toInt()
                    }
                }
                val body = String(input.readNBytes(length), Charsets.UTF_8)
                val path = requestLine[1]
                synchronized(recorded) { recorded.add(Call(requestLine[0], path, body)) }

                val answer = synchronized(answers) { answers[path] } ?: Answer(404, """{"error":"not found"}""")
                if (answer.delayMs > 0) Thread.sleep(answer.delayMs)

                val bytes = answer.body.toByteArray(Charsets.UTF_8)
                val head = "HTTP/1.1 ${answer.status} X\r\n" +
                    "Content-Type: application/json\r\n" +
                    "Content-Length: ${bytes.size}\r\n" +
                    "Connection: close\r\n\r\n"
                it.getOutputStream().apply {
                    write(head.toByteArray(Charsets.US_ASCII))
                    write(bytes)
                    flush()
                }
            }
        } catch (_: IOException) {
            // The client gave up waiting.
        }
    }

    private fun readLine(input: java.io.InputStream): String {
        val line = StringBuilder()
        while (true) {
            val byte = input.read()
            if (byte == -1 || byte == '\n'.code) break
            if (byte != '\r'.code) line.append(byte.toChar())
        }
        return line.toString()
    }
}
