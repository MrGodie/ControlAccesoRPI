package com.controlaccesorpi.mobile.ui

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import java.io.ByteArrayOutputStream
import kotlin.math.max

/**
 * Prepares a photo from the camera before sending it to the Raspberry Pi:
 * upright, small, and JPEG. The face detector needs the face upright, and
 * a small photo travels fast and is enough for the recognition model.
 * Nothing is written to the phone (NFR-13).
 */
object FacePhotos {

    /** Longest side of the photo that is sent. */
    const val MAX_SIDE = 640
    private const val JPEG_QUALITY = 85

    /** Returns the photo ready to send, or null if it could not be decoded. */
    fun prepare(jpeg: ByteArray, rotationDegrees: Int): ByteArray? {
        val original = BitmapFactory.decodeByteArray(jpeg, 0, jpeg.size) ?: return null

        val scale = minOf(1f, MAX_SIDE.toFloat() / max(original.width, original.height))
        val matrix = Matrix().apply {
            postScale(scale, scale)
            postRotate(rotationDegrees.toFloat())
        }
        val ready = Bitmap.createBitmap(original, 0, 0, original.width, original.height, matrix, true)

        val out = ByteArrayOutputStream()
        ready.compress(Bitmap.CompressFormat.JPEG, JPEG_QUALITY, out)
        if (ready !== original) ready.recycle()
        original.recycle()
        return out.toByteArray()
    }
}
