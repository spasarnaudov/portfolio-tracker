package io.github.spasarnaudov.portfoliotracker.core.data

import io.github.spasarnaudov.portfoliotracker.core.model.AppError
import io.github.spasarnaudov.portfoliotracker.core.model.ChartRange
import io.github.spasarnaudov.portfoliotracker.core.model.Holding
import io.github.spasarnaudov.portfoliotracker.core.model.ManualItem
import io.github.spasarnaudov.portfoliotracker.core.model.Portfolio
import io.github.spasarnaudov.portfoliotracker.core.model.PortfolioHistoryInterval
import io.github.spasarnaudov.portfoliotracker.core.model.PortfolioHistoryPoint
import io.github.spasarnaudov.portfoliotracker.core.network.ApiResult
import io.github.spasarnaudov.portfoliotracker.core.network.ApiService
import io.github.spasarnaudov.portfoliotracker.core.network.apiCall
import io.github.spasarnaudov.portfoliotracker.core.network.dto.HoldingUpdateDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.ManualItemUpdateDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.PortfolioUpdateRequestDto
import io.github.spasarnaudov.portfoliotracker.core.network.toDomain
import javax.inject.Inject
import javax.inject.Provider
import javax.inject.Singleton

@Singleton
class PortfolioRepository @Inject constructor(
    private val apiServiceProvider: Provider<ApiService>,
) {
    private val apiService: ApiService get() = apiServiceProvider.get()

    suspend fun getPortfolio(): ApiResult<Portfolio> {
        val result = apiCall { apiService.getPortfolio() }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.toDomain())
            is ApiResult.Error -> result
        }
    }

    /** Validates locally first (never sends negative quantities/prices), then calls `PUT /portfolio`. */
    suspend fun updatePortfolio(holdings: List<Holding>, manualItems: List<ManualItem>): ApiResult<Portfolio> {
        val errors = PortfolioValidator.validate(holdings, manualItems)
        if (errors.isNotEmpty()) {
            return ApiResult.Error(AppError.ValidationFailed(errors.first(), errors))
        }

        val holdingsDto = holdings.map { HoldingUpdateDto(it.assetId, it.quantity, it.includeInChart) }
        val manualItemsDto = manualItems.map {
            ManualItemUpdateDto(
                id = it.id,
                name = it.name,
                quantity = it.quantity,
                unitPrice = it.unitPrice,
                priceAssetId = it.priceAssetId,
                includeInChart = it.includeInChart,
                delete = it.markedForDeletion,
            )
        }

        val result = apiCall {
            apiService.updatePortfolio(PortfolioUpdateRequestDto(holdingsDto, manualItemsDto))
        }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.toDomain())
            is ApiResult.Error -> result
        }
    }

    suspend fun getPortfolioHistory(
        range: ChartRange,
        interval: PortfolioHistoryInterval,
    ): ApiResult<List<PortfolioHistoryPoint>> {
        val result = apiCall { apiService.getPortfolioHistory(range.wireValue, interval.wireValue) }
        return when (result) {
            is ApiResult.Success -> ApiResult.Success(result.data.points.mapNotNull { it.toDomain() })
            is ApiResult.Error -> result
        }
    }
}
