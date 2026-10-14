pluginManagement {
    buildscript {
        repositories {
            mavenCentral()
            maven("https://storage.googleapis.com/r8-releases/raw")
        }
        dependencies { classpath("com.android.tools:r8:9.1.29") }
    }
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven("https://www.jitpack.io")
    }
}
rootProject.name = "PlaceholderExtensions"
include(":common", ":video", ":manga", ":news", ":tv")
