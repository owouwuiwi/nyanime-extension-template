package example.placeholder.guide

import android.content.Context
import nyanime.addon.api.EpisodeGuideProvider

/** No fictional classification is presented as a real guide. */
class GuideFactory : EpisodeGuideProvider {
    override fun search(context: Context, requestId: String, identityJson: String): String = "{\"schema\":1,\"results\":[]}"
    override fun guide(context: Context, requestId: String, reference: String): String =
        throw IllegalArgumentException("The synthetic provider has no external work references")
    override fun cancel(requestId: String) = Unit
}
