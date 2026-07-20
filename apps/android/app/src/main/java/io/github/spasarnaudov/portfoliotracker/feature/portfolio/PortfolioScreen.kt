package io.github.spasarnaudov.portfoliotracker.feature.portfolio

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.github.spasarnaudov.portfoliotracker.core.model.ChartRange
import io.github.spasarnaudov.portfoliotracker.core.model.PortfolioHistoryInterval
import io.github.spasarnaudov.portfoliotracker.core.model.PortfolioHistoryPoint
import io.github.spasarnaudov.portfoliotracker.core.ui.components.ChartPoint
import io.github.spasarnaudov.portfoliotracker.core.ui.components.ConfirmDialog
import io.github.spasarnaudov.portfoliotracker.core.ui.components.EmptyState
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenError
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenLoading
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LineChart
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LoadStatus
import io.github.spasarnaudov.portfoliotracker.core.ui.format.formatMoneyOrDash
import java.math.BigDecimal

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PortfolioScreen(
    onAddManualItem: () -> Unit,
    onEditManualItem: (String) -> Unit,
    viewModel: PortfolioViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    var showDiscardConfirm by remember { mutableStateOf(false) }
    var isRefreshing by remember { mutableStateOf(false) }
    var showEmptyHoldings by remember { mutableStateOf(true) }

    LaunchedEffect(state.saveError) {
        state.saveError?.let { snackbarHostState.showSnackbar(it) }
    }
    LaunchedEffect(state.status) {
        if (state.status != LoadStatus.LOADING) isRefreshing = false
    }

    BackHandler(enabled = state.hasUnsavedChanges) { showDiscardConfirm = true }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(title = { Text("Portfolio") })
        },
        floatingActionButton = {
            FloatingActionButton(onClick = onAddManualItem) {
                Icon(Icons.Filled.Add, contentDescription = "Add manual item")
            }
        },
    ) { padding ->
        // Chart + filters render unconditionally above the holdings list — mirrors the web
        // portfolio page, where the chart panel is always visible regardless of table state.
        Column(modifier = Modifier.fillMaxSize().padding(padding)) {
            PortfolioChartSection(
                range = state.historyRange,
                interval = state.historyInterval,
                status = state.historyStatus,
                points = state.historyPoints,
                errorMessage = state.historyErrorMessage,
                showEmptyHoldings = showEmptyHoldings,
                onRangeSelected = viewModel::setHistoryRange,
                onIntervalSelected = viewModel::setHistoryInterval,
                onShowEmptyHoldingsChange = { showEmptyHoldings = it },
                onRetry = viewModel::retryHistory,
                modifier = Modifier.padding(horizontal = 16.dp),
            )
            HorizontalDivider(modifier = Modifier.padding(top = 12.dp))

            Box(modifier = Modifier.weight(1f)) {
                when (state.status) {
                    LoadStatus.LOADING -> FullScreenLoading()
                    LoadStatus.ERROR -> FullScreenError(
                        message = state.errorMessage ?: "Something went wrong.",
                        onRetry = viewModel::load,
                    )

                    LoadStatus.EMPTY -> EmptyState(
                        message = "Your portfolio is empty. Add a manual item or link an asset to get started.",
                        actionLabel = "Add manual item",
                        onAction = onAddManualItem,
                    )

                    LoadStatus.CONTENT -> PullToRefreshBox(
                        isRefreshing = isRefreshing,
                        onRefresh = { isRefreshing = true; viewModel.load() },
                    ) {
                        LazyColumn(modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp)) {
                            item {
                                Text(
                                    text = "Total value: ${state.totalValue.formatMoneyOrDash()}",
                                    style = MaterialTheme.typography.titleLarge,
                                    modifier = Modifier.padding(vertical = 12.dp),
                                )
                            }
                            val visibleHoldings = if (showEmptyHoldings) {
                                state.holdings
                            } else {
                                state.holdings.filter { it.originalQuantity > BigDecimal.ZERO }
                            }
                            if (visibleHoldings.isNotEmpty()) {
                                item { Text("Holdings", style = MaterialTheme.typography.titleMedium) }
                                items(visibleHoldings, key = { it.assetId }) { holding ->
                                    HoldingRow(
                                        holding = holding,
                                        onQuantityChange = { viewModel.updateHoldingQuantityText(holding.assetId, it) },
                                        onToggleChart = { viewModel.toggleHoldingIncludeInChart(holding.assetId) },
                                        onRemove = { viewModel.removeHolding(holding.assetId) },
                                    )
                                    HorizontalDivider()
                                }
                            }
                            if (state.manualItems.any { !it.markedForDeletion }) {
                                item {
                                    Text(
                                        "Manual items",
                                        style = MaterialTheme.typography.titleMedium,
                                        modifier = Modifier.padding(top = 16.dp),
                                    )
                                }
                                items(
                                    state.manualItems.filterNot { it.markedForDeletion },
                                    key = { it.clientKey },
                                ) { item ->
                                    ManualItemRow(
                                        item = item,
                                        onEdit = { onEditManualItem(item.clientKey) },
                                        onDelete = { viewModel.markManualItemForDeletion(item.clientKey) },
                                    )
                                    HorizontalDivider()
                                }
                            }
                            item { Spacer(modifier = Modifier.padding(bottom = 80.dp)) }
                        }
                    }
                }
            }
        }
    }

    if (showDiscardConfirm) {
        ConfirmDialog(
            title = "Discard changes?",
            text = "You have unsaved changes to your portfolio. Are you sure you want to leave?",
            confirmLabel = "Discard",
            destructive = true,
            onConfirm = { showDiscardConfirm = false; viewModel.discardChanges() },
            onDismiss = { showDiscardConfirm = false },
        )
    }
}

