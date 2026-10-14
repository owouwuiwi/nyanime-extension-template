import groovy.json.JsonSlurper

plugins {
    id("com.android.application") version "8.10.1" apply false
    kotlin("android") version "2.4.0" apply false
    kotlin("jvm") version "2.4.0" apply false
}

// One editable file supplies package identity, source IDs, language and website.
val template = JsonSlurper().parse(file("template.json")) as Map<*, *>
val modules = template["modules"] as Map<*, *>
extra["template"] = template

subprojects {
    if (name != "common") {
        apply(plugin = "com.android.application")
        apply(plugin = "org.jetbrains.kotlin.android")
        val module = modules[name] as Map<*, *>
        extensions.configure<com.android.build.gradle.AppExtension> {
            namespace = "example.placeholder.$name"
            compileSdkVersion(36)
            buildToolsVersion = "35.0.1"
            defaultConfig {
                applicationId = module["package"].toString()
                minSdk = 26
                targetSdk = 36
                versionCode = (template["versionCode"] as Number).toInt()
                versionName =
                    if (project.name == "manga") "${module["api"]}.${template["versionCode"]}" else template["versionName"].toString()
                manifestPlaceholders["extensionLabel"] = module["name"].toString()
                buildConfigField("String", "BASE_URL", "\"${template["baseUrl"]}\"")
                buildConfigField("String", "SOURCE_NAME", "\"${module["name"]}\"")
                buildConfigField("String", "LANGUAGE", "\"${template["language"]}\"")
                buildConfigField("long", "SOURCE_ID", "${module["sourceId"]}L")
            }
            buildFeatures.buildConfig = true
            compileOptions {
                sourceCompatibility = JavaVersion.VERSION_17
                targetCompatibility = JavaVersion.VERSION_17
            }
            buildTypes.getByName("release").isMinifyEnabled = false
        }
        extensions.configure<org.jetbrains.kotlin.gradle.dsl.KotlinAndroidProjectExtension> { jvmToolchain(17) }
        dependencies {
            add("implementation", project(":common"))
            // Host APIs and their shared libraries must NEVER enter extension DEX.
            add(
                "compileOnly",
                files(
                    rootProject.file("sdk/source-api.jar"),
                    rootProject.file("sdk/core-common.jar"),
                    rootProject.file("sdk/news-api.jar"),
                    rootProject.file("sdk/tv-api.jar"),
                ),
            )
            add("compileOnly", "org.jetbrains.kotlin:kotlin-stdlib:2.4.0")
            add("compileOnly", "org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.2")
            add("compileOnly", "org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
            add("compileOnly", "com.squareup.okhttp3:okhttp:5.4.0")
            add("compileOnly", "org.jsoup:jsoup:1.22.2")
            add("compileOnly", "io.reactivex:rxjava:1.3.8")
            add("compileOnly", "com.github.mihonapp:injekt:91edab2317")
        }
        tasks.matching { it.name.startsWith("compile") && it.name.endsWith("Kotlin") }.configureEach {
            doFirst {
                require(rootProject.file("sdk/sdk-lock.json").isFile) {
                    "SDK missing: run python tools/prepare_sdk.py --host /path/to/nyanime --build"
                }
            }
        }
    }
}
