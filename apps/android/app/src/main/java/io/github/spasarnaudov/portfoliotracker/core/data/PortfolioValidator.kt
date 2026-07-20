package io.github.spasarnaudov.portfoliotracker.core.data

import io.github.spasarnaudov.portfoliotracker.core.model.Holding
import io.github.spasarnaudov.portfoliotracker.core.model.ManualItem

/** Pure, unit-testable validation applied before a `PUT /portfolio` request is built. */
object PortfolioValidator {
    fun validate(holdings: List<Holding>, manualItems: List<ManualItem>): List<String> {
        val errors = mutableListOf<String>()

        for (holding in holdings) {
            if (holding.quantity.signum() < 0) {
                errors += "Quantity for ${holding.assetSymbol.ifBlank { "asset #${holding.assetId}" }} cannot be negative."
            }
        }

        for (item in manualItems) {
            if (item.markedForDeletion) continue
            if (item.name.isBlank()) {
                errors += "Manual item name cannot be empty."
            }
            if (item.quantity.signum() < 0) {
                errors += "Quantity for \"${item.name}\" cannot be negative."
            }
            val unitPrice = item.unitPrice
            if (unitPrice != null && unitPrice.signum() < 0) {
                errors += "Unit price for \"${item.name}\" cannot be negative."
            }
        }

        return errors
    }
}
