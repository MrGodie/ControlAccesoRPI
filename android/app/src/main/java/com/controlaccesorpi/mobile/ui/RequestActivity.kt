package com.controlaccesorpi.mobile.ui

import android.content.Intent
import android.os.Bundle
import android.os.SystemClock
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.controlaccesorpi.mobile.AccessApp
import com.controlaccesorpi.mobile.R
import com.controlaccesorpi.mobile.logic.AccessManager
import com.controlaccesorpi.mobile.logic.PresenceStatus
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Second view: the identified user waits for the PIR sensor to detect
 * presence and then requests access. The button starts disabled and is
 * enabled only while the Raspberry Pi reports presence (FR-16).
 *
 * Presence enables the request; it does not authorize access.
 */
class RequestActivity : AppCompatActivity() {

    private val manager: AccessManager get() = (application as AccessApp).manager

    private lateinit var statusText: TextView
    private lateinit var requestButton: Button
    private lateinit var cancelButton: Button
    private lateinit var progress: View

    private var presenceJob: Job? = null
    private var sending = false
    private var openedAt = 0L

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_request)

        val user = manager.currentUser
        if (user == null) {
            finish()
            return
        }

        statusText = findViewById(R.id.statusText)
        requestButton = findViewById(R.id.requestButton)
        cancelButton = findViewById(R.id.cancelButton)
        progress = findViewById(R.id.progress)

        findViewById<TextView>(R.id.greetingText).text =
            if (user.name.isNullOrBlank()) getString(R.string.request_greeting_no_name)
            else getString(R.string.request_greeting, user.name)

        requestButton.setOnClickListener { onRequestClicked() }
        cancelButton.setOnClickListener { finish() }

        openedAt = SystemClock.elapsedRealtime()
        onPresenceChanged(PresenceStatus.ABSENT)
        watchPresence()
    }

    /** Asks the Raspberry Pi about presence while this view is on screen. */
    private fun watchPresence() {
        presenceJob = lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                while (true) {
                    val status = withContext(Dispatchers.IO) { manager.checkPresence() }
                    if (sending) return@repeatOnLifecycle
                    onPresenceChanged(status)

                    // Nobody came to the access point: forget the user and go back.
                    if (status != PresenceStatus.PRESENT &&
                        SystemClock.elapsedRealtime() - openedAt > WAIT_LIMIT_MS
                    ) {
                        finish()
                        return@repeatOnLifecycle
                    }
                    delay(AccessManager.PRESENCE_POLL_MS)
                }
            }
        }
    }

    private fun onPresenceChanged(status: PresenceStatus) {
        requestButton.isEnabled = status == PresenceStatus.PRESENT
        statusText.setText(
            when (status) {
                PresenceStatus.PRESENT -> R.string.request_presence_detected
                PresenceStatus.ABSENT -> R.string.request_waiting_presence
                PresenceStatus.UNREACHABLE -> R.string.request_unreachable
            }
        )
    }

    private fun onRequestClicked() {
        if (sending) return
        sending = true
        presenceJob?.cancel()

        requestButton.isEnabled = false
        cancelButton.isEnabled = false
        progress.visibility = View.VISIBLE
        statusText.setText(R.string.request_sending)

        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                try {
                    manager.requestAccess()
                } catch (_: IllegalStateException) {
                    // Presence went away between the last check and the tap.
                    null
                }
            }

            if (result == null) {
                sending = false
                cancelButton.isEnabled = true
                progress.visibility = View.INVISIBLE
                onPresenceChanged(PresenceStatus.ABSENT)
                watchPresence()
            } else {
                startActivity(Intent(this@RequestActivity, ResultActivity::class.java))
                finish()
            }
        }
    }

    companion object {
        /** How long an identified user may wait for presence before the app starts over. */
        private const val WAIT_LIMIT_MS = 60_000L
    }
}
