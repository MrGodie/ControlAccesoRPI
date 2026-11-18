package com.controlaccesorpi.mobile.ui

import android.text.InputType
import android.widget.EditText
import android.widget.FrameLayout
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.controlaccesorpi.mobile.AccessApp
import com.controlaccesorpi.mobile.R

/**
 * Asks for the address of the Raspberry Pi ("Conexión"). Shared by the
 * camera view and the code and key view. [onSaved] runs after the new
 * address is stored.
 */
fun AppCompatActivity.askServerAddress(onSaved: () -> Unit = {}) {
    val app = application as AccessApp
    val field = EditText(this).apply {
        inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
        setText(app.settings.address)
        setSelection(text.length)
    }
    val margin = resources.getDimensionPixelSize(R.dimen.dialog_margin)
    val container = FrameLayout(this).apply {
        setPadding(margin, margin / 2, margin, 0)
        addView(field)
    }

    AlertDialog.Builder(this)
        .setTitle(R.string.connection_title)
        .setMessage(R.string.connection_message)
        .setView(container)
        .setPositiveButton(R.string.connection_save) { _, _ ->
            app.changeServerAddress(field.text.toString())
            onSaved()
        }
        .setNegativeButton(R.string.cancel, null)
        .show()
}
