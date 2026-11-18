package com.controlaccesorpi.mobile

import android.content.Intent
import android.os.Looper
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.test.core.app.ApplicationProvider
import com.controlaccesorpi.mobile.model.AppState
import com.controlaccesorpi.mobile.ui.IdentificationActivity
import com.controlaccesorpi.mobile.ui.RequestActivity
import com.controlaccesorpi.mobile.ui.ResultActivity
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows.shadowOf
import org.robolectric.android.controller.ActivityController
import org.robolectric.annotation.Config

/**
 * Runs the three views on the PC, with the real layouts and the real
 * logic, against a server that answers like the Raspberry Pi.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class ScreensTest {

    private val pi = FakeRaspberry()
    private val app: AccessApp get() = ApplicationProvider.getApplicationContext()

    @Before
    fun pointAppAtFakeRaspberry() = app.changeServerAddress(pi.baseUrl)

    @After
    fun stop() = pi.close()

    /** Lets background work and the main thread run until [condition] holds. */
    private fun await(what: String, condition: () -> Boolean) {
        val deadline = System.currentTimeMillis() + 8_000
        while (System.currentTimeMillis() < deadline) {
            // The clock of the simulated phone only moves when told to.
            shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofMillis(100))
            if (condition()) return
            Thread.sleep(20)
        }
        fail("Timed out waiting for: $what")
    }

    private fun nextScreen(): Intent? = shadowOf(app).nextStartedActivity

    private fun openIdentification(): ActivityController<IdentificationActivity> =
        Robolectric.buildActivity(IdentificationActivity::class.java).setup()

    private fun identify(screen: IdentificationActivity, id: String, pin: String) {
        screen.findViewById<EditText>(R.id.idField).setText(id)
        screen.findViewById<EditText>(R.id.pinField).setText(pin)
        screen.findViewById<Button>(R.id.identifyButton).performClick()
    }

    /** Goes through identification and the request, and returns the result screen. */
    private fun requestAccessAndOpenResult(accessAnswer: String): ResultActivity {
        pi.answer("/api/login", 200, """{"identified": true, "name": "Ana"}""")
        pi.answer("/api/access", 200, accessAnswer)

        identify(openIdentification().get(), "12", "123")
        await("the request screen") { app.manager.state == AppState.IDENTIFIED }
        assertEquals(RequestActivity::class.java.name, nextScreen()?.component?.className)

        val request = Robolectric.buildActivity(RequestActivity::class.java).setup().get()
        val button = request.findViewById<Button>(R.id.requestButton)
        await("the request to be enabled") { button.isEnabled }
        button.performClick()
        await("the result") { app.manager.state == AppState.SHOWING_RESULT && request.isFinishing }
        assertEquals(ResultActivity::class.java.name, nextScreen()?.component?.className)

        return Robolectric.buildActivity(ResultActivity::class.java).setup().get()
    }

    private fun title(screen: ResultActivity) = screen.findViewById<TextView>(R.id.resultTitle).text.toString()
    private fun detail(screen: ResultActivity) = screen.findViewById<TextView>(R.id.resultDetail).text.toString()

    @Test
    fun `a wrong code or key shows one message and stays on the form`() {
        pi.answer("/api/login", 200, """{"identified": false, "name": null}""")
        val screen = openIdentification().get()
        val message = screen.findViewById<TextView>(R.id.messageText)

        identify(screen, "12", "999")
        await("the error message") { message.visibility == View.VISIBLE }

        assertEquals(screen.getString(R.string.identify_not_recognized), message.text.toString())
        assertNull(nextScreen())
    }

    @Test
    fun `a technical failure while identifying is not shown as a wrong code or key`() {
        pi.answer("/api/login", 503, """{"result": "error_sistema"}""")
        val screen = openIdentification().get()
        val message = screen.findViewById<TextView>(R.id.messageText)

        identify(screen, "12", "123")
        await("the error message") { message.visibility == View.VISIBLE }

        assertEquals(screen.getString(R.string.identify_connection_error), message.text.toString())
        assertNull(nextScreen())
    }

    @Test
    fun `an incomplete form is not sent`() {
        val screen = openIdentification().get()
        val message = screen.findViewById<TextView>(R.id.messageText)

        identify(screen, "", "")
        await("the error message") { message.visibility == View.VISIBLE }

        assertEquals(screen.getString(R.string.identify_invalid_format), message.text.toString())
        assertTrue(pi.calls.isEmpty())
    }

    @Test
    fun `the request button is enabled right after identifying, without the PIR`() {
        pi.answer("/api/login", 200, """{"identified": true, "name": "Ana"}""")
        identify(openIdentification().get(), "12", "123")
        await("the identification") { app.manager.state == AppState.IDENTIFIED }

        val request = Robolectric.buildActivity(RequestActivity::class.java).setup().get()
        val button = request.findViewById<Button>(R.id.requestButton)
        val status = request.findViewById<TextView>(R.id.statusText)
        assertEquals("Hola, Ana", request.findViewById<TextView>(R.id.greetingText).text.toString())

        shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofSeconds(3))
        assertTrue(button.isEnabled)
        assertEquals(request.getString(R.string.request_ready), status.text.toString())
        assertTrue("the app must not ask for presence", pi.callsTo("/api/presence").isEmpty())
        assertTrue(pi.callsTo("/api/access").isEmpty())
    }

    @Test
    fun `an authorized access is shown and the app goes back to the start`() {
        val result = requestAccessAndOpenResult("""{"result": "autorizado", "name": "Ana"}""")

        assertEquals("Acceso autorizado", title(result))
        assertEquals("Bienvenido, Ana.", detail(result))
        assertEquals(1, pi.callsTo("/api/access").size)

        result.findViewById<Button>(R.id.doneButton).performClick()
        assertTrue(result.isFinishing)

        // Back on the form: nothing is left from the operation (FR-19).
        val form = openIdentification().get()
        assertEquals(AppState.IDLE, app.manager.state)
        assertNull(app.manager.currentUser)
        assertNull(app.manager.lastResult)
        assertEquals("", form.findViewById<EditText>(R.id.idField).text.toString())
        assertEquals("", form.findViewById<EditText>(R.id.pinField).text.toString())
    }

    @Test
    fun `a denied access is shown as denied`() {
        val result = requestAccessAndOpenResult("""{"result": "denegado_sin_permiso", "name": "Beto"}""")
        assertEquals("Acceso rechazado", title(result))
        assertEquals(result.getString(R.string.result_denied_no_permission), detail(result))
    }

    @Test
    fun `a technical failure is shown as not completed, never as denied`() {
        val result = requestAccessAndOpenResult("""{"result": "error_sistema", "name": null}""")
        assertEquals("No se pudo completar", title(result))
        assertEquals(result.getString(R.string.result_failed_system), detail(result))
    }

    @Test
    fun `the result screen closes by itself`() {
        val result = requestAccessAndOpenResult("""{"result": "autorizado", "name": "Ana"}""")
        assertFalse(result.isFinishing)
        shadowOf(Looper.getMainLooper()).idleFor(java.time.Duration.ofSeconds(9))
        assertTrue(result.isFinishing)
    }
}