@Composable
private fun PortfolioChartSection(
    range: ChartRange,
    interval: PortfolioHistoryInterval,
    status: LoadStatus,
    points: List<PortfolioHistoryPoint>,
    errorMessage: String?,
    showEmptyHoldings: Boolean,
    onRangeSelected: (ChartRange) -> Unit,
    onIntervalSelected: (PortfolioHistoryInterval) -> Unit,
    onShowEmptyHoldingsChange: (Boolean) -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier.fillMaxWidth().padding(top = 8.dp)) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(4.dp),
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
        ) {
            FilterDropdown(
                selectedLabel = range.label,
                options = PortfolioHistoryRanges,
                optionLabel = { it.label },
                onSelected = onRangeSelected,
            )
            FilterDropdown(
                selectedLabel = interval.label,
                options = PortfolioHistoryInterval.entries,
                optionLabel = { it.label },
                onSelected = onIntervalSelected,
            )
            Checkbox(checked = showEmptyHoldings, onCheckedChange = onShowEmptyHoldingsChange)
            Text("Show empty", style = MaterialTheme.typography.bodyMedium)
        }

        when (status) {
            LoadStatus.LOADING -> Box(
                modifier = Modifier.fillMaxWidth().height(220.dp).padding(top = 16.dp),
                contentAlignment = androidx.compose.ui.Alignment.Center,
            ) {
                CircularProgressIndicator()
            }

            LoadStatus.ERROR -> Box(
                modifier = Modifier.fillMaxWidth().height(220.dp).padding(top = 16.dp),
                contentAlignment = androidx.compose.ui.Alignment.Center,
            ) {
                Column(
                    horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(errorMessage ?: "Something went wrong.", style = MaterialTheme.typography.bodyMedium)
                    TextButton(onClick = onRetry) { Text("Retry") }
                }
            }

            LoadStatus.EMPTY -> Box(
                modifier = Modifier.fillMaxWidth().height(220.dp).padding(top = 16.dp),
                contentAlignment = androidx.compose.ui.Alignment.Center,
            ) {
                Text("Select portfolio items to see their history.", style = MaterialTheme.typography.bodyMedium)
            }

            LoadStatus.CONTENT -> LineChart(
                points = points.map { ChartPoint(it.timestamp, it.value) },
                showTimeInLabels = interval == PortfolioHistoryInterval.HOURLY,
                scrollable = false,
                modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
            )
        }
    }
}

@Composable
private fun <T> FilterDropdown(
    selectedLabel: String,
    options: List<T>,
    optionLabel: (T) -> String,
    onSelected: (T) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    Box {
        OutlinedButton(onClick = { expanded = true }) {
            Text(selectedLabel)
            Icon(Icons.Filled.ArrowDropDown, contentDescription = null)
        }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            options.forEach { option ->
                DropdownMenuItem(
                    text = { Text(optionLabel(option)) },
                    onClick = { onSelected(option); expanded = false },
                )
            }
        }
    }
}

@Composable
private fun HoldingRow(
    holding: HoldingRowState,
    onQuantityChange: (String) -> Unit,
    onToggleChart: () -> Unit,
    onRemove: () -> Unit,
) {
    val isRemoved = holding.quantityText.trim() == "0"
    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = "${holding.assetSymbol} · ${holding.assetName}",
                style = MaterialTheme.typography.bodyLarge,
                textDecoration = if (isRemoved) TextDecoration.LineThrough else TextDecoration.None,
            )
            Text(
                text = "Value: ${holding.value.formatMoneyOrDash()}",
                style = MaterialTheme.typography.bodySmall,
            )
        }
        OutlinedTextField(
            value = holding.quantityText,
            onValueChange = onQuantityChange,
            label = { Text("Qty") },
            singleLine = true,
            modifier = Modifier.width(110.dp),
        )
        Column(horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally) {
            Checkbox(checked = holding.includeInChart, onCheckedChange = { onToggleChart() })
            Text("Chart", style = MaterialTheme.typography.labelSmall)
        }
        IconButton(onClick = onRemove) {
            Icon(Icons.Filled.Delete, contentDescription = "Remove ${holding.assetSymbol}")
        }
    }
}

@Composable
private fun ManualItemRow(
    item: ManualItemDraft,
    onEdit: () -> Unit,
    onDelete: () -> Unit,
) {
    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
        Column(modifier = Modifier.weight(1f)) {
            Text(text = item.name, style = MaterialTheme.typography.bodyLarge)
            Text(
                text = "Qty ${item.quantityText} · Value: ${item.value.formatMoneyOrDash()}",
                style = MaterialTheme.typography.bodySmall,
            )
        }
        IconButton(onClick = onEdit) { Icon(Icons.Filled.Edit, contentDescription = "Edit ${item.name}") }
        IconButton(onClick = onDelete) { Icon(Icons.Filled.Delete, contentDescription = "Delete ${item.name}") }
    }
}
