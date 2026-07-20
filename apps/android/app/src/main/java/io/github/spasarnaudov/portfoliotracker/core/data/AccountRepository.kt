package io.github.spasarnaudov.portfoliotracker.core.data

import io.github.spasarnaudov.portfoliotracker.core.auth.SessionManager
import io.github.spasarnaudov.portfoliotracker.core.auth.TokenStorage
import io.github.spasarnaudov.portfoliotracker.core.model.User
import io.github.spasarnaudov.portfoliotracker.core.network.ApiResult
import io.github.spasarnaudov.portfoliotracker.core.network.ApiService
import io.github.spasarnaudov.portfoliotracker.core.network.apiCall
import io.github.spasarnaudov.portfoliotracker.core.network.dto.ChangePasswordRequestDto
import io.github.spasarnaudov.portfoliotracker.core.network.toDomain
import javax.inject.Inject
import javax.inject.Provider
import javax.inject.Singleton

@Singleton
class AccountRepository @Inject constructor(
    private val apiServiceProvider: Provider<ApiService>,
    private val tokenStorage: TokenStorage,
    private val sessionManager: SessionManager,
) {
    private val apiService: ApiService get() = apiServiceProvider.get()

    suspend fun getCurrentUser(): ApiResult<User> {
        val result = apiCall { apiService.getCurrentUser() }
        if (result is ApiResult.Success) {
            sessionManager.setUser(result.data.user.toDomain())
        }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.user.toDomain())
            is ApiResult.Error -> result
        }
    }

    suspend fun changePassword(currentPassword: String, newPassword: String): ApiResult<Unit> {
        val result = apiCall {
            apiService.changePassword(ChangePasswordRequestDto(currentPassword, newPassword))
        }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(Unit)
            is ApiResult.Error -> result
        }
    }

    /** Deactivates the account then clears local session state regardless of the outcome's UI handling. */
    suspend fun deactivateAccount(): ApiResult<Unit> {
        val result = apiCall { apiService.deactivateAccount() }
        if (result is ApiResult.Success) {
            tokenStorage.clear()
            sessionManager.setUser(null)
        }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(Unit)
            is ApiResult.Error -> result
        }
    }
}
