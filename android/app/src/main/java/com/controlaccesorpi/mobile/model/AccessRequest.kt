package com.controlaccesorpi.mobile.model

import org.json.JSONObject

/**
 * What the app sends to the Raspberry Pi to identify a user or to request
 * access. The Raspberry Pi decides; the request carries no permissions.
 */
class AccessRequest(
    val userId: Int,
    private val pin: String,
) {
    fun toJson(): String = JSONObject().put("id", userId).put("pin", pin).toString()

    // The key must never end up in a log.
    override fun toString(): String = "AccessRequest(userId=$userId)"
}
