package io.github.spasarnaudov.portfoliotracker.testutil

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import io.github.spasarnaudov.portfoliotracker.core.auth.SessionExpiryNotifier
import io.github.spasarnaudov.portfoliotracker.core.auth.SessionManager
import io.github.spasarnaudov.portfoliotracker.core.auth.TokenStorage
import io.github.spasarnaudov.portfoliotracker.core.network.ApiService
import io.github.spasarnaudov.portfoliotracker.core.network.AuthInterceptor
import io.github.spasarnaudov.portfoliotracker.core.network.UnauthorizedInterceptor
import io.github.spasarnaudov.portfoliotracker.core.network.networkJson
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit

/** Builds a real [ApiService] wired to the production interceptors, pointed at a MockWebServer instance. */
object TestApiServiceFactory {
    fun create(
        baseUrl: String,
        tokenStorage: TokenStorage,
        sessionManager: SessionManager = SessionManager(),
        sessionExpiryNotifier: SessionExpiryNotifier = SessionExpiryNotifier(),
    ): ApiService {
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(tokenStorage))
            .addInterceptor(UnauthorizedInterceptor(tokenStorage, sessionManager, sessionExpiryNotifier))
            .build()
        val retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(networkJson.asConverterFactory("application/json".toMediaType()))
            .build()
        return retrofit.create(ApiService::class.java)
    }
}
