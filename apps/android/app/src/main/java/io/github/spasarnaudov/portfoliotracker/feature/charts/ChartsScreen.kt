package io.github.spasarnaudov.portfoliotracker.feature.charts

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import io.github.spasarnaudov.portfoliotracker.core.model.Asset
import io.github.spasarnaudov.portfoliotracker.core.model.AssetPriceInterval
import io.github.spasarnaudov.portfoliotracker.core.model.ChartDefinition
import io.github.spasarnaudov.portfoliotracker.core.model.ChartRange
import io.github.spasarnaudov.portfoliotracker.core.ui.components.EmptyState
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenError
import io.github.spasarnaudov.portfoliotracker.core.ui.components.FullScreenLoading
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LineChart
import io.github.spasarnaudov.portfoliotracker.core.ui.components.LoadStatus

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChartsScreen(viewModel: ChartsViewModel = hiltViewModel()) {
    val state by viewModel.uiState.collectAsState()
    var editingChart by remember { mutableStateOf<ChartDefinition?>(null) }
    var showAddDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = { TopAppBar(title = { Text("Charts") }) },
        floatingActionButton = {
            FloatingActionButton(onClick = { showAddDialog = true }) {
                Icon(Icons.Filled.Add, contentDescription = "Add chart")
            }
        },
    ) { padding ->
        when (state.status) {
            LoadStatus.LOADING -> FullScreenLoading(modifier = Modifier.padding(padding))
            LoadStatus.ERROR -> FullScreenError(
                message = state.errorMessage ?: "Something went wrong.",
                modifier = Modifier.padding(padding),
                onRetry = viewModel::load,
            )

            LoadStatus.EMPTY -> EmptyState(
                message = "No charts configured yet.",
                modifier = Modifier.padding(padding),
                actionLabel = "Add chart",
                onAction = { showAddDialog = true },
            )

            LoadStatus.CONTENT -> LazyColumn(modifier = Modifier.fillMaxSize().padding(padding)) {
                items(state.charts, key = { it.id }) { chart ->
                    Card(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(chart.title, style = MaterialTheme.typography.titleMedium)
                                Row {
                                    IconButton(onClick = { editingChart = chart }) {
                                        Icon(Icons.Filled.Edit, contentDescription = "Edit ${chart.title}")
                                    }
                                    IconButton(onClick = { viewModel.removeChart(chart.id) }) {
                                        Icon(Icons.Filled.Delete, contentDescription = "Remove ${chart.title}")
                                    }
                                }
                            }
                            if (chart.id in state.chartLoading) {
                                CircularProgressIndicator(modifier = Modifier.padding(24.dp))
                            } else {
                                LineChart(
                                    points = state.chartData[chart.id] ?: emptyList(),
                                    scrollable = false,
                                    modifier = Modifier.fillMaxWidth(),
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    if (showAddDialog) {
        ChartEditDialog(
            assets = state.assets,
            initial = null,
            onDismiss = { showAddDialog = false },
            onSave = { viewModel.addChart(it); showAddDialog = false },
        )
    }

    editingChart?.let { chart ->
        ChartEditDialog(
            assets = state.assets,
            initial = chart,
            onDismiss = { editingChart = null },
            onSave = { viewModel.updateChart(it); editingChart = null },
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ChartEditDialog(
    assets: List<Asset>,
    initial: ChartDefinition?,
    onDismiss: () -> Unit,
    onSave: (ChartDefinition) -> Unit,
) {
    var title by remember { mutableStateOf(initial?.title ?: "") }
    var assetId by remember { mutableStateOf(initial?.assetId) }
    var range by remember { mutableStateOf(initial?.range ?: ChartRange.ONE_MONTH) }
    var interval by remember { mutableStateOf(initial?.interval ?: AssetPriceInterval.DAILY) }
    var expanded by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (initial == null) "Add chart" else "Edit chart") },
        text = {
            Column(
                modifier = Modifier.heightIn(max = 420.dp).verticalScroll(rememberScrollState()),
            ) {
                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("Title") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                androidx.compose.foundation.layout.Spacer(modifier = Modifier.padding(top = 8.dp))
                ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
                    OutlinedTextField(
                        value = assets.firstOrNull { it.id == assetId }?.let { "${it.symbol} · ${it.name}" } ?: "Portfolio value",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Data source") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                        modifier = Modifier.fillMaxWidth().menuAnchor(androidx.compose.material3.ExposedDropdownMenuAnchorType.PrimaryEditable, true),
                    )
                    DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                        DropdownMenuItem(text = { Text("Portfolio value") }, onClick = { assetId = null; expanded = false })
                        assets.forEach { asset ->
                            DropdownMenuItem(
                                text = { Text("${asset.symbol} · ${asset.name}") },
                                onClick = { assetId = asset.id; expanded = false },
                            )
                        }
                    }
                }
                androidx.compose.foundation.layout.Spacer(modifier = Modifier.padding(top = 8.dp))
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    ChartRange.entries.filter { it != ChartRange.CUSTOM }.forEach {
                        FilterChip(selected = range == it, onClick = { range = it }, label = { Text(it.label) })
                    }
                }
                androidx.compose.foundation.layout.Spacer(modifier = Modifier.padding(top = 8.dp))
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    AssetPriceInterval.entries.forEach {
                        FilterChip(selected = interval == it, onClick = { interval = it }, label = { Text(it.label) })
                    }
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    onSave(
                        (initial ?: ChartDefinition(title = title, assetId = assetId, range = range, interval = interval)).copy(
                            title = title.ifBlank { "Chart" },
                            assetId = assetId,
                            range = range,
                            interval = interval,
                        ),
                    )
                },
                enabled = title.isNotBlank(),
            ) { Text("Save") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } },
    )
}
