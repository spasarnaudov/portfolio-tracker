package io.github.spasarnaudov.portfoliotracker.core.model

import java.math.BigDecimal
import java.time.LocalDateTime

data class Holding(
    val assetId: Long,
    val assetSymbol: String,
    val assetName: String,
    val quantity: BigDecimal,
    val includeInChart: Boolean,
    val price: BigDecimal?,
    val value: BigDecimal?,
) {
    /** A quantity of zero marks this holding for removal when the portfolio is saved. */
    val isMarkedForRemoval: Boolean get() = quantity.signum() == 0
}

data class ManualItem(
    val id: Long?,
    val name: String,
    val quantity: BigDecimal,
    val unitPrice: BigDecimal?,
    val priceAssetId: Long?,
    val includeInChart: Boolean,
    val value: BigDecimal?,
    val markedForDeletion: Boolean = false,
) {
    val isNew: Boolean get() = id == null
    val usesManualPrice: Boolean get() = priceAssetId == null
}

data class Portfolio(
    val holdings: List<Holding>,
    val manualItems: List<ManualItem>,
    val totalValue: BigDecimal?,
)

data class PortfolioHistoryPoint(
    val timestamp: LocalDateTime,
    val value: BigDecimal,
)

enum class ChartRange(val wireValue: String, val label: String) {
    ONE_DAY("1d", "1D"),
    ONE_WEEK("1w", "1W"),
    ONE_MONTH("1m", "1M"),
    YEAR_TO_DATE("ytd", "YTD"),
    ONE_YEAR("1y", "1Y"),
    ALL("all", "All"),
    CUSTOM("custom", "Custom");
}

/** Intervals supported by `GET /assets/{id}/prices`. */
enum class AssetPriceInterval(val wireValue: String, val label: String) {
    RECORDED("recorded", "Recorded"),
    HOURLY("hourly", "Hourly"),
    DAILY("daily", "Daily"),
    WEEKLY("weekly", "Weekly"),
    MONTHLY("monthly", "Monthly"),
}

/** Intervals supported by `GET /portfolio/history` — a strict subset of the asset ones. */
enum class PortfolioHistoryInterval(val wireValue: String, val label: String) {
    HOURLY("hourly", "Hourly"),
    DAILY("daily", "Daily"),
    WEEKLY("weekly", "Weekly"),
}
