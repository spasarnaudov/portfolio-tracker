package io.github.spasarnaudov.portfoliotracker.core.data

import io.github.spasarnaudov.portfoliotracker.core.model.Holding
import io.github.spasarnaudov.portfoliotracker.core.model.ManualItem
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.math.BigDecimal

class PortfolioValidatorTest {

    private fun holding(quantity: String, symbol: String = "BTC") = Holding(
        assetId = 1,
        assetSymbol = symbol,
        assetName = "Bitcoin",
        quantity = BigDecimal(quantity),
        includeInChart = true,
        price = null,
        value = null,
    )

    private fun manualItem(
        name: String = "Gold ring",
        quantity: String = "1",
        unitPrice: String? = "70",
        markedForDeletion: Boolean = false,
    ) = ManualItem(
        id = null,
        name = name,
        quantity = BigDecimal(quantity),
        unitPrice = unitPrice?.let { BigDecimal(it) },
        priceAssetId = null,
        includeInChart = true,
        value = null,
        markedForDeletion = markedForDeletion,
    )

    @Test
    fun `valid holdings and manual items produce no errors`() {
        val errors = PortfolioValidator.validate(listOf(holding("2.5")), listOf(manualItem()))
        assertTrue(errors.isEmpty())
    }

    @Test
    fun `zero quantity holding is valid (it marks removal, not an error)`() {
        val errors = PortfolioValidator.validate(listOf(holding("0")), emptyList())
        assertTrue(errors.isEmpty())
    }

    @Test
    fun `negative holding quantity is rejected`() {
        val errors = PortfolioValidator.validate(listOf(holding("-1")), emptyList())
        assertEquals(1, errors.size)
        assertTrue(errors.first().contains("BTC"))
    }

    @Test
    fun `negative manual item quantity is rejected`() {
        val errors = PortfolioValidator.validate(emptyList(), listOf(manualItem(quantity = "-5")))
        assertTrue(errors.any { it.contains("Gold ring") })
    }

    @Test
    fun `negative manual item unit price is rejected`() {
        val errors = PortfolioValidator.validate(emptyList(), listOf(manualItem(unitPrice = "-10")))
        assertTrue(errors.isNotEmpty())
    }

    @Test
    fun `blank manual item name is rejected`() {
        val errors = PortfolioValidator.validate(emptyList(), listOf(manualItem(name = "  ")))
        assertTrue(errors.any { it.contains("name") })
    }

    @Test
    fun `manual items marked for deletion are not validated`() {
        val errors = PortfolioValidator.validate(
            emptyList(),
            listOf(manualItem(name = "", quantity = "-1", unitPrice = "-1", markedForDeletion = true)),
        )
        assertTrue(errors.isEmpty())
    }

    @Test
    fun `null manual unit price (manual pricing left blank) is not an error`() {
        val errors = PortfolioValidator.validate(emptyList(), listOf(manualItem(unitPrice = null)))
        assertTrue(errors.isEmpty())
    }
}
