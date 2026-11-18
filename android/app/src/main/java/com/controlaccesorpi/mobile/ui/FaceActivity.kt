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
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.controlaccesorpi.mobile.AccessApp
import com.controlaccesorpi.mobile.R
import com.controlaccesorpi.mobile.logic.AccessManager
import com.controlaccesorpi.mobile.logic.FaceOutcome
import com.controlaccesorpi.mobile.logic.PresenceStatus
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlin.coroutines.resume

/**
 * The app opens here: the user looks at the front camera and enters with
 * their face (FR-22). Like the request with code and key, it is enabled
 * only once the PIR has detected presence (FR-16). The photos go to the
 * Raspberry Pi, which identifies
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
    private var present = false
    private var presenceJob: Job? = null

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
        if (presenceJob?.isActive != true) watchPresence()
    }

    /**
     * Asks the Raspberry Pi about presence while this view is on screen.
     * "Entrar con rostro" is enabled only while the PIR reports presence,
     * like the request with code and key (FR-16, FR-22).
     */
    private fun watchPresence() {
        presenceJob = lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                while (true) {
                    val status = withContext(Dispatchers.IO) { app.manager.checkPresenceForFace() }
                    if (busy) return@repeatOnLifecycle
                    onPresenceChanged(status)
                    delay(AccessManager.PRESENCE_POLL_MS)
                }
            }
        }
    }

    private fun onPresenceChanged(status: PresenceStatus) {
        present = status == PresenceStatus.PRESENT
        faceButton.isEnabled = !busy && present && imageCapture != null
        // Without a camera the message about the camera stays on screen.
        if (imageCapture == null) return
        statusText.setText(
            when (status) {
                PresenceStatus.PRESENT -> R.string.face_presence_detected
                PresenceStatus.ABSENT -> R.string.request_waiting_presence
                PresenceStatus.UNREACHABLE -> R.string.request_unreachable
            }
        )
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
                faceButton.isEnabled = !busy && present
                statusText.setText(if (present) R.string.face_presence_detected else R.string.request_waiting_presence)
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
        if (busy || !present) return
        setBusy(true)
        presenceJob?.cancel()
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
            val outcome = withContext(Dispatchers.IO) {
                try {
                    app.manager.requestAccessByFace(photos)
                } catch (_: IllegalStateException) {
                    // Presence went away between the last check and the tap.
                    null
                }
            }
            photos.clear()

            when (outcome) {
                null -> {
                    present = false
                    setBusy(false)
                    statusText.setText(R.string.request_waiting_presence)
                    watchPresence()
                }
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
        faceButton.isEnabled = !value && present && imageCapture != null
        codeButton.isEnabled = !value
        progress.visibility = if (value) View.VISIBLE else View.INVISIBLE
    }

    companion object {
        /** Photos per attempt: if one is blurry, another may still work. */
        const val PHOTOS = 3
        private const val PHOTO_INTERVAL_MS = 300L
    }
}
