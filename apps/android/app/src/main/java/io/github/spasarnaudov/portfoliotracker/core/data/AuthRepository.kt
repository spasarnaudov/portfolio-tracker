package io.github.spasarnaudov.portfoliotracker.core.data

import io.github.spasarnaudov.portfoliotracker.core.auth.SessionManager
import io.github.spasarnaudov.portfoliotracker.core.auth.TokenStorage
import io.github.spasarnaudov.portfoliotracker.core.model.AppError
import io.github.spasarnaudov.portfoliotracker.core.model.User
import io.github.spasarnaudov.portfoliotracker.core.network.ApiResult
import io.github.spasarnaudov.portfoliotracker.core.network.ApiService
import io.github.spasarnaudov.portfoliotracker.core.network.apiCall
import io.github.spasarnaudov.portfoliotracker.core.network.dto.LoginRequestDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.RegisterRequestDto
import io.github.spasarnaudov.portfoliotracker.core.network.toDomain
import javax.inject.Inject
import javax.inject.Provider
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val apiServiceProvider: Provider<ApiService>,
    private val tokenStorage: TokenStorage,
    private val sessionManager: SessionManager,
) {
    private val apiService: ApiService get() = apiServiceProvider.get()

    suspend fun login(username: String, password: String, force: Boolean = false): ApiResult<User> {
        val result = apiCall { apiService.login(LoginRequestDto(username, password, if (force) true else null)) }
        return when (result) {
            is ApiResult.Success -> {
                tokenStorage.saveToken(result.data.token, result.data.expiresAt)
                val user = result.data.user.toDomain()
                sessionManager.setUser(user)
                ApiResult.Success(user)
            }

            is ApiResult.Error -> result
        }
    }

    suspend fun register(username: String, password: String): ApiResult<User> {
        val result = apiCall { apiService.register(RegisterRequestDto(username, password)) }
        return when (result) {
            is ApiResult.Success -> {
                tokenStorage.saveToken(result.data.token, result.data.expiresAt)
                val user = result.data.user.toDomain()
                sessionManager.setUser(user)
                ApiResult.Success(user)
            }

            is ApiResult.Error -> result
        }
    }

    /** Always clears local state, even if the server call fails. */
    suspend fun logout() {
        apiCall { apiService.logout() }
        tokenStorage.clear()
        sessionManager.setUser(null)
    }

    /** Startup session check: `401` means an invalid/expired token, other errors are surfaced as-is. */
    suspend fun restoreSession(): ApiResult<User> {
        if (tokenStorage.getToken() == null) {
            return ApiResult.Error(AppError.Unauthorized(null))
        }
        val result = apiCall { apiService.getCurrentUser() }
        return when (result) {
            is ApiResult.Success -> {
                val user = result.data.user.toDomain()
                sessionManager.setUser(user)
                ApiResult.Success(user)
            }

            is ApiResult.Error -> {
                if (result.error is AppError.Unauthorized) {
                    tokenStorage.clear()
                    sessionManager.setUser(null)
                }
                result
            }
        }
    }
}
