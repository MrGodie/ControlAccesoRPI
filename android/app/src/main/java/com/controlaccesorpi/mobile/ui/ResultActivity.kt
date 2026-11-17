package com.controlaccesorpi.mobile.ui

import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.controlaccesorpi.mobile.AccessApp
import com.controlaccesorpi.mobile.R
import com.controlaccesorpi.mobile.model.AccessResult
import com.controlaccesorpi.mobile.model.ResultStatus
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * Third view: shows whether access was authorized, denied, or could not
 * be completed for a technical reason (FR-18), then goes back to the
 * start. A technical failure is never shown as a denial (NFR-11).
 */
class ResultActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_result)

        val result = (application as AccessApp).manager.lastResult
        if (result == null) {
            finish()
            return
        }

        showResult(result)
        findViewById<Button>(R.id.doneButton).setOnClickListener { finish() }

        // onTimeout: back to the start without waiting for the user.
        lifecycleScope.launch {
            delay(SHOW_RESULT_MS)
            finish()
        }
    }

    /** Leaving this view ends the operation and forgets the user (FR-19). */
    override fun onDestroy() {
        if (isFinishing) (application as AccessApp).manager.reset()
        super.onDestroy()
    }

    private fun showResult(result: AccessResult) {
        val (title, detail, color) = when (result.status) {
            ResultStatus.AUTHORIZED -> Triple(
                getString(R.string.result_authorized_title),
                if (result.userName.isNullOrBlank()) getString(R.string.result_authorized_detail_no_name)
                else getString(R.string.result_authorized_detail, result.userName),
                R.color.result_authorized,
            )
            ResultStatus.DENIED_NO_PERMISSION -> Triple(
                getString(R.string.result_denied_title),
                getString(R.string.result_denied_no_permission),
                R.color.result_denied,
            )
            ResultStatus.DENIED_NOT_RECOGNIZED -> Triple(
                getString(R.string.result_denied_title),
                getString(R.string.result_denied_not_recognized),
                R.color.result_denied,
            )
            ResultStatus.SYSTEM_ERROR -> Triple(
                getString(R.string.result_failed_title),
                getString(R.string.result_failed_system),
                R.color.result_failed,
            )
            ResultStatus.CONNECTION_ERROR -> Triple(
                getString(R.string.result_failed_title),
                getString(R.string.result_failed_connection),
                R.color.result_failed,
            )
        }

        findViewById<View>(R.id.resultBanner).setBackgroundColor(ContextCompat.getColor(this, color))
        findViewById<TextView>(R.id.resultTitle).text = title
        findViewById<TextView>(R.id.resultDetail).text = detail
    }

    companion object {
        private const val SHOW_RESULT_MS = 8_000L
    }
}
