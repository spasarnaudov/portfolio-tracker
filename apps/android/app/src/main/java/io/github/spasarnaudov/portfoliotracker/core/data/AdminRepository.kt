package io.github.spasarnaudov.portfoliotracker.core.data

import io.github.spasarnaudov.portfoliotracker.core.model.AdminUserSummary
import io.github.spasarnaudov.portfoliotracker.core.model.LogContent
import io.github.spasarnaudov.portfoliotracker.core.model.LogFile
import io.github.spasarnaudov.portfoliotracker.core.model.LoginHistoryEntry
import io.github.spasarnaudov.portfoliotracker.core.model.LoginStatEntry
import io.github.spasarnaudov.portfoliotracker.core.network.ApiResult
import io.github.spasarnaudov.portfoliotracker.core.network.ApiService
import io.github.spasarnaudov.portfoliotracker.core.network.apiCall
import io.github.spasarnaudov.portfoliotracker.core.network.dto.AdminUserDto
import io.github.spasarnaudov.portfoliotracker.core.network.serialization.LocalDateTimeSerializer
import io.github.spasarnaudov.portfoliotracker.core.network.toDomain
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonPrimitive
import javax.inject.Inject
import javax.inject.Provider
import javax.inject.Singleton

/**
 * Every method here talks to an ASSUMED admin endpoint (see [io.github.spasarnaudov.portfoliotracker.core.network.ApiService]).
 * Only visible to `user.role == "admin"` — [io.github.spasarnaudov.portfoliotracker.core.auth.SessionManager]
 * gates navigation, and any `403` from the server is surfaced as-is rather than retried
 * or bypassed.
 */
@Singleton
class AdminRepository @Inject constructor(
    private val apiServiceProvider: Provider<ApiService>,
) {
    private val apiService: ApiService get() = apiServiceProvider.get()

    private fun AdminUserDto.toDomain() = AdminUserSummary(
        id = id,
        username = username,
        role = role,
        active = active,
        createdAt = createdAt?.let { runCatching { LocalDateTimeSerializer.parseFlexible(it) }.getOrNull() },
    )

    private fun JsonElement.toDisplayString(): String = when (this) {
        is JsonPrimitive -> content
        else -> toString()
    }

    private fun Map<String, JsonElement>.toEntries(): List<LoginStatEntry> =
        entries.map { LoginStatEntry(it.key, it.value.toDisplayString()) }

    suspend fun getUsers(): ApiResult<List<AdminUserSummary>> {
        val result = apiCall { apiService.getAdminUsers() }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.map { it.toDomain() })
            is ApiResult.Error -> result
        }
    }

    suspend fun getLoginStats(): ApiResult<List<LoginStatEntry>> {
        val result = apiCall { apiService.getAdminLoginStats() }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.toEntries())
            is ApiResult.Error -> result
        }
    }

    suspend fun getLoginHistory(): ApiResult<List<LoginHistoryEntry>> {
        val result = apiCall { apiService.getAdminLoginHistory() }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.map { LoginHistoryEntry(it.toEntries()) })
            is ApiResult.Error -> result
        }
    }

    suspend fun getLogFiles(): ApiResult<List<LogFile>> {
        val result = apiCall { apiService.getAdminLogFiles() }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.map { it.toDomain() })
            is ApiResult.Error -> result
        }
    }

    suspend fun getLogContent(name: String): ApiResult<LogContent> {
        val result = apiCall { apiService.getAdminLogContent(name) }
        return when (result) {
            is ApiResult.Success -> {
                val text = result.data.string()
                ApiResult.Success(LogContent(name = name, lines = text.lines()))
            }

            is ApiResult.Error -> result
        }
    }
}
