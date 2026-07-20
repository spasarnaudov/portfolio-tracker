package io.github.spasarnaudov.portfoliotracker.core.data

import io.github.spasarnaudov.portfoliotracker.core.model.ChartConfiguration
import io.github.spasarnaudov.portfoliotracker.core.network.ApiResult
import io.github.spasarnaudov.portfoliotracker.core.network.ApiService
import io.github.spasarnaudov.portfoliotracker.core.network.apiCall
import io.github.spasarnaudov.portfoliotracker.core.network.toDomain
import io.github.spasarnaudov.portfoliotracker.core.network.toDto
import javax.inject.Inject
import javax.inject.Provider
import javax.inject.Singleton

@Singleton
class ChartsRepository @Inject constructor(
    private val apiServiceProvider: Provider<ApiService>,
) {
    private val apiService: ApiService get() = apiServiceProvider.get()

    suspend fun getConfiguration(): ApiResult<ChartConfiguration> {
        val result = apiCall { apiService.getChartConfiguration() }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.toDomain())
            is ApiResult.Error -> result
        }
    }

    suspend fun updateConfiguration(configuration: ChartConfiguration): ApiResult<ChartConfiguration> {
        val result = apiCall { apiService.updateChartConfiguration(configuration.toDto()) }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.toDomain())
            is ApiResult.Error -> result
        }
    }
}
