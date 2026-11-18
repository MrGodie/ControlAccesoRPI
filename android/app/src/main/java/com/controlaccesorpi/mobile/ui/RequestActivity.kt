package com.controlaccesorpi.mobile.ui

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.controlaccesorpi.mobile.AccessApp
import com.controlaccesorpi.mobile.R
import com.controlaccesorpi.mobile.logic.AccessManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Second view: the identified user requests access. The request is
 * enabled as soon as the user is identified; the app does not wait for
 * the PIR sensor (FR-16, PIC-115). The Raspberry Pi decides the result.
 */
class RequestActivity : AppCompatActivity() {

    private val manager: AccessManager get() = (application as AccessApp).manager

    private lateinit var statusText: TextView
    private lateinit var requestButton: Button
    private lateinit var cancelButton: Button
    private lateinit var progress: View

    private var sending = false

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

        showReady()
    }

    private fun showReady() {
        requestButton.isEnabled = manager.canRequestAccess()
        statusText.setText(R.string.request_ready)
    }

    private fun onRequestClicked() {
        if (sending) return
        sending = true

        requestButton.isEnabled = false
        cancelButton.isEnabled = false
        progress.visibility = View.VISIBLE
        statusText.setText(R.string.request_sending)

        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                try {
                    manager.requestAccess()
                } catch (_: IllegalStateException) {
                    // The operation was reset before the tap (for example,
                    // the user identified again): nothing was sent.
                    null
                }
            }

            if (result == null) {
                sending = false
                cancelButton.isEnabled = true
                progress.visibility = View.INVISIBLE
                showReady()
            } else {
                startActivity(Intent(this@RequestActivity, ResultActivity::class.java))
                finish()
            }
        }
    }
}
