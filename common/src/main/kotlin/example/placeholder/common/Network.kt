package example.placeholder.common

import kotlinx.coroutines.suspendCancellableCoroutine
import okhttp3.Call
import okhttp3.Callback
import okhttp3.Headers
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import java.io.ByteArrayOutputStream
import java.io.IOException
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/** No private clients, cookie jars or retry loops. Reuse the host-owned HTTP stack. */
suspend fun readText(
    client: OkHttpClient,
    url: String,
    headers: Headers,
): String =
    suspendCancellableCoroutine { continuation ->
        val call =
            client.newCall(
                Request
                    .Builder()
                    .url(url)
                    .headers(headers)
                    .build(),
            )
        continuation.invokeOnCancellation { call.cancel() }
        call.enqueue(
            object : Callback {
                override fun onFailure(
                    call: Call,
                    error: IOException,
                ) {
                    if (continuation.isActive) continuation.resumeWithException(error)
                }

                override fun onResponse(
                    call: Call,
                    response: Response,
                ) {
                    try {
                        val result =
                            response.use {
                                if (!it.isSuccessful) throw IOException("Source returned HTTP ${it.code}")
                                val output = ByteArrayOutputStream()
                                it.body.byteStream().use { input ->
                                    val buffer = ByteArray(8192)
                                    while (true) {
                                        val count = input.read(buffer)
                                        if (count < 0) break
                                        if (output.size() + count > 1_048_576) throw IOException("Source response is too large")
                                        output.write(buffer, 0, count)
                                    }
                                }
                                output.toString(Charsets.UTF_8.name())
                            }
                        if (continuation.isActive) continuation.resume(result)
                    } catch (error: Exception) {
                        if (continuation.isActive) continuation.resumeWithException(error)
                    }
                }
            },
        )
    }
