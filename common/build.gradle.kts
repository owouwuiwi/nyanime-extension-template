plugins { kotlin("jvm") }
kotlin { jvmToolchain(17) }
dependencies {
    compileOnly("org.jetbrains.kotlin:kotlin-stdlib:2.4.0")
    compileOnly("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.2")
    compileOnly("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
    compileOnly("org.jsoup:jsoup:1.22.2")
    compileOnly("com.squareup.okhttp3:okhttp:5.4.0")
    testImplementation("org.jetbrains.kotlin:kotlin-stdlib:2.4.0")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
    testImplementation("org.jsoup:jsoup:1.22.2")
    testImplementation("com.squareup.okhttp3:okhttp:5.4.0")
    testImplementation("junit:junit:4.13.2")
}
tasks.test { systemProperty("fixtureRoot", rootProject.file("website").absolutePath) }
