package com.controlaccesorpi.mobile.ui

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.controlaccesorpi.mobile.AccessApp
import com.controlaccesorpi.mobile.R
import com.controlaccesorpi.mobile.logic.IdentifyOutcome
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * The user types their code and key. It only shows the form and the
 * outcome; identifying is done by AccessManager. It opens from the camera
 * view, by choice or because the facial access did not work (FR-22).
 */
class IdentificationActivity : AppCompatActivity() {

    private val app get() = application as AccessApp

    private lateinit var idField: EditText
    private lateinit var pinField: EditText
    private lateinit var identifyButton: Button
    private lateinit var messageText: TextView
    private lateinit var progress: View

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_identification)

        idField = findViewById(R.id.idField)
        pinField = findViewById(R.id.pinField)
        identifyButton = findViewById(R.id.identifyButton)
        messageText = findViewById(R.id.messageText)
        progress = findViewById(R.id.progress)

        identifyButton.setOnClickListener { onIdentifyClicked() }
        findViewById<Button>(R.id.connectionButton).setOnClickListener {
            askServerAddress { showError(null) }
        }

        // Coming from a facial access that did not work: say why (FR-22).
        intent.getStringExtra(EXTRA_MESSAGE)?.let { showError(it) }
    }

    /** Every time this view comes back, the operation starts from zero (FR-19). */
    override fun onResume() {
        super.onResume()
        app.manager.reset()
        idField.text.clear()
        pinField.text.clear()
        setBusy(false)
    }

    private fun onIdentifyClicked() {
        val id = idField.text.toString()
        val pin = pinField.text.toString()
        val manager = app.manager

        showError(null)
        setBusy(true)

        lifecycleScope.launch {
            val outcome = withContext(Dispatchers.IO) { manager.identify(id, pin) }
            setBusy(false)

            when (outcome) {
                IdentifyOutcome.IDENTIFIED ->
                    startActivity(Intent(this@IdentificationActivity, RequestActivity::class.java))
                IdentifyOutcome.INVALID_FORMAT -> showError(getString(R.string.identify_invalid_format))
                // One message for both fields: it never says which one was wrong (FR-15).
                IdentifyOutcome.NOT_RECOGNIZED -> showError(getString(R.string.identify_not_recognized))
                // A technical failure is not a wrong code or key (NFR-11).
                IdentifyOutcome.CONNECTION_ERROR -> showError(getString(R.string.identify_connection_error))
            }
        }
    }

    private fun showError(message: String?) {
        messageText.text = message.orEmpty()
        messageText.visibility = if (message == null) View.INVISIBLE else View.VISIBLE
    }

    private fun setBusy(busy: Boolean) {
        identifyButton.isEnabled = !busy
        idField.isEnabled = !busy
        pinField.isEnabled = !busy
        progress.visibility = if (busy) View.VISIBLE else View.INVISIBLE
    }

    companion object {
        /** Why the facial access sent the user here; shown above the form. */
        const val EXTRA_MESSAGE = "com.controlaccesorpi.mobile.FALLBACK_MESSAGE"
    }
}
