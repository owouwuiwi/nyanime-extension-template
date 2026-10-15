package example.placeholder.addon

import android.app.Activity
import android.content.Context
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import nyanime.addon.api.HostedAddon
import nyanime.addon.api.RinAddonHost
import nyanime.addon.api.RinAddonTask

class AddonFactory : HostedAddon {
    override fun createView(activity: Activity, context: Context, host: RinAddonHost): View =
        LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            val padding = (24 * context.resources.displayMetrics.density).toInt()
            setPadding(padding, padding, padding, padding)
            addView(TextView(context).apply {
                text = "Hosted addon demo"
                textSize = 24f
            })
            addView(TextView(context).apply {
                text = "The same signed APK works installed or imported. No Android components are registered."
                textSize = 16f
            })
            addView(Button(context).apply { text = "Back to Nyanime"; setOnClickListener { host.close() } })
        }
    override fun startTask(context: Context, name: String, arguments: Bundle, task: RinAddonTask) =
        throw UnsupportedOperationException("The demo does not run background tasks")
    override fun cancelTask(context: Context, name: String) = Unit
    override fun runPeriodicTask(context: Context, name: String, host: RinAddonHost): Int = 2
}
