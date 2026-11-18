package com.controlaccesorpi.mobile.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Size
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.core.resolutionselector.ResolutionSelector
import androidx.camera.core.resolutionselector.ResolutionStrategy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.controlaccesorpi.mobile.AccessApp
import com.controlaccesorpi.mobile.R
import com.controlaccesorpi.mobile.logic.FaceOutcome
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlin.coroutines.resume

/**
 * The app opens here: the user looks at the front camera and enters with
 * their face (FR-22). The photos go to the Raspberry Pi, which identifies
 * the face and decides. If the face does not work, the app goes to the
 * code and key form and says why; a recognized user without access gets
 * the denial instead, because their key would give the same answer.
 */
class FaceActivity : AppCompatActivity() {

    private val app get() = application as AccessApp

    private lateinit var preview: PreviewView
    private lateinit var statusText: TextView
    private lateinit var faceButton: Button
    private lateinit var codeButton: Button
    private lateinit var progress: View

    private var imageCapture: ImageCapture? = null
    private var busy = false

    private val askCameraPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) startCamera() else cameraUnavailable(R.string.face_no_permission)
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_face)

        preview = findViewById(R.id.preview)
        statusText = findViewById(R.id.statusText)
        faceButton = findViewById(R.id.faceButton)
        codeButton = findViewById(R.id.codeButton)
        progress = findViewById(R.id.progress)

        faceButton.setOnClickListener { onFaceClicked() }
        codeButton.setOnClickListener { openForm(null) }
        findViewById<Button>(R.id.connectionButton).setOnClickListener { askServerAddress() }

        faceButton.isEnabled = false
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) ==
            PackageManager.PERMISSION_GRANTED
        ) {
            startCamera()
        } else {
            askCameraPermission.launch(Manifest.permission.CAMERA)
        }
    }

    override fun onResume() {
        super.onResume()
        setBusy(false)
    }

    private fun startCamera() {
        val future = try {
            ProcessCameraProvider.getInstance(this)
        } catch (_: Exception) {
            cameraUnavailable(R.string.face_no_camera)
            return
        }
        future.addListener({
            try {
                val provider = future.get()
                val selector = when {
                    provider.hasCamera(CameraSelector.DEFAULT_FRONT_CAMERA) -> CameraSelector.DEFAULT_FRONT_CAMERA
                    provider.hasCamera(CameraSelector.DEFAULT_BACK_CAMERA) -> CameraSelector.DEFAULT_BACK_CAMERA
                    else -> null
                }
                if (selector == null) {
                    cameraUnavailable(R.string.face_no_camera)
                    return@addListener
                }

                val shown = Preview.Builder().build().also { it.surfaceProvider = preview.surfaceProvider }
                val capture = ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                    .setResolutionSelector(
                        ResolutionSelector.Builder()
                            .setResolutionStrategy(
                                ResolutionStrategy(
                                    Size(1280, 960),
                                    ResolutionStrategy.FALLBACK_RULE_CLOSEST_LOWER_THEN_HIGHER,
                                )
                            )
                            .build()
                    )
                    .build()

                provider.unbindAll()
                provider.bindToLifecycle(this, selector, shown, capture)
                imageCapture = capture
                faceButton.isEnabled = !busy
            } catch (_: Exception) {
                cameraUnavailable(R.string.face_no_camera)
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun cameraUnavailable(message: Int) {
        imageCapture = null
        faceButton.isEnabled = false
        statusText.setText(message)
    }

    private fun onFaceClicked() {
        val capture = imageCapture ?: return
        if (busy) return
        setBusy(true)
        statusText.setText(R.string.face_capturing)

        lifecycleScope.launch {
            val photos = mutableListOf<ByteArray>()
            repeat(PHOTOS) { index ->
                if (index > 0) delay(PHOTO_INTERVAL_MS)
                val taken = takePhoto(capture) ?: return@repeat
                withContext(Dispatchers.Default) { FacePhotos.prepare(taken.first, taken.second) }
                    ?.let { photos.add(it) }
            }

            if (photos.isEmpty()) {
                setBusy(false)
                cameraUnavailable(R.string.face_no_camera)
                return@launch
            }

            statusText.setText(R.string.face_sending)
            val outcome = withContext(Dispatchers.IO) { app.manager.requestAccessByFace(photos) }
            photos.clear()

            when (outcome) {
                FaceOutcome.RESULT -> startActivity(Intent(this@FaceActivity, ResultActivity::class.java))
                FaceOutcome.NOT_RECOGNIZED -> openForm(getString(R.string.face_not_recognized))
                FaceOutcome.NO_FACE -> openForm(getString(R.string.face_no_face))
                FaceOutcome.UNAVAILABLE -> openForm(getString(R.string.face_unavailable))
                FaceOutcome.SYSTEM_ERROR -> openForm(getString(R.string.face_system_error))
                FaceOutcome.CONNECTION_ERROR -> openForm(getString(R.string.identify_connection_error))
            }
        }
    }

    /** Takes one photo and returns its JPEG bytes and rotation, or null if it failed. */
    private suspend fun takePhoto(capture: ImageCapture): Pair<ByteArray, Int>? =
        suspendCancellableCoroutine { continuation ->
            capture.takePicture(
                ContextCompat.getMainExecutor(this),
                object : ImageCapture.OnImageCapturedCallback() {
                    override fun onCaptureSuccess(image: ImageProxy) {
                        val photo = try {
                            val buffer = image.planes[0].buffer
                            val bytes = ByteArray(buffer.remaining()).also { buffer.get(it) }
                            bytes to image.imageInfo.rotationDegrees
                        } finally {
                            image.close()
                        }
                        if (continuation.isActive) continuation.resume(photo)
                    }

                    override fun onError(exception: ImageCaptureException) {
                        if (continuation.isActive) continuation.resume(null)
                    }
                },
            )
        }

    /** Goes to the code and key form; [message] says why, when the face did not work. */
    private fun openForm(message: String?) {
        setBusy(false)
        startActivity(
            Intent(this, IdentificationActivity::class.java)
                .putExtra(IdentificationActivity.EXTRA_MESSAGE, message)
        )
    }

    private fun setBusy(value: Boolean) {
        busy = value
        faceButton.isEnabled = !value && imageCapture != null
        codeButton.isEnabled = !value
        progress.visibility = if (value) View.VISIBLE else View.INVISIBLE
        if (!value && imageCapture != null) statusText.text = ""
    }

    companion object {
        /** Photos per attempt: if one is blurry, another may still work. */
        const val PHOTOS = 3
        private const val PHOTO_INTERVAL_MS = 300L
    }
}
