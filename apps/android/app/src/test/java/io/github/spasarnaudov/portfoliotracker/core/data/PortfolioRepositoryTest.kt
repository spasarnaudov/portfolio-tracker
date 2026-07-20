package io.github.spasarnaudov.portfoliotracker.core.data

import io.github.spasarnaudov.portfoliotracker.core.model.ChartRange
import io.github.spasarnaudov.portfoliotracker.core.model.Holding
import io.github.spasarnaudov.portfoliotracker.core.model.ManualItem
import io.github.spasarnaudov.portfoliotracker.core.model.PortfolioHistoryInterval
import io.github.spasarnaudov.portfoliotracker.core.network.ApiResult
import io.github.spasarnaudov.portfoliotracker.testutil.FakeTokenStorage
import io.github.spasarnaudov.portfoliotracker.testutil.TestApiServiceFactory
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.math.BigDecimal
import javax.inject.Provider

class PortfolioRepositoryTest {

    private lateinit var server: MockWebServer
    private lateinit var repository: PortfolioRepository

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
        val apiService = TestApiServiceFactory.create(server.url("/").toString(), FakeTokenStorage())
        repository = PortfolioRepository(Provider { apiService })
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun `update portfolio maps holdings and a new manual item with id null`() = runTest {
        server.enqueue(MockResponse().setResponseCode(200).setBody("""{"holdings":[],"manual_items":[]}"""))

        val holdings = listOf(
            Holding(assetId = 12, assetSymbol = "BTC", assetName = "Bitcoin", quantity = BigDecimal("2.5"), includeInChart = true, price = null, value = null),
        )
        val manualItems = listOf(
            ManualItem(id = null, name = "Gold ring", quantity = BigDecimal("8.2"), unitPrice = BigDecimal("70"), priceAssetId = null, includeInChart = true, value = null),
        )

        repository.updatePortfolio(holdings, manualItems)

        // Field names on the wire are snake_case, matching API.md's PUT /portfolio example exactly.
        val body = server.takeRequest().body.readUtf8()
        assertTrue(body.contains("\"asset_id\":12"))
        assertTrue(body.contains("\"quantity\":2.5"))
        assertTrue(body.contains("\"include_in_chart\":true"))
        assertTrue(body.contains("\"id\":null"))
        assertTrue(body.contains("\"name\":\"Gold ring\""))
        assertTrue(body.contains("\"unit_price\":70"))
    }

    @Test
    fun `update portfolio marks an existing manual item for deletion`() = runTest {
        server.enqueue(MockResponse().setResponseCode(200).setBody("""{"holdings":[],"manual_items":[]}"""))

        val manualItems = listOf(
            ManualItem(id = 7, name = "Old item", quantity = BigDecimal.ONE, unitPrice = null, priceAssetId = null, includeInChart = true, value = null, markedForDeletion = true),
        )

        repository.updatePortfolio(emptyList(), manualItems)

        val body = server.takeRequest().body.readUtf8()
        assertTrue(body.contains("\"id\":7"))
        assertTrue(body.contains("\"delete\":true"))
    }

    @Test
    fun `update portfolio with a negative quantity is rejected locally without an HTTP call`() = runTest {
        val holdings = listOf(
            Holding(assetId = 1, assetSymbol = "BTC", assetName = "Bitcoin", quantity = BigDecimal("-1"), includeInChart = true, price = null, value = null),
        )

        val result = repository.updatePortfolio(holdings, emptyList())

        assertTrue(result is ApiResult.Error)
        assertEquals(0, server.requestCount)
    }

    @Test
    fun `get portfolio history sends the requested range and interval as query params`() = runTest {
        server.enqueue(MockResponse().setResponseCode(200).setBody("[]"))

        repository.getPortfolioHistory(ChartRange.ONE_WEEK, PortfolioHistoryInterval.HOURLY)

        val recorded = server.takeRequest()
        assertTrue(recorded.path!!.contains("range=1w"))
        assertTrue(recorded.path!!.contains("interval=hourly"))
    }
}
