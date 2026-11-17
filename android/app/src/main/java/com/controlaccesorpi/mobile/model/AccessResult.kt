package com.controlaccesorpi.mobile.model

import org.json.JSONException
import org.json.JSONObject

/** Result of one access request, as shown on the result screen. */
class AccessResult(
    val status: ResultStatus,
    val userName: String? = null,
) {
    fun isAuthorized(): Boolean = status == ResultStatus.AUTHORIZED

    companion object {
        /** Parses the body of `POST /api/access`: `{"result": ..., "name": ...}`. */
        fun fromJson(json: String): AccessResult =
            try {
                val body = JSONObject(json)
                AccessResult(
                    status = ResultStatus.fromApi(body.optString("result")),
                    userName = if (body.isNull("name")) null else body.optString("name"),
                )
            } catch (_: JSONException) {
                AccessResult(ResultStatus.SYSTEM_ERROR)
            }

        fun connectionError(): AccessResult = AccessResult(ResultStatus.CONNECTION_ERROR)
    }
}
