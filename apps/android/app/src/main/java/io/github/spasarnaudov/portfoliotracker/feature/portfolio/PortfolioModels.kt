package io.github.spasarnaudov.portfoliotracker.feature.portfolio

import io.github.spasarnaudov.portfoliotracker.core.model.Holding
import java.math.BigDecimal
import java.util.UUID

/** Editable row for a holding: [quantityText] is the free-typed value; [quantity] is parsed lazily on save. */
data class HoldingRowState(
    val assetId: Long,
    val assetSymbol: String,
    val assetName: String,
    val quantityText: String,
    val includeInChart: Boolean,
    val price: BigDecimal?,
    val value: BigDecimal?,
    val originalQuantity: BigDecimal,
    val originalIncludeInChart: Boolean,
) {
    val isDirty: Boolean
        get() = quantityText != originalQuantity.toPlainString() || includeInChart != originalIncludeInChart

    val parsedQuantity: BigDecimal?
        get() = quantityText.trim().toBigDecimalOrNull()

    companion object {
        fun from(holding: Holding) = HoldingRowState(
            assetId = holding.assetId,
            assetSymbol = holding.assetSymbol,
            assetName = holding.assetName,
            quantityText = holding.quantity.toPlainString(),
            includeInChart = holding.includeInChart,
            price = holding.price,
            value = holding.value,
            originalQuantity = holding.quantity,
            originalIncludeInChart = holding.includeInChart,
        )
    }
}

/**
 * A manual item being edited locally. [clientKey] lets several new (server `id == null`)
 * items coexist in the pending list before save.
 */
data class ManualItemDraft(
    val clientKey: String = UUID.randomUUID().toString(),
    val id: Long?,
    val name: String,
    val quantityText: String,
    val unitPriceText: String,
    val priceAssetId: Long?,
    val includeInChart: Boolean,
    val value: BigDecimal?,
    val markedForDeletion: Boolean = false,
) {
    val usesManualPrice: Boolean get() = priceAssetId == null

    companion object {
        fun from(item: io.github.spasarnaudov.portfoliotracker.core.model.ManualItem) = ManualItemDraft(
            id = item.id,
            name = item.name,
            quantityText = item.quantity.toPlainString(),
            unitPriceText = item.unitPrice?.toPlainString() ?: "",
            priceAssetId = item.priceAssetId,
            includeInChart = item.includeInChart,
            value = item.value,
        )

        fun blank() = ManualItemDraft(
            id = null,
            name = "",
            quantityText = "",
            unitPriceText = "",
            priceAssetId = null,
            includeInChart = true,
            value = null,
        )
    }
}

private fun String.toBigDecimalOrNull(): BigDecimal? = try {
    if (isBlank()) null else BigDecimal(this)
} catch (e: NumberFormatException) {
    null
}
