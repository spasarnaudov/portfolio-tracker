plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

android {
    namespace = "io.github.spasarnaudov.portfoliotracker"
    compileSdk {
        version = release(36)
    }

    defaultConfig {
        applicationId = "io.github.spasarnaudov.portfoliotracker"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    flavorDimensions += "environment"
    productFlavors {
        create("alpha") {
            dimension = "environment"
            versionNameSuffix = "-alpha"
            buildConfigField("String", "API_BASE_URL", "\"http://piglet.tailf5e9c9.ts.net:5000/api/v1/\"")
        }
        create("beta") {
            dimension = "environment"
            versionNameSuffix = "-beta"
            // Reachable only over Tailscale (see network_security_config_release.xml);
            // no public HTTPS backend is planned.
            buildConfigField("String", "API_BASE_URL", "\"http://piglet.tailf5e9c9.ts.net:5000/api/v1/\"")
        }
        create("production") {
            dimension = "environment"
            // Reachable only over Tailscale (see network_security_config_release.xml);
            // no public HTTPS backend is planned.
            buildConfigField("String", "API_BASE_URL", "\"http://piglet.tailf5e9c9.ts.net:5000/api/v1/\"")
        }
    }

    buildTypes {
        debug {
            versionNameSuffix = "-debug"
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    testOptions {
        unitTests {
            isIncludeAndroidResources = true
            isReturnDefaultValues = true
        }
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

androidComponents {
    onVariants(selector().withBuildType("debug")) { variant ->
        val environment = variant.productFlavors
            .first { (dimension, _) -> dimension == "environment" }
            .second
        variant.applicationId.set(
            "io.github.spasarnaudov.portfoliotracker.$environment.debug"
        )
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons.extended)

    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.hilt.navigation.compose)

    implementation(libs.androidx.datastore.preferences)

    implementation(libs.hilt.android)
    ksp(libs.hilt.android.compiler)

    implementation(platform(libs.squareup.okhttp.bom))
    implementation(libs.squareup.okhttp)
    implementation(libs.squareup.okhttp.logging.interceptor)
    implementation(libs.squareup.retrofit)
    implementation(libs.squareup.retrofit.kotlinx.serialization.converter)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.kotlinx.coroutines.android)

    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(platform(libs.squareup.okhttp.bom))
    testImplementation(libs.squareup.okhttp.mockwebserver)
    testImplementation(libs.squareup.retrofit)
    testImplementation(libs.squareup.retrofit.kotlinx.serialization.converter)
    testImplementation(libs.kotlinx.serialization.json)

    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.kotlinx.coroutines.test)
    androidTestImplementation(platform(libs.squareup.okhttp.bom))
    androidTestImplementation(libs.squareup.okhttp.mockwebserver)
    androidTestImplementation(libs.squareup.retrofit)
    androidTestImplementation(libs.squareup.retrofit.kotlinx.serialization.converter)
    androidTestImplementation(libs.kotlinx.serialization.json)

    debugImplementation(libs.androidx.compose.ui.tooling)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
}
