package io.github.spasarnaudov.portfoliotracker.core.network

import io.github.spasarnaudov.portfoliotracker.core.model.Asset
import io.github.spasarnaudov.portfoliotracker.core.model.AssetPriceInterval
import io.github.spasarnaudov.portfoliotracker.core.model.ChartConfiguration
import io.github.spasarnaudov.portfoliotracker.core.model.ChartDefinition
import io.github.spasarnaudov.portfoliotracker.core.model.ChartRange
import io.github.spasarnaudov.portfoliotracker.core.model.Holding
import io.github.spasarnaudov.portfoliotracker.core.model.LogFile
import io.github.spasarnaudov.portfoliotracker.core.model.ManualItem
import io.github.spasarnaudov.portfoliotracker.core.model.Portfolio
import io.github.spasarnaudov.portfoliotracker.core.model.PortfolioHistoryPoint
import io.github.spasarnaudov.portfoliotracker.core.model.PricePoint
import io.github.spasarnaudov.portfoliotracker.core.model.User
import io.github.spasarnaudov.portfoliotracker.core.network.dto.AssetDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.ChartConfigurationDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.ChartDefinitionDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.HoldingResponseDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.LogFileDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.ManualItemResponseDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.PortfolioHistoryPointDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.PortfolioResponseDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.PricePointDto
import io.github.spasarnaudov.portfoliotracker.core.network.dto.UserDto
import io.github.spasarnaudov.portfoliotracker.core.network.serialization.LocalDateTimeSerializer
import java.time.LocalDate
import java.time.LocalDateTime

fun UserDto.toDomain() = User(id = id, username = username, role = role)

private fun parseTimestampOrNull(raw: String?): LocalDateTime? =
    raw?.let { runCatching { LocalDateTimeSerializer.parseFlexible(it) }.getOrNull() }
        ?: raw?.let { runCatching { LocalDate.parse(it).atStartOfDay() }.getOrNull() }

fun HoldingResponseDto.toDomain() = Holding(
    assetId = assetId,
    assetSymbol = assetSymbol ?: "",
    assetName = assetName ?: assetSymbol ?: "Asset #$assetId",
    quantity = quantity,
    includeInChart = includeInChart,
    price = price,
    value = value,
)

fun ManualItemResponseDto.toDomain() = ManualItem(
    id = id,
    name = name,
    quantity = quantity,
    unitPrice = unitPrice,
    priceAssetId = priceAssetId,
    includeInChart = includeInChart,
    value = value,
)

fun PortfolioResponseDto.toDomain() = Portfolio(
    holdings = holdings.map { it.toDomain() },
    manualItems = manualItems.map { it.toDomain() },
    totalValue = totalValue,
)

fun PortfolioHistoryPointDto.toDomain(): PortfolioHistoryPoint? {
    val ts = parseTimestampOrNull(timestamp) ?: return null
    return PortfolioHistoryPoint(timestamp = ts, value = value)
}

fun AssetDto.toDomain(isGoldBuyback: Boolean) = Asset(
    id = id,
    symbol = symbol,
    name = name,
    currentPrice = currentPrice,
    currency = currency,
    isGoldBuyback = isGoldBuyback,
)

fun PricePointDto.toDomain(): PricePoint? {
    val ts = parseTimestampOrNull(timestamp) ?: return null
    return PricePoint(timestamp = ts, price = price)
}

fun ChartDefinitionDto.toDomain(): ChartDefinition? {
    val range = ChartRange.entries.firstOrNull { it.wireValue == range } ?: return null
    val interval = AssetPriceInterval.entries.firstOrNull { it.wireValue == interval } ?: AssetPriceInterval.DAILY
    return ChartDefinition(
        id = id ?: java.util.UUID.randomUUID().toString(),
        title = title ?: "Chart",
        assetId = assetId,
        range = range,
        interval = interval,
        startDate = startDate?.let { runCatching { LocalDate.parse(it) }.getOrNull() },
        endDate = endDate?.let { runCatching { LocalDate.parse(it) }.getOrNull() },
    )
}

fun ChartConfigurationDto.toDomain() = ChartConfiguration(charts = charts.mapNotNull { it.toDomain() })

fun ChartDefinition.toDto() = ChartDefinitionDto(
    id = id,
    title = title,
    assetId = assetId,
    range = range.wireValue,
    interval = interval.wireValue,
    startDate = startDate?.toString(),
    endDate = endDate?.toString(),
)

fun ChartConfiguration.toDto() = ChartConfigurationDto(charts = charts.map { it.toDto() })

fun LogFileDto.toDomain() = LogFile(
    name = name,
    sizeBytes = sizeBytes,
    modifiedAt = parseTimestampOrNull(modifiedAt),
)
